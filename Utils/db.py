import os
import sqlite3


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def create_connection(db_file):
    try:
        conn = sqlite3.connect(db_file, check_same_thread=False)
        conn.row_factory = dict_factory
        return conn
    except sqlite3.Error as e:
        print(e)
        return None


print(os.getcwd() + '/athlessary-database.db')
conn = create_connection(os.getcwd() + '/athlessary-database.db')


def insert(table_name, col_names, col_params):
    """

    :param table_name: name of hte table to insert into
    :param col_names: the names of the columns
    :param col_params: the data to insert
    :return: return the user ID
    """

    col_to_str = ', '.join(col_names)
    params_tuple = tuple(col_params)
    q_marks = ['?' for i in range(len(col_params))]
    q_marks = ', '.join(q_marks)
    sql = 'INSERT INTO %s (%s) VALUES (%s)' % (table_name, col_to_str, q_marks)

    cur = conn.cursor()
    print('getting the execute ret val')
    row_id = cur.execute(sql, params_tuple).lastrowid
    conn.commit()
    cur.close()

    return row_id


def delete_entry(table_name, id_col_name, item_id):
    """

    :param id_col_name: the name of the column name containing the numerical ID
    :param table_name: name of the table to delete from
    :param item_id: id of the entry to be deleted
    :return: nothing
    """

    sql = 'DELETE FROM %s WHERE %s=?' % (table_name, id_col_name)
    params = (item_id,)

    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    cur.close()


def set_where_clause(cols, operators=None):
    if operators is None:
        operators = ['=' for i in range(len(cols))]

    base = '%s%s? ' % (cols[0], operators[0])
    where_col_to_str = ['AND %s%s?' % (cols[i], operators[i]) for i in range(1, len(cols))]
    return base + ' '.join(where_col_to_str)


def select(table_name, select_cols, where_cols=None, where_params=None, operators=None, order_by=None,
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
    cur = conn.cursor()

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


def update(table_name, update_cols, update_params, where_cols, where_params, operators=None):
    """

    :param table_name:
    :param update_cols:
    :param update_params:
    :param where_cols:
    :param where_params:
    :return:
    """

    cur = conn.cursor()

    set_str = [update_cols[i] + '=?' for i in range(len(update_cols))]
    set_str = ', '.join(set_str)

    where_str = set_where_clause(where_cols, operators)

    sql = 'UPDATE %s SET %s WHERE %s' % (table_name, set_str, where_str)

    params = tuple(update_params) + tuple(where_params)

    cur.execute(sql, params)

    conn.commit()


