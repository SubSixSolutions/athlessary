import sqlite3
from os import getcwd


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def set_where_clause(cols, operators=None):
    if operators is None:
        operators = ['=' for i in range(len(cols))]

    base = '%s%s? ' % (cols[0], operators[0])
    where_col_to_str = ['AND %s%s?' % (cols[i], operators[i]) for i in range(1, len(cols))]
    return base + ' '.join(where_col_to_str)


class Database:

    def __init__(self, db_file, df=dict_factory):
        abs_path = getcwd() + "/" + db_file
        try:
            self.conn = sqlite3.connect(abs_path, check_same_thread=False)
            self.conn.row_factory = df
            self.init_tables()
        except sqlite3.Error as e:
            print(e)
            self.conn = None

    def valid_connection(self):
        if self.conn is not None:
            return True
        return False

    def create_users(self):
        cur = self.conn.cursor()

        sql = '''CREATE TABLE IF NOT EXISTS [users] (
                    password  STRING (1, 50),
                    id        INTEGER        PRIMARY KEY AUTOINCREMENT,
                    first     STRING (1, 20) NOT NULL,
                    last      STRING (1, 20) NOT NULL,
                    username  STRING (2, 20) UNIQUE NOT NULL,
                    address   STRING (1, 50),
                    has_car   BOOLEAN,
                    num_seats INTEGER,
                    picture   BLOB           DEFAULT ('images/defaults/profile.jpg')
                    ); '''

        cur.execute(sql)
        self.conn.commit()
        cur.close()

    def create_workouts(self):
        cur = self.conn.cursor()

        sql = '''CREATE TABLE IF NOT EXISTS workout (
                    workout_id  INTEGER        PRIMARY KEY AUTOINCREMENT,
                    user_id     INTEGER        NOT NULL,
                    time        INTEGER        NOT NULL,
                    by_distance BOOLEAN        NOT NULL,
                    name        STRING (2, 20) NOT NULL
                );'''

        cur.execute(sql)
        self.conn.commit()
        cur.close()

    def create_erg(self):
        cur = self.conn.cursor()

        sql = '''CREATE TABLE IF NOT EXISTS erg (
                    erg_id     INTEGER NOT NULL
                    PRIMARY KEY AUTOINCREMENT,
                    workout_id INTEGER NOT NULL,
                    distance   INTEGER NOT NULL,
                    minutes    INTEGER NOT NULL,
                    seconds    INTEGER NOT NULL
                    );'''

        cur.execute(sql)
        self.conn.commit()
        cur.close()

    def init_tables(self):
        # TODO: clean up this query

        self.create_users()
        self.create_workouts()
        self.create_erg()

    def insert(self, table_name, col_names, col_params):
        """
        :param table_name: name of hte table to insert into
        :param col_names: the names of the columns
        :param col_params: the data to insert
        :return: return the ID
        """

        col_to_str = ', '.join(col_names)
        params_tuple = tuple(col_params)
        q_marks = ['?' for i in range(len(col_params))]
        q_marks = ', '.join(q_marks)
        sql = 'INSERT INTO %s (%s) VALUES (%s)' % (table_name, col_to_str, q_marks)

        cur = self.conn.cursor()

        row_id = cur.execute(sql, params_tuple).lastrowid
        self.conn.commit()
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

    def select(self, table_name, select_cols, where_cols=None, where_params=None, operators=None, order_by=None,
               group_by=None, fetchone=True):
        """
        selects from database
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

        # set operators to '=' if none are specified
        # if operators is None:
        #     operators = ['=' for i in range(len(where_cols))]
        #
        # base = '%s%s? ' % (where_cols[0], operators[0])
        # where_col_to_str = ['AND %s%s?' % (where_cols[i], operators[i]) for i in range(1, len(where_cols))]
        # where_col_to_str = base + ' '.join(where_col_to_str)

        where_col_to_str = set_where_clause(where_cols, operators)

        params_tuple = tuple(where_params)
        sql = 'SELECT %s FROM %s WHERE %s' % (select_cols_to_str, table_name, where_col_to_str)

        if order_by:
            sql += 'ORDER BY ' + ', '.join(order_by)

        print(sql)
        print(params_tuple)
        # execute the query
        cur.execute(sql, params_tuple)

        # determine whether to fetch one or all
        if fetchone:
            result = cur.fetchone()
        else:
            result = cur.fetchall()
        cur.close()

        return result

    def update(self, table_name, update_cols, update_params, where_cols, where_params, operators=None):
        """

        :param table_name:
        :param update_cols:
        :param update_params:
        :param where_cols:
        :param where_params:
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

    def get_workouts(self, user_id):
        cur = self.conn.cursor()

        sql = 'SELECT * ' \
              'FROM workout as w ' \
              'JOIN erg as e ' \
              'ON e.workout_id = w.workout_id ' \
              'WHERE w.user_id=?'

        cur.execute(sql, (user_id,))

        result = cur.fetchall()
        cur.close()
        return result

    def get_aggregate_workouts_by_name(self, user_id, workout_name):
        cur = self.conn.cursor()

        sql = 'SELECT w.by_distance, AVG(e.distance) AS distance, ' \
              'AVG((e.minutes*60)+e.seconds) AS total_seconds, ' \
              'w.time ' \
              'FROM workout as w ' \
              'JOIN erg as e ' \
              'ON e.workout_id = w.workout_id ' \
              'WHERE w.user_id=? ' \
              'AND w.name=? ' \
              'GROUP BY e.workout_id'

        cur.execute(sql, (user_id, workout_name))

        result = cur.fetchall()
        cur.close()
        return result

    def find_all_workout_names(self, user_id):
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
