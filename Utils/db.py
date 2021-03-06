import os
import re
import sqlite3
import sys

import psycopg2
from psycopg2 import extras, sql as SQL

from Utils import config
from Utils.log import log


def generate_connection_string(unit_test=False):
    try:
        connect_str = "dbname=\'{0}\' user=\'{1}\' host=\'{2}\' password=\'{3}\' port=\'{4}\'".format(
            os.environ['RDS_DB_NAME'], os.environ['RDS_USERNAME'],
            os.environ['RDS_HOST_NAME'], os.environ['RDS_PASSWORD'],
            os.environ['RDS_PORT']
        )
        log.info('DB generation from environ success')
        return connect_str
    except KeyError:
        try:
            from Utils.secret_config import db_credentials

            if unit_test:
                from Utils.secret_config import unit_test_db_name
                db_name = unit_test_db_name
            else:
                from Utils.secret_config import test_db_name
                db_name = test_db_name

            connect_str = "dbname=\'{0}\' user=\'{1}\' host=\'{2}\' password=\'{3}\' port=\'{4}\'".format(
                db_name, db_credentials['username'],
                db_credentials['host'], db_credentials['password'],
                db_credentials['port']
            )
            log.info('DB {} generated from db credentials'.format(db_name))
            return connect_str
        except ModuleNotFoundError:
            sys.stderr.write('Could Not Establish Database Connection')
            sys.exit(1)


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

    base = SQL.SQL('{}{}{} ').format(SQL.Identifier(cols[0]), SQL.SQL(operators[0]), SQL.Placeholder())
    where_col_to_str = [SQL.SQL('AND {}{}{}').format(SQL.Identifier(cols[i]), SQL.SQL(operators[i]), SQL.Placeholder())
                        for i in range(1, len(cols))]
    return SQL.SQL("{} {}").format(base, SQL.SQL(" ").join(where_col_to_str))


