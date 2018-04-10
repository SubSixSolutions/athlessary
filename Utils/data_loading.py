import csv

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

            if 'first_name' not in keys or 'last_name' not in keys:
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
                else:
                    csv_row_data[key] = None

            if 'm/w' in keys and 'v/n' in keys:
                csv_row_data['team'] = row['m/w'] + row['v/n']
            else:
                csv_row_data['team'] = None

            User.user_from_csv_row(csv_row_data)


def validate_phone_number(phone_number_str):
    if type(phone_number_str) is not str:
        return None

    phone_number_str = phone_number_str.replace('-', '')
    if len(phone_number_str) is not 10:
        return None
    else:
        return int(phone_number_str)
