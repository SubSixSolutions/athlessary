from flask import Flask
from passlib.hash import pbkdf2_sha256
import sqlite3
import hashlib, uuid
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

from User.user import User

app = Flask(__name__)
# TODO Update secret key and move to external file
app.secret_key = 'super secret string'  # Change this!
app.debug = True
login_manager = LoginManager()
login_manager.init_app(app)


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


conn = create_connection('athlessary-database.db')


@login_manager.user_loader
def load_user(user_id):
    cur = conn.cursor()
    return User(user_id, cur)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        username = request.form['username']
        password = request.form['password']

        query = " SELECT * FROM users WHERE username = ?"

        params = (username,)

        cur = conn.cursor()
        cur.execute(query, params)

        result = cur.fetchone()
        print(result)
        hash = result['password']
        password_match = pbkdf2_sha256.verify(password, hash)
        if password_match:
            curr_user = User(result['id'], cur)
            login_user(curr_user)
            flash("LOGIN SUCCESSFUL")
            return "GOOD JOB"
        return "go back and try again"


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    else:
        # TODO Check if username is unique
        username = request.form['username']
        first = request.form['first']
        last = request.form['last']
        pw = request.form['pw']
        pw_again = request.form['pw_again']
        if pw == pw_again:
            pw_hash = pbkdf2_sha256.encrypt(pw, rounds=200000, salt_size=16)

            query = "INSERT INTO users (username, first, last, password) VALUES (?, ?, ?, ?)"
            params = (username, first, last, pw_hash)

            cur = conn.cursor()
            cur.execute(query, params)
            conn.commit()
            return 'success11'
        else:
            return render_template('signup.html')


@app.route('/userlist')
@login_required
def userlist():
    cur = conn.cursor()
    query = "SELECT password, id, first, last FROM users;"

    cur.execute(query)
    users = cur.fetchall()

    return render_template('userlist.html', user_list=users)


@app.route('/')
def hello_world():
    return "hi"


@app.route('/<username>')
@login_required
def profile_page(username):

    # TODO more elegant solution to not found page

    if username == current_user.username:
        return render_template('profile.html')
    return render_template('404.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return "BYE"


if __name__ == '__main__':
    app.run()