class Database:
    def __init__(self, unit_test=False):
        """

        :param unit_test: a boolean; true if a connection to the unit test db should be opened
        """
        try:
            connect_str = generate_connection_string(unit_test)
            self.conn = psycopg2.connect(connect_str, cursor_factory=extras.RealDictCursor)
            if config.DB_INIT:
                self.init_tables()
            log.info('Return new database object from connect_str: {}'.format(connect_str))
        except sqlite3.Error as e:
            log.error(e, exc_info=True)
            self.conn = None

    def valid_connection(self):
        if self.conn is not None:
            return True
        return False

    def safe_execute(self, sql_statement, params=None, fetchone=True):
        """

        :return:
        """

        log.info("Is valid connection? -- {}".format(self.valid_connection()))

        try:
            with self.conn.cursor() as cur:
                cur.execute(sql_statement, params)
                log.info((re.sub('[\s]{2,}', '', str(cur.query))).replace('\\n', ''))
                if fetchone:
                    return cur.fetchone()
                return cur.fetchall()

        except psycopg2.InternalError or psycopg2.OperationalError as e:
            self.conn.rollback()
            log.error(e)
            log.error(sql_statement)
            log.error(params)
            log.error('roll back required')
            return None

    def safe_execute_sql_only(self, sql_statement, params=None):
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql_statement, params)
                log.info((re.sub('[\s]{2,}', '', str(cur.query))).replace('\\n', ''))

        except psycopg2.InternalError as e:
            self.conn.rollback()
            log.error(e)
            log.error(sql_statement)
            log.error('roll back required')

    def create_users(self):
        # cur.execute("DROP TABLE IF EXISTS users")

        sql = '''CREATE TABLE IF NOT EXISTS users ()'''
        self.safe_execute_sql_only(sql)

        column_list = [{'col_name': 'password', 'd_type': 'VARCHAR(255)', 'config': []},
                       {'col_name': 'user_id', 'd_type': 'SERIAL', 'config': ['PRIMARY_KEY']},
                       {'col_name': 'role', 'd_type': 'INTEGER', 'config': ['DEFAULT(1)']},
                       {'col_name': 'first', 'd_type': 'VARCHAR(20)', 'config': ['NOT NULL']},
                       {'col_name': 'last', 'd_type': 'VARCHAR(20)', 'config': ['NOT NULL']},
                       {'col_name': 'username', 'd_type': 'VARCHAR(20)', 'config': ['NOT NULL', 'UNIQUE']},
                       {'col_name': 'email', 'd_type': 'VARCHAR(255)', 'config': ['NOT NULL', 'UNIQUE']},
                       {'col_name': 'confirm_email', 'd_type': 'Boolean', 'config': ['Default(False)']},
                       {'col_name': 'address', 'd_type': 'VARCHAR(150)', 'config': []},
                       {'col_name': 'city', 'd_type': 'VARCHAR(255)', 'config': []},
                       {'col_name': 'state', 'd_type': 'VARCHAR(255)', 'config': []},
                       {'col_name': 'zip', 'd_type': 'INTEGER', 'config': []},
                       {'col_name': 'num_seats', 'd_type': 'INTEGER', 'config': ['DEFAULT(0)']},
                       {'col_name': 'phone', 'd_type': 'BIGINT', 'config': []},
                       {'col_name': 'team', 'd_type': 'VARCHAR(20)', 'config': []},
                       {'col_name': 'x', 'd_type': 'REAL', 'config': []},
                       {'col_name': 'y', 'd_type': 'REAL', 'config': []}]

        for column in column_list:
            self.add_column(table='users', col_name=column['col_name'],
                            data_type=column['d_type'],
                            config=column['config'])

            self.conn.commit()

    def add_column(self, table='', col_name='', data_type='', config=[]):
        sql = '''ALTER TABLE {} ADD {} {}'''.format(table, col_name, data_type, ' '.join(config))

        try:
            self.safe_execute_sql_only(sql)
        except psycopg2.ProgrammingError as e:
            log.error('{}'.format(e))

    def create_profile(self):
        # cur.execute("DROP TABLE IF EXISTS profile")

        sql = '''CREATE TABLE IF NOT EXISTS profile (
                        user_id INTEGER      UNIQUE PRIMARY KEY NOT NULL,
                        picture VARCHAR(255) NOT NULL DEFAULT ('defaults/profile.jpg'),
                        bio     VARCHAR(250) NOT NULL,
                        birthday     DATE,
                        height  DOUBLE PRECISION      DEFAULT(0),
                        weight  DOUBLE PRECISION      DEFAULT(0),
                        show_age BOOLEAN     DEFAULT(FALSE),
                        show_height BOOLEAN  DEFAULT(FALSE),
                        show_weight BOOLEAN DEFAULT(FALSE)
              );'''
        self.safe_execute_sql_only(sql)
        self.conn.commit()

        # trigger on profile
        sql = '''CREATE OR REPLACE FUNCTION remove_user() RETURNS trigger AS
                $$
                BEGIN
                    DELETE FROM users
                    WHERE users.user_id = old.user_id;
                    RETURN NEW;
                END;
                $$
                LANGUAGE plpgsql;
                '''

        self.safe_execute_sql_only(sql)

        self.safe_execute_sql_only("DROP TRIGGER IF EXISTS delete_user on profile;")

        sql = '''CREATE TRIGGER delete_user
                     AFTER DELETE
                     ON profile
                     FOR EACH ROW
                     EXECUTE PROCEDURE remove_user();'''

        self.safe_execute_sql_only(sql)

        # trigger on user
        sql = '''CREATE OR REPLACE FUNCTION remove_profile() RETURNS trigger AS
                $$
                BEGIN
                    DELETE FROM profile
                    WHERE profile.user_id IN (old.user_id);
                    RETURN NEW;
                END;
                $$
                LANGUAGE plpgsql;
                '''

        self.safe_execute_sql_only(sql)

        self.safe_execute_sql_only("DROP TRIGGER IF EXISTS delete_profile on users;")

        sql = '''CREATE TRIGGER delete_profile
                     AFTER DELETE
                     ON users
                     FOR EACH ROW
                     EXECUTE PROCEDURE remove_profile();'''

        self.safe_execute_sql_only(sql)
        self.conn.commit()

    def create_workouts(self):
        # cur.execute("DROP TABLE IF EXISTS workout")

        sql = '''CREATE TABLE IF NOT EXISTS workout (
                    workout_id  SERIAL         PRIMARY KEY,
                    user_id     INTEGER        NOT NULL,
                    time        TIMESTAMP      NOT NULL,
                    by_distance BOOLEAN        NOT NULL,
                    name        VARCHAR(25)    NOT NULL
                );'''

        self.safe_execute_sql_only(sql)

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
                    RETURN NEW;
                END;
                $$
                LANGUAGE plpgsql;
                '''

        self.safe_execute_sql_only(sql)

        self.safe_execute_sql_only("DROP TRIGGER IF EXISTS delete_all_pieces on workout;")

        sql = '''CREATE TRIGGER delete_all_pieces
                     AFTER DELETE
                     ON workout
                     FOR EACH ROW
                     EXECUTE PROCEDURE remove_all_pieces();'''

        self.safe_execute_sql_only(sql)
        self.conn.commit()

    def create_erg(self):
        sql = '''CREATE TABLE IF NOT EXISTS erg (
                    erg_id     SERIAL  NOT NULL PRIMARY KEY,
                    workout_id INTEGER NOT NULL,
                    distance   INTEGER NOT NULL,
                    minutes    INTEGER NOT NULL,
                    seconds    FLOAT NOT NULL
                );'''

        self.safe_execute_sql_only(sql)

        sql = '''CREATE OR REPLACE FUNCTION remove_workouts_without_pieces() RETURNS trigger AS
                $$
                BEGIN
                    DELETE FROM workout
                    WHERE workout.workout_id NOT IN (
                        SELECT erg.workout_id
                        FROM erg
                        GROUP BY erg.workout_id
                    );
                    RETURN NEW;
                END
                $$
                LANGUAGE plpgsql;
              '''

        self.safe_execute_sql_only(sql)

        self.safe_execute_sql_only("DROP TRIGGER IF EXISTS delete_workouts_without_pieces on erg;")

        sql = '''CREATE TRIGGER delete_workouts_without_pieces
                 AFTER DELETE
                 ON erg
                 EXECUTE PROCEDURE remove_workouts_without_pieces();'''

        self.safe_execute_sql_only(sql)

        self.conn.commit()

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

    def insert(self, table_name, col_names, col_params, pk):
        """
        :param pk:
        :param table_name: name of hte table to insert into
        :param col_names: the names of the columns
        :param col_params: the data to insert
        :return: return the ID
        """

        q1 = SQL.SQL("insert into {} ({}) values ({}) returning {}").format(SQL.Identifier(table_name),
                                                                            SQL.SQL(', ').join(
                                                                                map(SQL.Identifier, col_names)),
                                                                            SQL.SQL(', ').join(
                                                                                SQL.Placeholder() * len(col_names)),
                                                                            SQL.Identifier(pk))
        print(list(col_params))

        row_id = self.safe_execute(q1, list(col_params))[pk]

        self.conn.commit()

        return row_id

    def delete_entry(self, table_name, id_col_name, item_id):
        """
        :param id_col_name: the name of the column name containing the numerical ID
        :param table_name: name of the table to delete from
        :param item_id: id of the entry to be deleted
        :return: nothing
        """

        sql = SQL.SQL("DELETE FROM {} WHERE {}={}").format(SQL.Identifier(table_name), SQL.Identifier(id_col_name),
                                                           SQL.Literal(item_id))
        self.safe_execute_sql_only(sql)
        self.conn.commit()

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

        # set up ordering
        if order_by:
            order = SQL.SQL(" ORDER BY {}").format(SQL.SQL(", ").join(map(SQL.Identifier, order_by)))
        else:
            order = SQL.SQL('')

        # determine select - All or individual attributes
        if select_cols == ['ALL']:
            select_cols_to_str = SQL.SQL('*')
        else:
            select_cols_to_str = SQL.SQL(', ').join(map(SQL.Identifier, select_cols))

        # select all rows in table if no where clause is specified
        if where_cols is None:
            sql = SQL.SQL("SELECT {} FROM {}{}").format(select_cols_to_str, SQL.Identifier(table_name), order)
            result = self.safe_execute(sql, params=None, fetchone=False)
            return result

        # set up 'WHERE' part of query
        where_col_to_str = set_where_clause(where_cols, operators)

        params_tuple = tuple(where_params)
        if type(params_tuple[0]) == list:
            user_id_list = SQL.SQL(', ').join(map(SQL.Literal, params_tuple[0]))
            sql = SQL.SQL("SELECT {} FROM {} WHERE {} IN ({});").format(select_cols_to_str, SQL.Identifier(table_name),
                                                                        SQL.Identifier(where_cols[0]), user_id_list)
            result = self.safe_execute(sql, params=None, fetchone=False)
            return result
        else:
            sql = SQL.SQL("SELECT {} FROM {} WHERE {}").format(select_cols_to_str, SQL.Identifier(table_name),
                                                               where_col_to_str)

        if order_by:
            sql += order

        # execute the query
        result = self.safe_execute(sql, params_tuple, fetchone=fetchone)

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

        set_str = [SQL.SQL("{}={}").format(SQL.Identifier(update_cols[i]), SQL.Placeholder()) for i in
                   range(len(update_cols))]
        set_str = SQL.SQL(", ").join(set_str)

        where_str = set_where_clause(where_cols, operators)

        sql = SQL.SQL("UPDATE {} SET {} WHERE {}").format(SQL.Identifier(table_name), set_str, where_str)

        params = tuple(update_params) + tuple(where_params)

        self.safe_execute_sql_only(sql, params)

        self.conn.commit()

    def get_workouts(self, user_id):
        """
        joins workouts and ergs and returns the result
        :param user_id: the id of the current user
        :return: array of dictionaries representing table rows
        """

        sql = SQL.SQL(
          '''SELECT *
          FROM workout AS w
          JOIN erg AS e
          ON e.workout_id = w.workout_id
          WHERE w.user_id={}
          ORDER BY w.time DESC'''
        ).format(SQL.Literal(user_id))

        result = self.safe_execute(sql, params=None, fetchone=False)

        return result

    def get_workouts_by_id(self, user_id, workout_id):
        """
        joins workouts and ergs and returns the result of a single workout specified by the workout id
        :param user_id: the id of the current user
        :param workout_id: the workout to get
        :return: array of dictionaries representing table rows
        """

        sql = SQL.SQL(
            '''SELECT *, to_char(time, 'yyyy-mm-ddThh24:mi:ss.000Z') as time
             FROM workout AS w
             JOIN erg AS e
             ON e.workout_id = w.workout_id
             WHERE w.user_id={}
             AND e.workout_id={}
             ORDER BY e.erg_id'''
        ).format(SQL.Placeholder(), SQL.Placeholder())

        result = self.safe_execute(sql, (user_id, workout_id), fetchone=False)

        print(result)
        return result

    def get_aggregate_workouts_by_name(self, user_id, workout_name):
        """
        ** gets all workouts for a specific user with a specific workout name
        for each workout of a specific type (for which there may be several pieces),
        take the average distance and time of all the pieces in the workout
        :param user_id:
        :param workout_name:
        :return: an array of dictionaries, each representing a workout with
        aggregated totals for distance and time
        """

        sql = SQL.SQL(
            '''SELECT distance, total_seconds, w.workout_id, w.time, w.by_distance
             FROM workout AS w
             JOIN
                  (SELECT AVG(e.distance) AS distance,
                  AVG((e.minutes*60)+e.seconds) AS total_seconds, e.workout_id
                  FROM workout AS w
                  JOIN erg AS e
                  ON e.workout_id = w.workout_id
                  WHERE w.user_id={}
                  AND w.name={}
                  GROUP BY e.workout_id) AS agg_table
             ON w.workout_id = agg_table.workout_id
             ORDER BY w.time'''
        ).format(SQL.Placeholder(), SQL.Placeholder())

        result = self.safe_execute(sql, (user_id, workout_name), fetchone=False)

        return result

    def get_aggregate_workouts_by_id(self, user_id):
        """
        ** gets all workouts for a specific user
        for each workout for a specific user (for which there may be several pieces),
        take the average distance and time of all the pieces in the workout
        :param user_id: the id of the user for which to gather all workouts
        :return: an array of dictionaries, each representing a workout with
        aggregated totals for distance and time
        """
        sql = SQL.SQL(
            '''SELECT distance, total_seconds, w.workout_id, w.time, w.by_distance, w.name
             FROM workout AS w
             JOIN
                  (SELECT AVG(e.distance) AS distance,
                  AVG((e.minutes*60)+e.seconds) AS total_seconds, e.workout_id
                  FROM workout AS w
                  JOIN erg AS e
                  ON e.workout_id = w.workout_id
                  WHERE w.user_id={}
                  GROUP BY e.workout_id) AS agg_table
             ON w.workout_id = agg_table.workout_id
             ORDER BY w.time DESC'''
        ).format(SQL.Placeholder())

        result = self.safe_execute(sql, (user_id,), fetchone=False)

        for res in result:
            res['total_seconds'] = float(res['total_seconds'])
            res['distance'] = float(res['distance'])
            res['time'] = res['time'].strftime('%Y-%m-%dT%H:%M:00.000Z')
            splits = float(res['distance']) / float(500)
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
        print(user_id)
        sql = SQL.SQL(
            '''SELECT DISTINCT name
             FROM workout
             WHERE user_id={}
             GROUP BY name
             HAVING COUNT(workout_id) > 1'''
        ).format(SQL.Placeholder())

        result = self.safe_execute(sql, (user_id,), fetchone=False)

        return result

    def get_total_meters(self, user_id):
        """
        aggregates all of the total meters for a user
        :param user_id: the current user to aggregate all meters for
        :return: a integer; total meters rowed by individual
        """
        sql = SQL.SQL(
            '''SELECT SUM(e.distance) AS total_meters
             FROM workout AS w
             JOIN erg AS e
             ON e.workout_id = w.workout_id
             WHERE w.user_id={}
             GROUP BY user_id'''
        ).format(SQL.Placeholder())

        result = self.safe_execute(sql, (user_id,), fetchone=True)
        return result

    def get_user(self, user_id):
        sql = SQL.SQL(
            '''SELECT *
             FROM users as u
             JOIN profile as p
             ON u.user_id = p.user_id
             WHERE u.user_id={}'''
        ).format(SQL.Placeholder())

        result = self.safe_execute(sql, (user_id,), fetchone=True)
        return result

    def get_names(self):
        sql = SQL.SQL("SELECT ARRAY_AGG(username) as names FROM users")

        result = self.safe_execute(sql, params=None, fetchone=True)

        if result:
            return result['names']
        return None

    def get_emails(self):
        sql = SQL.SQL("SELECT ARRAY_AGG(email) as emails FROM users")

        result = self.safe_execute(sql, params=None, fetchone=True)

        if result:
            return result['emails']
        return None

    def get_leader_board_meters(self, date):
        """
        gets the total meters for every rower from a certain cutoff date
        :param date: the datetime cutoff date for meters
        :return:
        """
        q = SQL.SQL(
            '''
            SELECT SUM(tbl.distance) AS total_meters,  u.username
            FROM (
                SELECT distance, user_id
                FROM workout AS w
                JOIN erg AS e 
                ON w.workout_id = e.workout_id
                WHERE w.time>{}
                ) AS tbl
            JOIN users AS u
            ON u.user_id = tbl.user_id
            GROUP BY u.username
            ORDER BY total_meters DESC
            '''
        ).format(SQL.Placeholder())

        result = self.safe_execute(q, (date,), fetchone=False)
        return result

    def get_leader_board_minutes(self, date):
        """
        gets total minutes of each athlete from present until the cutoff date
        :param date: the datetime object of the cuttoff date
        :return:
        """
        q = SQL.SQL(
            '''
            SELECT (SUM(tbl.minutes) * 60) + SUM(tbl.seconds) AS total_seconds,  u.username
            FROM (
                SELECT user_id, minutes, seconds
                FROM workout AS w
                JOIN erg AS e 
                ON w.workout_id = e.workout_id
                WHERE w.time>{}
                ) AS tbl
            JOIN users AS u
            ON u.user_id = tbl.user_id
            GROUP BY u.username
            ORDER BY total_seconds DESC
            '''
        ).format(SQL.Placeholder())

        result = self.safe_execute(q, (date,), fetchone=False)
        return result


    def get_leader_board_split(self, date):
        """
        gets aggregated split of each athlete from present until the cutoff date
        :param date: the datetime object of the cuttoff date
        :return:
        """
        q = SQL.SQL(
            '''
            SELECT (((SUM(tbl.minutes) * 60) + SUM(tbl.seconds))::FLOAT / SUM(tbl.distance)) * 500 AS split,  u.username
            FROM (
                SELECT user_id, minutes, seconds, distance
                FROM workout AS w
                JOIN erg AS e 
                ON w.workout_id = e.workout_id
                WHERE w.time>{}
                ) AS tbl
            JOIN users AS u
            ON u.user_id = tbl.user_id
            GROUP BY u.username
            ORDER BY split
            '''
        ).format(SQL.Placeholder())

        result = self.safe_execute(q, (date,), fetchone=False)
        return result

    def get_profile_stats(self, user_id):
        """
        get the age, weight, and height of the user as well as the
        boolean values that determine whether or not the user wishes
        the values to be public
        :param user_id: the ID of the user
        :return:
        """

        q = SQL.SQL(
            '''
            SELECT weight, height, show_age, show_height, show_weight, EXTRACT(YEAR FROM AGE(birthday))::INTEGER AS age
            FROM profile
            WHERE user_id={}
            '''
        ).format(SQL.Literal(user_id))

        result = self.safe_execute(q)
        return result

    def get_heat_map_calendar_results(self, user_id):
        """
        take a user ID and a time offset (from GMT to user's local time) and return the counts of each day
        :param user_id:
        :return:
        """

        q1 = SQL.SQL(
            '''
            SELECT COUNT(time) as count, time as date
            FROM workout
            WHERE user_id={}
            GROUP BY date;
            '''
        ).format(SQL.Placeholder())

        result = self.safe_execute(q1, (user_id,), fetchone=False)
        return result

    def get_last_three_workouts(self, user_id):
        """
        ** gets all workouts for a specific user
        for each workout for a specific user (for which there may be several pieces),
        take the average distance and time of all the pieces in the workout
        :param user_id: the id of the user for which to gather all workouts
        :return: an array of dictionaries, each representing a workout with
        aggregated totals for distance and time
        """
        sql = SQL.SQL(
            '''SELECT distance, total_seconds, w.workout_id, w.time, w.by_distance, w.name
             FROM workout AS w
             JOIN
                  (SELECT AVG(e.distance) AS distance,
                  AVG((e.minutes*60)+e.seconds) AS total_seconds, e.workout_id
                  FROM workout AS w
                  JOIN erg AS e
                  ON e.workout_id = w.workout_id
                  WHERE w.user_id={}
                  GROUP BY e.workout_id) AS agg_table
             ON w.workout_id = agg_table.workout_id
             ORDER BY w.time DESC
             LIMIT 3'''
        ).format(SQL.Placeholder())

        result = self.safe_execute(sql, (user_id,), fetchone=False)

        for res in result:
            res['total_seconds'] = float(res['total_seconds'])
            res['distance'] = float(res['distance'])
            # res['time'] = res['time'].strftime('%Y-%m-%dT%H:%M:00.000Z')
            splits = float(res['distance']) / float(500)
            res['avg_sec'] = format(((res['total_seconds'] / splits) % 60), '.2f')
            res['avg_min'] = int(res['total_seconds'] / splits / 60)

        return result
