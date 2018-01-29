import unittest

from Utils import db


class TestDB(unittest.TestCase):

    def test_insert(self):
        sample_col_names = ['username', 'first', 'last', 'password', 'address', 'has_car', 'num_seats']
        sample_data = ['h1i', 'hello', 'bye', '123', '1 east green', True, 3]
        table = 'users'
        row_id = db.insert(table, sample_col_names, sample_data)
        self.assertGreater(row_id, 0, 'row id must be greater than 0')
        db.delete_entry(table, 'id', row_id)
