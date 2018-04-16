import time
import unittest

from Utils.db import Database
from Utils.util_basic import create_workout

db = Database(True)


def create_user(user_name):
    # add user
    sample_col_names = ['username', 'first', 'last', 'password', 'address', 'num_seats']
    sample_data = [user_name, 'hello', 'bye', '123', '1 east green', 3]
    table = 'users'
    user_id = db.insert(table, sample_col_names, sample_data, 'user_id')

    # add user profile
    sample_col_names = ['user_id', 'picture', 'bio']
    sample_data = [user_id, 'my pic', 'hello']
    db.insert('profile', sample_col_names, sample_data, 'user_id')

    return user_id


def clean_up_table(table, pk,):
    # empty users
    rows = db.select(table, [pk], fetchone=False)
    for _id in rows:
        db.delete_entry(table, pk, _id[pk])


class TestAutoDB(unittest.TestCase):
    """
    Test automated insert, select, and update sql creation
    """

    def test_insert(self):
        """
        test insert functionality
        :return:
        """
        # create a user
        row_id = create_user('user1f023')

        # assert it exists and that it has a row_id > 0
        self.assertGreater(row_id, 0, 'row id must be greater than 0')

        # delete user
        clean_up_table('users', 'user_id')

        # assert empty
        self.assertEqual([], db.select('users', ['ALL'], fetchone=False))

    def test_select(self):
        """
        tests select functionality
        :return:
        """
        # insert new row
        cur_username = 'xyz'
        first_name = 'jimmy'
        last_name = 'ricky'
        sample_col_names = ['username', 'first', 'last', 'password', 'address', 'num_seats']
        sample_data = [cur_username, first_name, last_name, '123', '1 east green', 4]
        table = 'users'
        row_id = db.insert(table, sample_col_names, sample_data, 'user_id')

        # select ALL by 1 parameter (ID)
        row = db.select(table, ['ALL'], ['user_id'], [row_id])
        self.assertEqual(cur_username, row['username'], 'incorrect username')

        # select 1 parameter (first name) by 1 parameter (ID)
        row = db.select(table, ['first'], ['user_id'], [row_id])
        self.assertEqual(first_name, row['first'], 'incorrect first name')

        # select 2 parameters (first, last) by 1 parameter (ID)
        row = db.select(table, ['first', 'last'], ['user_id'], [row_id])
        self.assertEqual(first_name, row['first'], 'incorrect first name')
        self.assertEqual(last_name, row['last'], 'incorrect last name')

        # select 2 parameters (first, last) by 2 parameters (ID, username)
        row = db.select(table, ['first', 'last'], ['user_id', 'username'], [row_id, cur_username])
        self.assertEqual(first_name, row['first'], 'incorrect first name')
        self.assertEqual(last_name, row['last'], 'incorrect last name')

        # insert another row
        cur_username = 'jr'
        first_name = 'jane'
        last_name = 'robby'
        sample_col_names = ['username', 'first', 'last', 'password', 'address', 'num_seats']
        sample_data = [cur_username, first_name, last_name, '123', '1 east green', 3]
        table = 'users'
        row_id = db.insert(table, sample_col_names, sample_data, 'user_id')

        # test fetch many without where clause
        rows = db.select(table, ['user_id'], fetchone=False)
        self.assertEqual(2, len(rows))

        # test fetch many with where clause
        rows = db.select(table, ['user_id'], ['address'], ['1 east green'], fetchone=False)
        self.assertEqual(2, len(rows))

        # test different operator (one operator)
        rows = db.select(table, ['username', 'user_id'], ['user_id'], [10000], ['<'], fetchone=False)
        self.assertEqual(2, len(rows))

        # test different operator (two operators)
        rows = db.select(table, ['username', 'user_id'], ['user_id', 'address'], [10000, '1 east green'], ['<', '='],
                         fetchone=False)
        self.assertEqual(2, len(rows))

        # test different operator (three operators)
        rows = db.select(table, ['username', 'user_id'], ['user_id', 'address', 'num_seats'], [10000, '1 east green', '1'],
                         ['<', '=', '>'], fetchone=False)
        self.assertEqual(2, len(rows))

        # test oder by with where clause

        rows = db.select(table, ['username', 'user_id'], ['user_id', 'address'], [-1, '1 east green'], operators=['>', '='],
                         fetchone=False, order_by=['username'])

        self.assertEqual(rows[0]['username'], 'jr', 'jr comes before xyz')
        self.assertEqual(rows[1]['username'], 'xyz', 'xyz comes last')

        # test order by without where clause
        rows = db.select(table, ['username', 'user_id'], order_by=['username'], fetchone=False)
        self.assertEqual(rows[0]['username'], 'jr', 'jr comes before xyz')
        self.assertEqual(rows[1]['username'], 'xyz', 'xyz comes last')

        # delete all entries
        clean_up_table('users', 'user_id')

        # assert empty
        rows = db.select(table, ['user_id'], fetchone=False)
        self.assertEqual([], rows, 'not all deleted!')

    def test_update(self):
        """
        test update functionality
        :return:
        """
        # insert new row
        table = 'profile'
        row_id = create_user('new_user')

        # update picture field
        db.update(table, ['picture'], ['my pic'], ['user_id'], [row_id], ['='])

        row = db.select(table, ['picture'], ['user_id'], [row_id])

        # assert picture has changed
        self.assertEqual(row['picture'], 'my pic', 'does not match picture')

        # clean up
        clean_up_table('users', 'user_id')

        # assert empty
        self.assertEqual([], db.select('users', ['ALL'], fetchone=False))


