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
        # return render_template('profile.html', photo_form=form)
        workout_names = db.find_all_workout_names(current_user.user_id)
        return render_template('index.html', workouts=workout_names)
    return render_template('404.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    print("LOGGING OUT")
    return redirect(url_for('new_signup'))


@app.route('/workouts', methods=['GET', 'POST'])
@login_required
def workouts():
    if request.method == 'POST':

        # TODO implement other workouts

        # get the parameters from the form
        meters = request.form.getlist('meters[]')
        minutes = request.form.getlist('minutes[]')
        seconds = request.form.getlist('seconds[]')

        if meters != [''] and minutes != [''] and seconds != ['']:

            # is workout by distance or by time?
            by_distance = False
            if request.form.get('workout_type') == 'Distance':
                by_distance = True

            # add workout to database
            create_workout(current_user.user_id, db, meters, minutes, seconds, by_distance)

            return Response(json.dumps({}), status=201, mimetype='application/json')

    return render_template('workout.html')


@login_required
@app.route('/api_hello', methods=['POST'])
def api_hello():

    if request.method == 'POST':
        workout_name = request.form.get('share')

        if workout_name is None:
            return render_template('404.html')

        results = db.get_aggregate_workouts_by_name(current_user.user_id, workout_name)

        data_arr = []
        label_arr = []
        _ids = []

        y_axis = ''

        for res in results:
            if res['by_distance'] == 0:
                data_arr.append(res['distance'])
                y_axis = 'Meters'
            else:
                data_arr.append(res['total_seconds']/float(60))
                y_axis = 'Minutes'
            label_arr.append(datetime.datetime.fromtimestamp(res['time']).strftime('%b %d %Y %p'))
            _ids.append(res['workout_id'])

        data = {
            'data': data_arr,
            'labels': label_arr,
            'name': workout_name,
            'y_axis': y_axis,
            '_ids': _ids
        }
        js = json.dumps(data)

        return Response(js, status=200, mimetype='application/json')


@login_required
@app.route('/meters_rowed', methods=['GET'])
def meters_rowed():
    if request.method == 'GET':
        total_meters = db.get_total_meters(current_user.user_id)
        js = json.dumps(total_meters)
        return Response(js, status=200, mimetype='application/json')


@app.route('/', methods=['GET', 'POST'])
def new_signup():
    # forms to handle sign up and sign in
    signup_form = web_forms.SignUpForm()
    signin_form = web_forms.SignInForm()

    login = True

    if request.method == 'POST':
        if signin_form.data['submit_bttn']:
            if signin_form.validate():
                username = signin_form.data['username_field']
                password = signin_form.data['password_field']

                result = db.select('users', ['password', 'id'], ['username'], [username])
                print(result)
                if result:
                    hash = result['password']
                    password_match = pbkdf2_sha256.verify(password, hash)
                    if password_match:
                        curr_user = User(result['id'])
                        login_user(curr_user)
                        flash('signed in!')
                        # return render_template('test_flash.html')
                        # return redirect(url_for('profile_page', username=username))
                        return redirect(url_for('profile'))

        elif signup_form.data['submit']:
            if signup_form.validate():
                # log new user in
                curr_user = User.user_from_form(signup_form.data)
                login_user(curr_user)

                # redirect user to their new profile page
                flash('signed in!')
                # return redirect(url_for('profile_page', username=current_user.username))
                return redirect(url_for('profile'))

        login = False

    return render_template('new_signup.html', sign_up=signup_form, sign_in=signin_form, login=login)


@app.route('/get_a_workout', methods=['POST'])
def get_a_workout():
    workout_id = request.form.get('workout_id')
    result = db.get_workouts_by_id(current_user.user_id, workout_id)
    js = json.dumps(result)
    return Response(js, status=200, mimetype='application/json')


@app.route('/get_all_workouts', methods=['GET'])
def get_all_workouts():
    workouts = db.get_aggregate_workouts_by_id(current_user.user_id)
    js = json.dumps(workouts)
    return Response(js, status=200, mimetype='application/json')


@app.route('/edit_workout', methods=['POST'])
def edit_workout():

    by_distance = int(request.form.get('by_distance'))
    erg_ids = request.form.getlist('erg_ids[]')

    if by_distance == 1:
        meters = request.form.getlist('meters[]')
        for i in range(len(erg_ids)):
            db.update('erg', ['distance'], [int(meters[i])], ['erg_id'], [int(erg_ids[i])])
    else:
        minutes = request.form.getlist('minutes[]')
        seconds = request.form.getlist('seconds[]')

        for i in range(len(erg_ids)):
            db.update('erg', ['minutes', 'seconds'], [int(minutes[i]), int(seconds[i])], ['erg_id'], [erg_ids[i]])

    old_date_stamp = float(request.form.get('old_date')) // 1
    new_date = request.form.get('new_date')
    new_time = request.form.get('time')
    old_date = float(request.form.get('old_date'))
    old_date = datetime.datetime.fromtimestamp(old_date)

    new_date_arr = new_date.split('-')
    new_time_arr = new_time.split(':')
    import time
    new_date_obj = datetime.datetime(int(new_date_arr[0]), int(new_date_arr[1]), int(new_date_arr[2]), int(new_time_arr[0]), int(new_time_arr[1]), old_date.second)
    new_date = time.mktime(new_date_obj.timetuple())

    if old_date_stamp != new_date:
        workout_id = request.form.get('workout_id')
        db.update('workout', ['time'], [new_date], ['workout_id'], [workout_id])

    return Response(json.dumps({}), status=201, mimetype='application/json')


@app.route('/get_workout_names', methods=['GET'])
def get_workout_names():
    workout_names = db.find_all_workout_names(current_user.user_id)
    js = json.dumps(workout_names)
    return Response(js, status=200, mimetype='application/json')


@app.route('/delete_workout', methods=['POST'])
def delete_workout():
    workout_id = request.form.get('workout_id')
    db.delete_entry('workout', 'workout_id', workout_id)
    return Response(json.dumps({}), 201, mimetype='application/json')


@app.route('/get_all_athletes', methods=['GET'])
def get_all_athletes():
    users = db.select('users', ['ALL'], fetchone=False)
    js = json.dumps(users)
    return Response(js, status=200, mimetype='application/json')


@app.route('/roster')
def roster():
    return render_template('roster_page.html')


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    form = web_forms.ProfileForm()

    if request.method == 'POST':
        if form.validate():
            user_attrs = ['address', 'city', 'state', 'zip', 'phone', 'team', 'num_seats']
            profile_attrs = ['bio']
            user_cols = []
            profile_cols = []
            for attribute in user_attrs:
                user_cols.append(form.data[attribute])

            for attribute in profile_attrs:
                profile_cols.append((form.data[attribute]))

            db.update('users', user_attrs, user_cols, ['id'], [current_user.user_id])

            db.update('profile', profile_attrs, profile_cols, ['user_id'], [current_user.user_id])

    profile = db.select('profile', ['ALL'], ['user_id'], [current_user.user_id])
    print(profile)

    if current_user.team:
        form.team.default = current_user.team
        form.process()
    form.bio.data = profile['bio']
    if current_user.address:
        form.address.data = current_user.address
    if current_user.state:
        form.state.data = current_user.state
    if current_user.city:
        form.city.data = current_user.city
    if current_user.zip:
        form.zip.data = current_user.zip
    if current_user.phone:
        form.phone.data = current_user.phone
    form.num_seats.data = current_user.num_seats
    return render_template('profile_5.html', form=form, profile=profile)


@app.route('/save_img', methods=['POST'])
def save_img():
    import base64
    img = request.form.get('img')

    if img:
        print(img)
        img = img.split(',')[1]

        data = img.encode()
        data = base64.b64decode(data)

        # specify the directory
        directory = os.getcwd() + '/static/images/%s' % current_user.user_id

        # create directory if it does not exist
        if not os.path.exists(directory):
            os.makedirs(directory)

        imgFile = open(directory + '/profile.png', 'wb')
        imgFile.write(data)

        # update current user
        pic_location = 'images/%s/%s' % (current_user.user_id, 'profile.png')
        current_user.picture = pic_location

        # update the database
        db.update('profile', ['picture'], [pic_location], ['user_id'], [current_user.user_id])

        print('done')

    return Response(json.dumps({img: pic_location}), 201, mimetype='application/json')


if __name__ == '__main__':
    app.run()
