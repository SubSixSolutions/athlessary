import datetime
import os

from flask import Flask, render_template, request, redirect, url_for, flash, Response
from flask import json
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_uploads import configure_uploads, patch_request_class
from passlib.hash import pbkdf2_sha256

import Forms.web_forms as web_forms
from User.user import User
from Utils.db import Database
from Utils.util_basic import create_workout

app = Flask(__name__)
# TODO Update secret key and move to external file
app.secret_key = 'super secret string'  # Change this!
app.debug = True
app.config['UPLOADED_PHOTOS_DEST'] = os.getcwd()

configure_uploads(app, web_forms.photos)
patch_request_class(app)  # set maximum file size, default is 16MB

login_manager = LoginManager()
login_manager.init_app(app)

db = Database("athlessary-database.db")


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    handles signup of the user
    :return: profile page of the user
    """

    # form to handle sign up
    form = web_forms.SignUpForm()

    # if form is validated and method is post
    if request.method == 'POST' and form.validate():
        # log new user in
        curr_user = User.user_from_form(form.data)
        login_user(curr_user)

        # redirect user to their new profile page
        flash('signed in!')
        return redirect(url_for('profile_page', username=current_user.username))

    # display sign up form
    return render_template('signup.html', form=form)


@app.route('/', methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    else:
        username = request.form['username']
        password = request.form['password']

        result = db.select('users', ['password', 'id'], ['username'], [username])

        print(result)
        hash = result['password']
        password_match = pbkdf2_sha256.verify(password, hash)
        if password_match:
            curr_user = User(result['id'])
            login_user(curr_user)
            flash("LOGIN SUCCESSFUL")
            return redirect(url_for('profile_page', username=username))
        return render_template('login.html')


@app.route('/userlist')
@login_required
def userlist():
    users = db.select('users', ['ALL'], order_by=['username'])

    return render_template('userlist.html', user_list=users)


@app.route('/<username>', methods=['POST', 'GET'])
@login_required
def profile_page(username):
    # TODO more elegant solution to not found page

    if username == current_user.username:

        # create photo form
        form = web_forms.PhotoForm()

        # check to see if user is trying to upload a photo
        if form.validate_on_submit():
            # save file and update the current user
            current_user.change_profile_picture(form)

            # TODO Should we commit the changes here? It won't hurt to commit them later

        # render profile page
        return render_template('profile.html', photo_form=form)
    return render_template('404.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    print("LOGGING OUT")
    return redirect(url_for('login'))


@app.route('/add_workout', methods=['GET', 'POST'])
@login_required
def add_workout():
    if request.method == 'POST':

        # TODO implement other workouts

        # get the parameters from the form
        meters = request.form.getlist('meters')
        minutes = request.form.getlist('minutes')
        seconds = request.form.getlist('seconds')

        # is workout by distance or by time?
        by_distance = False
        if request.form.get('workout_type') == 'Distance':
            by_distance = True

        # add workout to database
        create_workout(current_user.user_id, db, meters, minutes, seconds, by_distance)

        return redirect(url_for('profile_page', username=current_user.username))

    workouts = db.get_workouts(current_user.user_id)

    return render_template('workout.html', workouts=workouts)


@app.route("/chart")
def chart():

    workout_names = db.find_all_workout_names(current_user.user_id)
    return render_template('chart.html', workouts=workout_names)


@app.route('/api_hello', methods=['GET', 'POST'])
def api_hello():

    if request.method == 'POST':
        workout_name = request.form['share']
        results = db.get_aggregate_workouts_by_name(current_user.user_id, workout_name)
    else:
        results = db.get_aggregate_workouts_by_name(current_user.user_id, '5x5min')

    data_arr = []
    label_arr = []

    for res in results:
        print(res['by_distance'])
        if res['by_distance'] == 0:
            data_arr.append(res['distance'])
        else:
            data_arr.append(res['total_seconds']/float(60))
        label_arr.append(datetime.datetime.fromtimestamp(res['time']).strftime('%Y-%m-%d %H:%M:%S'))

    data = {
        'data': data_arr,
        'labels': label_arr
    }
    js = json.dumps(data)

    resp = Response(js, status=200, mimetype='application/json')

    return resp


if __name__ == '__main__':
    app.run()