class TestDBSpecific(unittest.TestCase):
    """
    test queries for specific purposes
    """

    def test_aggregate_workouts(self):
        """
        test to make sure that pieces are aggregated by workout correctly
        :return:
        """
        # add user
        row_id = create_user('my_new_user')

        # add workout
        meters = [2000, 2000]
        minutes = [6, 7]
        seconds = [58, 1]
        by_distance = True
        create_workout(row_id, db, meters, minutes, seconds, by_distance)

        # aggregate the workouts
        res = db.get_aggregate_workouts_by_name(row_id, '2x2000m')
        print(res)
        self.assertIsNotNone(res, 'result should not be none')
        self.assertEqual(res[0]['total_seconds'], 419.5, 'seconds are wrong')
        self.assertEqual(res[0]['by_distance'], by_distance, 'by_distance is incorrect')

        # Note:: this will fail if the machine is running slowly, change timedelta if so
        # self.assertTrue(res[0]['time'] - datetime.datetime.utcnow() < 10, 'time is incorrect')

        # add second workout
        meters = [2000, 2000]
        minutes = [6, 6]
        seconds = [58, 54]
        by_distance = True
        create_workout(row_id, db, meters, minutes, seconds, by_distance)

        res = db.get_aggregate_workouts_by_name(row_id, '2x2000m')

        self.assertEqual(2, len(res), 'result should not be none')
        self.assertEqual(res[1]['total_seconds'], 416, 'seconds are wrong')

        # clean up pieces
        clean_up_table('erg', 'erg_id')
        self.assertEqual(0, len(db.select('erg', ['ALL'], fetchone=False)))

        # clean up workouts
        clean_up_table('workout', 'workout_id')
        self.assertEqual(0, len(db.select('workout', ['ALL'], fetchone=False)))

        # clean up users
        clean_up_table('users', 'user_id')
        self.assertEqual(0, len(db.select('users', ['ALL'], fetchone=False)))

    def test_get_workout_names(self):
        """
        test that the unique names of the workouts are returned
        :return:
        """
        # add user
        row_id = create_user('a_user')

        names = db.find_all_workout_names(row_id)
        self.assertEqual([], names, 'names array is empty')

        # add workout
        meters = [2000, 2000]
        minutes = [6, 7]
        seconds = [50, 13]
        by_distance = True
        create_workout(row_id, db, meters, minutes, seconds, by_distance)

        # assert empty; only returns name when count of workout type > 2
        names = db.find_all_workout_names(row_id)
        self.assertEqual([], names, 'names array is empty')

        # add second workout
        meters = [2000, 2000]
        minutes = [6, 7]
        seconds = [51, 17]
        by_distance = True
        create_workout(row_id, db, meters, minutes, seconds, by_distance)

        # assert names is no longer empty
        names = db.find_all_workout_names(row_id)
        self.assertEqual('2x2000m', names[0]['name'], 'names array must have one element, 2x2000m')

        # clean up users
        clean_up_table('users', 'user_id')
        self.assertEqual(0, len(db.select('users', ['ALL'], fetchone=False)))

    def test_get_total_meters(self):
        """
        returns the total meters for a single user
        :return:
        """
        # add user
        user_id = create_user('user123')

        meters = [2000, 2000]
        minutes = [6, 7]
        seconds = [58, 1]
        by_distance = True
        create_workout(user_id, db, meters, minutes, seconds, by_distance)

        total_meters = db.get_total_meters(user_id)['total_meters']
        self.assertEqual(total_meters, 4000, 'number of meters does not match up')

        # clean up pieces
        clean_up_table('erg', 'erg_id')
        self.assertEqual(0, len(db.select('erg', ['ALL'], fetchone=False)))

        # clean up workouts
        clean_up_table('workout', 'workout_id')
        self.assertEqual(0, len(db.select('workout', ['ALL'], fetchone=False)))

        # clean up users
        clean_up_table('users', 'user_id')
        self.assertEqual(0, len(db.select('users', ['ALL'], fetchone=False)))

    def test_get_names(self):
        # returns the names of all the users in the database

        clean_up_table('users', 'user_id')

        create_user('jim')
        create_user('bob')
        create_user('jane')
        create_user('sammy')

        names = db.get_names()

        self.assertEqual(type(names), type([]), 'names is not of type array')
        self.assertTrue('jim' in names)
        self.assertTrue('bob' in names)
        self.assertTrue('jane' in names)
        self.assertTrue('sammy' in names)
        self.assertTrue('jill' not in names)

        # clean up users
        clean_up_table('users', 'user_id')
        self.assertEqual(0, len(db.select('users', ['ALL'], fetchone=False)))

    def test_get_user(self):
        # make sure profile comes with user

        user_id = create_user('tim')

        user = db.get_user(user_id)

        self.assertEqual(user['bio'], 'hello')
        self.assertEqual(user['picture'], 'my pic')
        self.assertEqual(user['user_id'], user_id)
        self.assertEqual(user['username'], 'tim')

    def test_get_workouts(self):

        user_id = create_user('joe')

        create_workout(user_id, db, [2000, 2000], [6, 6], [45, 42], True)

        workouts = db.get_workouts(user_id)

        self.assertEqual(len(workouts), 2, 'there are not 2 results')
        self.assertTrue(workouts[0]['by_distance'], 'by_distance is incorrectly set')
        self.assertEqual(workouts[0]['distance'], 2000)
        self.assertEqual(workouts[1]['minutes'], 6)

    def test_get_workout(self):
        # should return a single workout of 1+ pieces

        user_id = create_user('jane')

        create_workout(user_id, db, [5373, 5927], [30, 30], [00, 00], False)

        workout = db.get_workouts(user_id)

        # should be 2 result (2 pieces)
        self.assertEqual(len(workout), 2)

        workout_id = workout[0]['workout_id']

        my_workout = db.get_workouts_by_id(user_id, workout_id)

        # found both pieces
        self.assertEqual(len(my_workout), 2)
        self.assertEqual(my_workout[0]['by_distance'], False)
        self.assertEqual(my_workout[0]['minutes'], 30)
        self.assertEqual(my_workout[0]['seconds'], 00)

        # check order by clause; this one should be second
        self.assertEqual(my_workout[1]['distance'], 5927)

    def test_aggregate_workouts_by_id(self):
        user_id = create_user('lisa')

        create_workout(user_id, db, [5834, 5892], [30, 30], [00, 00], False)

        # pause tests to differentiate between time stamps
        time.sleep(1)

        create_workout(user_id, db, [2000, 2000], [6, 6], [59, 53], True)

        aggregates = db.get_aggregate_workouts_by_id(user_id)

        self.assertEqual(len(aggregates), 2, 'there are currently 2 workouts')
        self.assertEqual(aggregates[0]['distance'], 2000, '2k is the most recent workout')

        self.assertEqual(format(((416 / 4) % 60), '.2f'), aggregates[0]['avg_sec'], 'average second')
        self.assertEqual(int(416 / 4 / 60), aggregates[0]['avg_min'], 'average minute')


