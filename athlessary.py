from flask import Flask
import sqlite3
import hashlib, uuid
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, jsonify

app = Flask(__name__)
app.debug = True


def create_connection(db_file):
    try:
        conn = sqlite3.connect(db_file, check_same_thread=False)
        return conn
    except sqlite3.Error as e:
        print(e)
        return None


conn = create_connection('athlessary-database.db')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        cur = conn.cursor()
        username = request.form['username']
        password = request.form['password']
        #salt = uuid.uuid4().hex
        #hashed_password = hashlib.sha512(password + salt).hexdigest()

    return "welcome!"


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    else:
        first = request.form['first']
        last = request.form['last']
        pw = request.form['pw']
        pw_again = request.form['pw_again']
        if pw == pw_again:
            cur = conn.cursor()
            cur.execute('INSERT INTO users (first, last, password)\n'
                        'VALUES (?, ?, ?)', (first, last, pw))
            conn.commit()
            return 'success11'
        else:
            return render_template('signup.html')

@app.route('/userlist')
def userlist():
    cur = conn.cursor()
    cur.execute("SELECT password,\n"
                "       id,\n"
                "       first,\n"
                "       last\n"
                "      FROM users;\n"
                "      ")
    users = cur.fetchall()

    return render_template('userlist.html', user_list=users)



@app.route('/')
def hello_world():

    cur = conn.cursor()
    cur.execute('''SELECT password,
         id,
         first,
         last
    FROM users;''')
    row = cur.fetchone()
    return row[2]


if __name__ == '__main__':


    app.run()
