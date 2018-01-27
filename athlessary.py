from flask import Flask
from passlib.hash import pbkdf2_sha256
import sqlite3
import hashlib, uuid
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from wtforms import StringField, TextField, RadioField, IntegerField, SelectField, SubmitField, PasswordField, \
    BooleanField
from wtforms.validators import DataRequired, InputRequired, Length
from User.user import User
from wtforms import Form, BooleanField, StringField, PasswordField, validators




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


class SignUpForm(Form):
    username = StringField('username', validators=[Length(min=1, max=5, message="must be less than 5 chars"), InputRequired("must not be empty")])
    password = PasswordField('New Password', [
        validators.InputRequired(),
        validators.EqualTo('retype_pass', message='Passwords must match')
    ])
    retype_pass = PasswordField('retype password')
    address = StringField('address', validators=[validators.InputRequired()])
    first = StringField('first name', validators=[validators.InputRequired()])
    last = StringField('last name', validators=[validators.InputRequired()])
    has_car = BooleanField('do you have a car?', validators=[validators.InputRequired()])
    num_seats = IntegerField('num seats', validators=[validators.InputRequired()])


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    handles signup of the user
    :return: profile page of the user
    """

    # form to handle sign up
    form = SignUpForm(request.form)

    # if form is validated and method is post
    if request.method == 'POST' and form.validate():

        # collect form data
        username = form['username'].data
        password = form['password'].data
        address = form['address'].data
        first = form['first'].data
        last = form['last'].data
        has_car = form['has_car'].data
        num_seats = form['num_seats'].data

        # hash password
        hashed_pass = pbkdf2_sha256.encrypt(password, rounds=200000, salt_size=16)

        # insert into db
        cur = conn.cursor()
        cur.execute('INSERT INTO users (username, first, last, password, address, has_car, num_seats)\n'
                    'VALUES (?, ?, ?, ?, ?, ?, ?)', (username, first, last, hashed_pass, address, has_car, num_seats))
        conn.commit()

        # find the id of the user
        sql = '''
                      SELECT *
                      FROM users
                      WHERE username = ?
                      '''

        params = (username,)

        cur = conn.cursor()
        cur.execute(sql, params)

        result = cur.fetchone()

        # log new user in
        curr_user = User(result['id'], cur)
        login_user(curr_user)

        # redirect user to their new profile page
        flash('signed in!')
        return redirect(url_for('profile_page', username=username))

    # display sign up form
    return render_template('signup.html', form=form)


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
              '''

        params = (username,)

        cur = conn.cursor()
        cur.execute(sql, params)

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
