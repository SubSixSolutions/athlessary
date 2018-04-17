import csv
import usaddress
from geopy import Nominatim

from User.user import User
from Utils.log import log


def csv_to_db(path_to_csv_file):
    with open(path_to_csv_file) as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            csv_row_data = {}

            # keys to lowercase, remove spaces
            row = dict((k.lower().replace(' ', '_'), v) for k, v in row.items())
            keys = row.keys()

            if not row['first_name'] or not row['last_name']:
                continue

            first = row['first_name']
            last = row['last_name']
            csv_row_data['first'] = first
            csv_row_data['last'] = last
            csv_row_data['username'] = str.lower(first[0] + last)

            bonus_keys = ['address', 'num_seats', 'phone']
            for key in bonus_keys:
                if key in keys:

                    if key == 'phone':
                        csv_row_data[key] = validate_phone_number(row[key])
                    else:
                        csv_row_data[key] = row[key]

                    if key == 'address':
                        address_dict = validate_address(row[key])
                        if address_dict is not None:
                            coord_dict = get_coordinates_from_address(address_dict)
                            if coord_dict is not None:
                                address_dict = {**address_dict, **coord_dict}
                            # merge the address_dict into csv_row_data
                            csv_row_data = {**csv_row_data, **address_dict}

                    if key == 'num_seats':
                        if len(row[key]) > 0:
                            csv_row_data[key] = int(row[key])
                        else:
                            csv_row_data[key] = 0
                else:
                    csv_row_data[key] = None

            if 'm/w' in keys and 'v/n' in keys:
                csv_row_data['team'] = row['m/w'] + row['v/n']
            else:
                csv_row_data['team'] = None

            log.debug('creating new user with data: {}'.format(csv_row_data))

            User.user_from_csv_row(csv_row_data)


def validate_phone_number(phone_number_str):
    if type(phone_number_str) is not str:
        return None

    phone_number_str = phone_number_str.replace('-', '')
    if len(phone_number_str) is not 10:
        return None
    else:
        return int(phone_number_str)


def validate_address(address_str):
    parsed_address = usaddress.tag(address_str)
    address_dict = None
    tagged_address = dict(parsed_address[0])
    log.debug('tagged_address: {}'.format(tagged_address))
    if not parsed_address[1] == 'Street Address':
        log.warn('{} is not a valid address'.format(address_str))
    else:

        address_number_seq = (
            tagged_address.get('AddressNumberPrefix', ''),
            tagged_address.get('AddressNumber', ''),
            tagged_address.get('AddressNumberSuffix', '')
        )

        address_number = ' '.join(address_number_seq)
        # Remove extra internal whitespace
        address_number = ' '.join(address_number.strip().split())

        street_name_seq = (
            tagged_address.get('StreetNamePreDirectional', ''),
            tagged_address.get('StreetNamePreModifier', ''),
            tagged_address.get('StreetNamePreType', ''),
            tagged_address.get('StreetName', ''),
            tagged_address.get('StreetNamePostDirectional', ''),
            tagged_address.get('StreetNamePostModifier', ''),
            tagged_address.get('StreetNamePostType', '')
        )

        street_name = ' '.join(street_name_seq)
        street_name = ' '.join(street_name.strip().split())

        street_address = ' '.join((address_number, street_name))

        address_dict = {'address': street_address,
                        'city': tagged_address.get('PlaceName', ''),
                        'state': tagged_address.get('StateName', ''),
                        'zip': int(tagged_address.get('ZipCode', ''))}

        log.info('Successfully parsed {} into {}'.format(address_str, address_dict))

    return address_dict


def get_coordinates_from_address(address_dict):
    geolocator = Nominatim(user_agent="__name__", scheme="http")

    query = {
        'street': address_dict['address'],
        'city': address_dict['city'],
        'state': address_dict['state'],
        'postalcode': str(address_dict['zip'])
    }
    location = geolocator.geocode(query)

    if location:
        x = location.latitude
        y = location.longitude
        return {'x': x, 'y': y}
    else:
        return None
