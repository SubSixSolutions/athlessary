import csv

from User.user import User
from Utils.log import log


def csv_to_db(path_to_csv_file):
    with open(path_to_csv_file) as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            csv_row_data = {}

            first = row['First Name']
            last = row['Last Name']
            csv_row_data['first'] = first
            csv_row_data['last'] = last
            csv_row_data['username'] = first[0] + last
            csv_row_data['address'] = ''
            csv_row_data['num_seats'] = 0
            csv_row_data['team'] = row['M/W'] + row['V/N']
            csv_row_data['phone'] = validate_phone_number(row['Phone'])
            User.user_from_csv_row(csv_row_data)


def validate_phone_number(phone_number_str):
    phone_number_str = phone_number_str.replace('-', '')
    print('{} {}'.format(phone_number_str, int(phone_number_str)))
    if len(phone_number_str) is not 10:
        return None
    else:
        return int(phone_number_str)
