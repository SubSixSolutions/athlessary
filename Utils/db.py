import sqlite3

import psycopg2
from psycopg2 import extras, sql as SQL

from Utils.log import log

connect_str = "dbname='test' user='athlessary_admin' host='test-db.cwhz0vdyxldt.us-west-2.rds.amazonaws.com' " + \
              "password='Athlessary18' port='5432'"


def set_where_clause(cols, operators=None):
    """
    given an array of columns, this sets a string to become the 'WHERE' clause in a query
    using the correct set of operators (=, <, >)
    :param cols: an array of the names of columns to search for
    :param operators: optional; an array of strings of mathematical operators
    :return: a string of the form 'col_name=? AND col2_name>?' etc.
    """
    if operators is None:
        operators = ['=' for i in range(len(cols))]

    base = '%s%s? ' % (cols[0], operators[0])
    where_col_to_str = ['AND %s%s?' % (cols[i], operators[i]) for i in range(1, len(cols))]
    return base + ' '.join(where_col_to_str)


class Database:
    def __init__(self, db_file):
        try:
            self.conn = psycopg2.connect(connect_str, cursor_factory=extras.RealDictCursor)
            self.init_tables()
            log.info('Return NEW database object')
        except sqlite3.Error as e:
            log.error(e, exc_info=True)
            self.conn = None

    def valid_connection(self):
        if self.conn is not None:
            return True
        return False

    def create_users(self):
        cur = self.conn.cursor()

        # cur.execute("DROP TABLE IF EXISTS users")

        sql = '''CREATE TABLE IF NOT EXISTS users (
                password  VARCHAR(255),
                user_id   SERIAL           PRIMARY KEY,
                first     VARCHAR(20)      NOT NULL,
                last      VARCHAR(20)      NOT NULL,
                username  VARCHAR(20)      UNIQUE
                                           NOT NULL,
                address   VARCHAR(150),
                city      VARCHAR(255),
                state     VARCHAR(255),
                zip       INTEGER,
                num_seats INTEGER          DEFAULT (0),
                phone     INTEGER,
                team      VARCHAR(20),
                y         REAL,
                x         REAL
            );'''

        cur.execute(sql)
        self.conn.commit()

        sql = '''CREATE OR REPLACE FUNCTION remove_profile() RETURNS trigger AS
                $$
                BEGIN
                    DELETE FROM profile
                    WHERE profile.user_id = old.user_id;
                END;
                $$
                LANGUAGE plpgsql;
                '''

        cur.execute(sql)

        cur.execute("DROP TRIGGER IF EXISTS delete_profile on users;")

        sql = '''CREATE TRIGGER delete_profile
                 AFTER DELETE
                 ON users
                 FOR EACH ROW
                 EXECUTE PROCEDURE remove_profile();'''

        cur.execute(sql)
        self.conn.commit()
        cur.close()

    def create_profile(self):
        cur = self.conn.cursor()
        sql = '''CREATE TABLE IF NOT EXISTS profile (
                        user_id INTEGER      UNIQUE PRIMARY KEY NOT NULL,
                        picture VARCHAR(255) NOT NULL DEFAULT ('images/defaults/profile.jpg'),
                        bio     VARCHAR(250) NOT NULL);'''
        cur.execute(sql)
        self.conn.commit()
        cur.close()

    def create_workouts(self):
        cur = self.conn.cursor()

        sql = '''CREATE TABLE IF NOT EXISTS workout (
                    workout_id  SERIAL         PRIMARY KEY,
                    user_id     INTEGER        NOT NULL,
                    time        INTEGER        NOT NULL,
                    by_distance BOOLEAN        NOT NULL,
                    name        VARCHAR(25)    NOT NULL
                );'''

        cur.execute(sql)

        # remove  pieces in workout if workout is deleted

        sql = '''CREATE OR REPLACE FUNCTION remove_all_pieces() RETURNS trigger AS
                $$
                BEGIN
                  DELETE FROM erg
                    WHERE erg.workout_id IN (
                        SELECT erg.workout_id
                        FROM erg
                        WHERE erg.workout_id = old.workout_id
                    );
                END;
                $$
                LANGUAGE plpgsql;
                '''

        cur.execute(sql)

        cur.execute("DROP TRIGGER IF EXISTS delete_all_pieces on workout;")

        sql = '''CREATE TRIGGER delete_all_pieces
                     AFTER DELETE
                     ON workout
                     FOR EACH ROW
                     EXECUTE PROCEDURE remove_all_pieces();'''

        cur.execute(sql)
        self.conn.commit()
        cur.close()

    def create_erg(self):
        cur = self.conn.cursor()

        sql = '''CREATE TABLE IF NOT EXISTS erg (
                    erg_id     SERIAL  NOT NULL PRIMARY KEY,
                    workout_id INTEGER NOT NULL,
                    distance   INTEGER NOT NULL,
                    minutes    INTEGER NOT NULL,
                    seconds    INTEGER NOT NULL
                );'''

        cur.execute(sql)

        sql = '''CREATE OR REPLACE FUNCTION remove_workouts_without_pieces() RETURNS trigger AS
                $$
                BEGIN
                    DELETE FROM workout
                    WHERE workout.workout_id NOT IN (
                        SELECT erg.workout_id
                        FROM erg
                        GROUP BY erg.workout_id
                    );
                END
                $$
                LANGUAGE plpgsql;
              '''

        cur.execute(sql)

        cur.execute("DROP TRIGGER IF EXISTS delete_workouts_without_pieces on erg;")

        sql = '''CREATE TRIGGER delete_workouts_without_pieces
                 AFTER DELETE
                 ON erg
                 EXECUTE PROCEDURE remove_workouts_without_pieces();'''

        cur.execute(sql)

        self.conn.commit()
        cur.close()

    def init_tables(self):
        """
        sets up the database by calling functions to create each table
        and its relevant triggers
        :return:
        """
        self.create_users()
        self.create_workouts()
        self.create_erg()
        self.create_profile()

    def insert(self, table_name, col_names, col_params):
        """
        :param table_name: name of hte table to insert into
        :param col_names: the names of the columns
        :param col_params: the data to insert
        :return: return the ID
        """

        cols = SQL.SQL(', ').join(SQL.Identifier(n) for n in col_names)
        params = SQL.SQL(', ').join(SQL.Literal(l) for l in col_params)
        sql = SQL.SQL("INSERT INTO {0} ({1}) VALUES ({2})".format(SQL.Identifier(table_name), cols, params))
        print(sql.as_string(self.conn))

        q1 = SQL.SQL("insert into {} ({}) values ({}) returning {}").format(SQL.Identifier(table_name),
                                                               SQL.SQL(', ').join(map(SQL.Identifier, col_names)),
                                                               SQL.SQL(', ').join(SQL.Placeholder() * len(col_names)),
                                                               SQL.Identifier('user_id'))
        print(q1.as_string(self.conn))

        cur = self.conn.cursor()

        cur.execute(q1, list(col_params))

        row_id = cur.fetchone()['user_id']

        self.conn.commit()

        log.info(cur.query)

        cur.close()

        return row_id

    def delete_entry(self, table_name, id_col_name, item_id):
        """
        :param id_col_name: the name of the column name containing the numerical ID
        :param table_name: name of the table to delete from
        :param item_id: id of the entry to be deleted
        :return: nothing
        """

        sql = 'DELETE FROM %s WHERE %s=?' % (table_name, id_col_name)
        params = (item_id,)

        cur = self.conn.cursor()
        cur.execute(sql, params)
        self.conn.commit()
        cur.close()

        log.info('Delete on %s' % table_name)

    def select(self, table_name, select_cols, where_cols=None, where_params=None, operators=None, order_by=None,
               group_by=None, fetchone=True):
        """
        selects from database; can set select_cols to ['ALL'] to use '*' SQL operator
        :param group_by:
        :param order_by: list of columns to sort results by
        :param operators: list of operators for query, =, <, >
        :param fetchone: true if only to fetchone, otherwise use fetchall
        :param table_name: name of the table to access
        :param select_cols: list of the names of the columns for the select clause
        :param where_cols: list of the names of the columns specified in the where clause
        :param where_params: list of the parameter values to compare the where columns to
        :return: the row(s), if any, matching the query
        """

        # TODO implement group by

        # create cursor
        cur = self.conn.cursor()

        # set up ordering
        if order_by:
            order = ' ORDER BY ' + ', '.join(order_by)
        else:
            order = ''

        # determine select - All or individual attributes
        if select_cols == ['ALL']:
            select_cols_to_str = '*'
        else:
            select_cols_to_str = ', '.join(select_cols)

        # select all rows in table if no where clause is specified
        if where_cols is None:
            sql = 'SELECT %s FROM %s%s' % (select_cols_to_str, table_name, order)
            print(sql)
            cur.execute('SELECT %s FROM %s%s' % (select_cols_to_str, table_name, order))
            result = cur.fetchall()
            cur.close()
            return result

        # set up 'WHERE' part of query
        where_col_to_str = set_where_clause(where_cols, operators)

        params_tuple = tuple(where_params)
        if type(params_tuple[0]) == list:
            litty_list = tuple(map(int, params_tuple[0]))
            sql = 'SELECT %s FROM %s WHERE %s IN %s;' % (select_cols_to_str, table_name, where_cols[0], litty_list)
            cur.execute(sql)
            result = cur.fetchall()
            return result
        else:
            sql = 'SELECT %s FROM %s WHERE %s' % (select_cols_to_str, table_name, where_col_to_str)

        if order_by:
            sql += ' ORDER BY ' + ', '.join(order_by)

        log.info('sql:%s and params:%s' % (sql, params_tuple))

        # execute the query
        cur.execute(sql, params_tuple)

        # determine whether to fetch one or all
        if fetchone:
            result = cur.fetchone()
        else:
            result = cur.fetchall()
        cur.close()

        log.info('Select on table %s' % table_name)

        return result

    def update(self, table_name, update_cols, update_params, where_cols, where_params, operators=None):
        """
        Similar to select; automates process of updating database rows
        :param table_name: string; the name of the table to perform the update on
        :param update_cols: array; the names of the columns being updated
        :param update_params: array; the parameters to set the update columns to
        :param where_cols: array; the names of the columns to be specified in the 'WHERE' clause
        :param where_params: array; the parameters to search for in the 'WHERE" clause
        :param operators: optional array; mathematical operators for 'WHERE' clause
        :return:
        """

        cur = self.conn.cursor()

        set_str = [update_cols[i] + '=?' for i in range(len(update_cols))]
        set_str = ', '.join(set_str)

        where_str = set_where_clause(where_cols, operators)

        sql = 'UPDATE %s SET %s WHERE %s' % (table_name, set_str, where_str)

        params = tuple(update_params) + tuple(where_params)

        cur.execute(sql, params)

        self.conn.commit()

        cur.close()

        log.info('Update on table %s' % table_name)

    def get_workouts(self, user_id):
        """
        joins workouts and ergs and returns the result
        :param user_id: the id of the current user
        :return: array of dictionaries representing table rows
        """
        cur = self.conn.cursor()

        sql = '''
              SELECT *
              FROM workout AS w
              JOIN erg AS e
              ON e.workout_id = w.workout_id
              WHERE w.user_id=?
              '''

        cur.execute(sql, (user_id,))

        result = cur.fetchall()
        cur.close()
        return result

    def get_workouts_by_id(self, user_id, workout_id):
        """
        joins workouts and ergs and returns the result
        :param user_id: the id of the current user
        :return: array of dictionaries representing table rows
        """
        cur = self.conn.cursor()

        sql = '''
              SELECT *
              FROM workout AS w
              JOIN erg AS e
              ON e.workout_id = w.workout_id
              WHERE w.user_id=?
              AND e.workout_id=?
              '''

        cur.execute(sql, (user_id, workout_id))

        result = cur.fetchall()
        cur.close()
        return result

    def get_aggregate_workouts_by_name(self, user_id, workout_name):
        """
        for each workout of a specific type (for which there may be several pieces),
        take the average distance and time of all the pieces in the workout
        :param user_id:
        :param workout_name:
        :return: an array of dictionaries, each representing a workout with
        aggregated totals for distance and time
        """
        cur = self.conn.cursor()

        sql = '''
              SELECT w.by_distance, AVG(e.distance) AS distance,
              AVG((e.minutes*60)+e.seconds) AS total_seconds, w.time, w.workout_id
              FROM workout AS w
              JOIN erg AS e
              ON e.workout_id = w.workout_id
              WHERE w.user_id=?
              AND w.name=?
              GROUP BY e.workout_id
              ORDER BY w.time
              '''

        cur.execute(sql, (user_id, workout_name))

        result = cur.fetchall()
        cur.close()
        return result

    def get_aggregate_workouts_by_id(self, user_id):
        """
        for each workout of a specific type (for which there may be several pieces),
        take the average distance and time of all the pieces in the workout
        :param user_id:
        :param workout_name:
        :return: an array of dictionaries, each representing a workout with
        aggregated totals for distance and time
        """
        cur = self.conn.cursor()

        sql = '''
              SELECT w.by_distance, AVG(e.distance) AS distance,
              AVG((e.minutes*60)+e.seconds) AS total_seconds, w.time,
              w.name, w.workout_id
              FROM workout AS w
              JOIN erg AS e
              ON e.workout_id = w.workout_id
              WHERE w.user_id=?
              GROUP BY e.workout_id
              ORDER BY w.time DESC
              '''

        cur.execute(sql, (user_id,))

        result = cur.fetchall()
        cur.close()
        import datetime
        for res in result:
            res['time'] = datetime.datetime.fromtimestamp(res['time']).strftime('%b %d %Y %p')
            # res['time'] = datetime.datetime.fromtimestamp(res['time']).strftime('%Y-%m-%d %H:%M:%S')
            splits = res['distance'] / float(500)
            res['avg_sec'] = format(((res['total_seconds'] / splits) % 60), '.2f')
            res['avg_min'] = int(res['total_seconds'] / splits / 60)

        return result

    def find_all_workout_names(self, user_id):
        """
        returns all the distinct names of the workouts
        a user has completed having more than 1 workout
        logged under that name
        :param user_id: the id of the current user
        :return: a list of strings (workout names)
        """
        cur = self.conn.cursor()
        print(user_id)
        sql = '''SELECT DISTINCT name
                 FROM workout
                 WHERE user_id=?
                 GROUP BY name
                 HAVING COUNT(workout_id) > 1 '''

        cur.execute(sql, (user_id,))

        result = cur.fetchall()
        print(result)
        cur.close()
        return result

    def get_total_meters(self, user_id):
        """
        aggregates all of the total meters for a user
        :param user_id: the current user to aggregate all meters for
        :return: a integer; total meters rowed by individual
        """
        cur = self.conn.cursor()
        sql = '''SELECT SUM(e.distance) AS total_meters
                 FROM workout AS w
                 JOIN erg AS e
                 ON e.workout_id = w.workout_id
                 WHERE w.user_id=?
                 GROUP BY user_id'''
        cur.execute(sql, (user_id,))
        result = cur.fetchone()
        print(result)
        cur.close()
        return result

    def get_user(self, user_id):
        cur = self.conn.cursor()

        sql = '''SELECT *
                 FROM users as u
                 JOIN profile as p
                 ON u.user_id = p.user_id
                 WHERE u.user_id=?
              '''

        cur.execute(sql, (user_id,))
        result = cur.fetchone()
        cur.close()
        return result

    def get_names(self):
        self.conn.cursor_factory = extras.DictCursor

        cur = self.conn.cursor()

        sql = '''SELECT username
                 FROM users
              '''

        cur.execute(sql)
        result = cur.fetchall()
        print(result)
        cur.close()

        self.conn.cursor_factory = extras.RealDictCursor

        return result
