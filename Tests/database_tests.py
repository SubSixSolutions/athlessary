import unittest

from Utils.db import Database
from Utils.util_basic import create_workout

# It's okay that this doesn't exist because the database initializer ensures it's setup properly
db = Database("test-database.db")


class TestAutoDB(unittest.TestCase):
    """
    Test automated insert, select, and update sql creation
    """

    db = Database("test-database.db")

    def test_clean_database_begin(self):
        # assert empty
        rows = self.db.select('users', ['id'], fetchone=False)
        for _id in rows:
            self.db.delete_entry('users', 'id', _id['id'])
        rows = self.db.select('users', ['id'], fetchone=False)
        self.assertEqual([], rows, 'not all deleted!!')
        print(rows)

    def test_insert(self):
        sample_col_names = ['username', 'first', 'last', 'password', 'address', 'has_car', 'num_seats']
        sample_data = ['h1i', 'hello', 'bye', '123', '1 east green', True, 3]
        table = 'users'
        row_id = self.db.insert(table, sample_col_names, sample_data)
        self.assertGreater(row_id, 0, 'row id must be greater than 0')
        self.db.delete_entry(table, 'id', row_id)

    def test_select(self):

        # insert new row
        cur_username = '123a4bob112342'
        first_name = 'jimmy'
        last_name = 'ricky'
        sample_col_names = ['username', 'first', 'last', 'password', 'address', 'has_car', 'num_seats']
        sample_data = [cur_username, first_name, last_name, '123', '1 east green', True, 4]
        table = 'users'
        row_id = self.db.insert(table, sample_col_names, sample_data)

        # select ALL by 1 parameter (ID)
        row = self.db.select(table, ['ALL'], ['id'], [row_id])
        print(row)
        self.assertEqual(cur_username, row['username'], 'incorrect username')

        # select 1 parameter (first name) by 1 parameter (ID)
        row = self.db.select(table, ['first'], ['id'], [row_id])
        print(row)
        self.assertEqual(first_name, row['first'], 'incorrect first name')

        # select 2 parameters (first, last) by 1 parameter (ID)
        row = self.db.select(table, ['first', 'last'], ['id'], [row_id])
        print(row)
        self.assertEqual(first_name, row['first'], 'incorrect first name')
        self.assertEqual(last_name, row['last'], 'incorrect last name')

        # select 2 parameters (first, last) by 2 parameters (ID, username)
        row = self.db.select(table, ['first', 'last'], ['id', 'username'], [row_id, cur_username])
        print(row)
        self.assertEqual(first_name, row['first'], 'incorrect first name')
        self.assertEqual(last_name, row['last'], 'incorrect last name')

        # insert another row
        cur_username = 'jiam1'
        first_name = 'jane'
        last_name = 'robby'
        sample_col_names = ['username', 'first', 'last', 'password', 'address', 'has_car', 'num_seats']
        sample_data = [cur_username, first_name, last_name, '123', '1 east green', True, 3]
        table = 'users'
        row_id = self.db.insert(table, sample_col_names, sample_data)

        # test fetch many without where clause
        rows = self.db.select(table, ['id'], fetchone=False)
        self.assertEqual(2, len(rows))
        print(rows)

        # test fetch many with where clause
        rows = self.db.select(table, ['id'], ['address'], ['1 east green'], fetchone=False)
        self.assertEqual(2, len(rows))
        print(rows)

        # test different operator (one operator)
        rows = self.db.select(table, ['username', 'id'], ['id'], [10000], ['<'], fetchone=False)
        self.assertEqual(2, len(rows))
        print(rows)

        # test different operator (two operators)
        rows = self.db.select(table, ['username', 'id'], ['id', 'address'], [10000, '1 east green'], ['<', '='], fetchone=False)
        self.assertEqual(2, len(rows))
        print(rows)

        # test different operator (three operators)
        rows = self.db.select(table, ['username', 'id'], ['id', 'address', 'num_seats'], [10000, '1 east green', '1'], ['<', '=', '>'],
                              fetchone=False)
        self.assertEqual(2, len(rows))
        print(rows)

        # TODO test oder by

        # delete all entries
        for _id in rows:
            self.db.delete_entry(table, 'id', _id['id'])

        # assert empty
        rows = self.db.select(table, ['id'], fetchone=False)
        self.assertEqual([], rows, 'not all deleted!!')
        print(rows)

    def test_update(self):
        # insert new row
        cur_username = '123a4bob112342'
        first_name = 'jimmy'
        last_name = 'ricky'
        sample_col_names = ['username', 'first', 'last', 'password', 'address', 'has_car', 'num_seats']
        sample_data = [cur_username, first_name, last_name, '123', '1 east green', True, 4]
        table = 'users'
        row_id = self.db.insert(table, sample_col_names, sample_data)

        self.db.update(table, ['picture'], ['my pic'], ['id'], [row_id], ['='])

        row = self.db.select(table, ['picture'], ['id'], [row_id])

        self.assertEqual(row['picture'], 'my pic', 'does not match pictaure')

    def test_clean_database_end(self):
        # assert empty
        rows = self.db.select('users', ['id'], fetchone=False)
        for _id in rows:
            self.db.delete_entry('users', 'id', _id['id'])
        rows = self.db.select('users', ['id'], fetchone=False)
        self.assertEqual([], rows, 'not all deleted!!')
        print(rows)


class TestDBSpecific(unittest.TestCase):

    def test_aggregate_workouts(self):
        # add user
        sample_col_names = ['username', 'first', 'last', 'password', 'address', 'has_car', 'num_seats']
        sample_data = ['h1i', 'hello', 'bye', '123', '1 east green', True, 3]
        table = 'users'
        row_id = db.insert(table, sample_col_names, sample_data)

        # add workout
        meters = [2000, 2000]
        minutes = [6, 7]
        seconds = [58, 1]
        by_distance = True
        create_workout(row_id, db, meters, minutes, seconds, by_distance)

        res = db.get_aggregate_workouts_by_name(row_id, '2x2000m')
        print(res)
        self.assertIsNotNone(res, 'result should not be none')
        self.assertEqual(res[0]['total_seconds'], 419.5, 'seconds are wrong')
