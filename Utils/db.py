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

    :param table_name: name of the table to delete from
    :param item_id: id of the entry to be deleted
    :return: nothing
    """

    sql = 'DELETE from %s WHERE %s=?' % (table_name, id_col_name)
    params = (item_id,)

    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    cur.close()


def temp_select(user_id):
    sql = '''
                  SELECT *
                  FROM users
                  WHERE id = ?
                  '''

    cur = conn.cursor()
    params = (user_id,)
    cur.execute(sql, params)
    result = cur.fetchone()
    cur.close()
    return result

