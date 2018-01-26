from flask import Flask
import sqlite3
import hashlib, uuid
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
#from flask_wtf import FlaskForm, Form, validators
from wtforms import StringField, TextField, RadioField, IntegerField, SelectField, SubmitField, PasswordField, \
    BooleanField
from wtforms.validators import DataRequired, InputRequired, Length
from User.user import User
from wtforms import Form, BooleanField, StringField, PasswordField, validators




app = Flask(__name__)
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


class RegistrationForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email Address', [validators.Length(min=6, max=35)])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Repeat Password')
    accept_tos = BooleanField('I accept the TOS', [validators.DataRequired()])


@login_manager.user_loader
def load_user(user_id):
    cur = conn.cursor()
    return User(user_id, cur)


class MyForm(Form):
    username = StringField('username', validators=[Length(min=1, max=5, message="must be less than 5 chars"), InputRequired("must not be empty")])
    password = PasswordField('password')
    address = StringField('address')
    first = StringField('first name')
    last = StringField('last name')
    has_car = BooleanField('do you have a car?')
    num_seats = IntegerField('num seats')


@app.route('/login2', methods=['GET', 'POST'])
def login2():
    form = MyForm(request.form)
    if request.method == 'POST' and form.validate():
        print(form.username.data)
        print(form['username'])
        return 'hi'
    return render_template('login2.html', form=form)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        username = request.form['username']
        password = request.form['password']

        sql = '''
              SELECT *
              FROM users
              WHERE username = ?
              AND password = ?
              '''

        params = (username, password)

        cur = conn.cursor()
        cur.execute(sql, params)

        result = cur.fetchone()
        print(result)
        if result is not None:
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
@login_required
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
