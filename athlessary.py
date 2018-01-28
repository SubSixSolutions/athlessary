import os
from flask import Flask
from flask_wtf import FlaskForm
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class
from flask_wtf.file import FileRequired, FileAllowed
from passlib.hash import pbkdf2_sha256
import sqlite3
import hashlib, uuid
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
from wtforms import StringField, TextField, RadioField, IntegerField, SelectField, SubmitField, PasswordField, \
    BooleanField, FileField
from wtforms.validators import InputRequired, Length
from User.user import User
from wtforms import Form, BooleanField, StringField, PasswordField, validators


app = Flask(__name__)
# TODO Update secret key and move to external file
app.secret_key = 'super secret string'  # Change this!
app.debug = True
app.config['UPLOADED_PHOTOS_DEST'] = os.getcwd()


photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)
patch_request_class(app)  # set maximum file size, default is 16MB


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


login_manager = LoginManager()
login_manager.init_app(app)
conn = create_connection('athlessary-database.db')


@login_manager.user_loader
def load_user(user_id):
    cur = conn.cursor()
    return User(user_id, cur)


class SignUpForm(FlaskForm):
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
    submit = SubmitField(u'Create Account')


class PhotoForm(FlaskForm):
    photo = FileField('Update Your Profile Pic', validators=[FileAllowed(photos, u'Image only!'), FileRequired(u'File was empty!')])
    submit = SubmitField(u'Upload')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    handles signup of the user
    :return: profile page of the user
    """

    # form to handle sign up
    form = SignUpForm()

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
            return redirect(url_for('profile_page', username=username))
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


@app.route('/<username>', methods=['POST', 'GET'])
@login_required
def profile_page(username):

    # TODO more elegant solution to not found page

    if username == current_user.username:

        # create photo form
        form = PhotoForm()

        # check to see if user is trying to upload a photo
        if form.validate_on_submit():

            # get the name of the photo
            f = form.photo.data
            filename = secure_filename(f.filename)
            extension = filename.split('.')[-1]
            name = 'profile.' + extension

            # specify the directory
            directory = os.getcwd() + '/static/images/%s' % current_user.user_id

            # create directory if it does not exist
            if not os.path.exists(directory):
                os.makedirs(directory)

            # delete old file
            if current_user.picture != 'images/defaults/profile.jpg':
                try:
                    os.remove(os.getcwd() + '/static/' + current_user.picture)
                except OSError:
                    pass

            # save image out to disk
            f.save(os.path.join(directory, filename))

            # update current user
            pic_location = 'images/%s/%s' % (current_user.user_id, filename)
            current_user.picture = pic_location

            # update the database
            cur = conn.cursor()
            cur.execute('''UPDATE users SET picture=? WHERE id=?''', (pic_location, current_user.user_id))

            # TODO Should we commit the changes here? It won't hurt to commit them later
            conn.commit()

        # render profile page
        return render_template('profile.html', photo_form=form)
    return render_template('404.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('login')


if __name__ == '__main__':
    app.run()