class TestTriggers(unittest.TestCase):

    def test_trigger_delete_workout_after_all_pieces_are_deleted(self):
        """
        test the trigger that is meant to delete the workout row once all of the connected
        erg pieces have been deleted
        :return:
        """
        # add a user
        user_id = create_user('123user123')

        # create workouts
        meters = [2000, 2000]
        minutes = [6, 7]
        seconds = [58, 1]
        by_distance = True
        create_workout(user_id, db, meters, minutes, seconds, by_distance)

        rows = db.select('erg', ['ALL'], fetchone=False)

        # assert that there are 2 erg pieces
        self.assertEqual(len(rows), 2, 'incorrect length of rows')

        # assert that there is one workout
        self.assertEqual(len(db.select('workout', ['ALL'], fetchone=False)), 1, 'there is one workout')

        # delete one of the erg pieces
        db.delete_entry('erg', 'erg_id', rows[0]['erg_id'])

        rows = db.select('erg', ['ALL'], fetchone=False)

        # assert that there is only one erg piece
        self.assertEqual(len(rows), 1, 'there should only be 1 row')

        # assert that there is STILL one workout
        self.assertEqual(len(db.select('workout', ['ALL'], fetchone=False)), 1, 'there is one workout')

        # delete the other erg piece
        db.delete_entry('erg', 'erg_id', rows[0]['erg_id'])

        # assert that there are no erg pieces
        self.assertEqual(len(db.select('erg', ['ALL'], fetchone=False)), 0, 'erg table is empty')

        # assert that there are no workouts
        self.assertEqual(len(db.select('workout', ['ALL'], fetchone=False)), 0, 'workout table is empty')

        # clean up users
        clean_up_table('users', 'user_id')
        self.assertEqual(0, len(db.select('users', ['ALL'], fetchone=False)))

    def test_trigger_del_pieces_after_del_workout(self):
        """
        tests the trigger for deleting all connected pieces after
        a workout has been deleted
        :return:
        """
        # add a user
        user_id = create_user('123user123')

        # create workouts
        meters = [2000, 2000]
        minutes = [6, 7]
        seconds = [52, 10]
        by_distance = True
        create_workout(user_id, db, meters, minutes, seconds, by_distance)

        # delete all workouts
        clean_up_table('workout', 'workout_id')

        # assert that there are no workouts
        self.assertEqual(len(db.select('workout', ['ALL'], fetchone=False)), 0, 'workout table is empty')

        # assert that there are no erg pieces
        self.assertEqual(len(db.select('erg', ['ALL'], fetchone=False)), 0, 'erg table is empty')

        # clean up users
        clean_up_table('users', 'user_id')
        self.assertEqual(0, len(db.select('users', ['ALL'], fetchone=False)))


class TestLeaderBoardQueries():

    def test_get_aggregate_meters(self):
        """
        test that all workouts since
        :return:
        """

        # last_sun = today - datetime.timedelta(today.isoweekday())
        # datetime.datetime(last_sun.year, last_sun.month, last_sun.day, 23, 59, 59)
