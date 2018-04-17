import unittest

from Utils.data_loading import csv_to_db, validate_phone_number
from Utils.db import Database
from Utils.log import log
from main import validate_filename

db = Database(True)


def clean_up_table(table, pk):
    # empty users
    rows = db.select(table, [pk], fetchone=False)
    for _id in rows:
        db.delete_entry(table, pk, _id[pk])


class TestUserLoading(unittest.TestCase):

    def test_valid_filename(self):
        valid_csv_name = 'roster.csv'
        valid_txt_name = 'roster.txt'
        csv_is_valid = validate_filename(valid_csv_name)
        txt_is_valid = validate_filename(valid_txt_name)
        self.assertTrue(csv_is_valid and txt_is_valid)

    def test_invalid_filename_easy(self):
        invalid_jpg_name = 'roster.jpg'
        jpg_is_valid = validate_filename(invalid_jpg_name)
        self.assertFalse(jpg_is_valid)

    def test_invalid_filename_hard(self):
        invalid_csv_name = 'roster.csv.jpg'
        csv_is_valid = validate_filename(invalid_csv_name)
        self.assertFalse(csv_is_valid)

    def test_valid_phone_number(self):
        valid_pn_string = '555-555-5555'
        valid_pn_int = 5555555555
        self.assertEqual(valid_pn_int, validate_phone_number(valid_pn_string))

    def test_easy_csv(self):
        clean_up_table('users', 'user_id')
        path = 'TestResources/easy_test_roster.csv'
        csv_to_db(path)
        log.debug('{}'.format(db.select('users', ['ALL'])))
        result = db.select('users', ['username'], where_cols=['username'], where_params=['jdoe'], operators=['='], fetchone=False)
        self.assertEqual([{'username': 'jdoe'}], result)
        clean_up_table('users', 'user_id')

    def test_duplicate_entry(self):
        clean_up_table('users', 'user_id')
        path = 'TestResources/easy_test_roster_w_pn.csv'
        csv_to_db(path)
        csv_to_db(path)
        result = db.select('users', ['phone'], where_cols=['username'], where_params=['jdoe'], operators=['='], fetchone=False)
        self.assertEqual([{'phone': 5555555555}], result)
        clean_up_table('users', 'user_id')
