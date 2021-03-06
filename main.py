import base64
import os
import threading
import datetime
from urllib.parse import urlparse, urljoin, parse_qs

import boto3
from flask import Flask, render_template, request, redirect, url_for, Response, json, abort, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from passlib.hash import pbkdf2_sha256
from werkzeug.utils import secure_filename
from twilio.rest import Client
import Forms.web_forms as web_forms
from itsdangerous import URLSafeTimedSerializer

from User.user import User
from Utils import util_basic, hashes
from Utils.config import db
from Utils.driver_generation import generate_cars, modified_k_means
from Utils.log import log
from Utils.util_basic import bucket_name, verify_user_address
from Utils.util_basic import create_workout, build_graph_data
from Utils.data_loading import csv_to_db
from Utils.config import twilio_sid, twilio_auth_token, twilio_number
from Utils.hashes import hash_password
from Utils.config import password_recovery_email, password_recovery_email_creds


application = Flask(__name__)
# TODO Update secret key and move to external file
application.secret_key = 'super secret string'  # Change this!
application.debug = True

ts = URLSafeTimedSerializer(application.config["SECRET_KEY"])

CSV_UPLOAD_FOLDER = './csv_uploads'
ALLOWED_EXTENSIONS = {'csv', 'txt'}
application.config['CSV_UPLOAD_FOLDER'] = CSV_UPLOAD_FOLDER

twilio_client = Client(twilio_sid, twilio_auth_token)

login_manager = LoginManager()
login_manager.init_app(application)

# redirect unauthorized view to login page
login_manager.login_view = 'new_signup'


def sign_certificate(resource_name):
    client = boto3.client('s3')
    url = client.generate_presigned_url('get_object', Params={'Bucket': bucket_name,
                                                              'Key': resource_name}, ExpiresIn=60)
    return url


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


@login_manager.user_loader
def load_user(user_id):
    try:
        return User(user_id)
    except ValueError:
        return None


@application.route('/', methods=['GET', 'POST'])
def new_signup():
    # forms to handle sign up and sign in
    signup_form = web_forms.SignUpForm()
    signin_form = web_forms.SignInForm()

    login = True

    if request.method == 'POST':
        if signin_form.data['submit_bttn']:
            if signin_form.validate_on_submit():
                username = signin_form.data['username_field']
                password = signin_form.data['password_field']

                result = db.select('users', ['password', 'user_id'], ['username'], [username])

                log.info('here is result: {}'.format(result))

                if result:
                    hash = result['password']
                    password_match = pbkdf2_sha256.verify(password, hash)
                    if password_match:
                        curr_user = User(result['user_id'])
                        login_user(curr_user)

                        next_url = request.args.get('next')

                        if not is_safe_url(next_url):
                            return abort(400)

                        if not current_user.is_profile_complete():
                            flash('Please complete your profile before continuing!')
                            return redirect(next_url or url_for('profile'))

                        return redirect(next_url or url_for('team'))

                signin_form.username_field.errors.append("Invalid Username or Password.")

        elif signup_form.data['submit']:
            if signup_form.validate():
                # create token
                token = ts.dumps(signup_form.data['email'], salt='email-confirm-key')

                # build url
                confirm_url = url_for(
                    'confirm_email',
                    token=token,
                    _external=True)

                # set up html that makes up email
                html = render_template(
                    'signup_email.html',
                    validate_url=confirm_url,
                    user={'first': signup_form.data['first'], 'last': signup_form.data['last']})

                # create thread to speed up process
                subject = "Confirm Your Email"

                t1 = threading.Thread(target=util_basic.send_email, args=(signup_form.data['email'], html, subject))
                t1.start()

                # create user
                curr_user = User.user_from_form(signup_form.data)

                # log user in
                login_user(curr_user)

                # wait for thread
                t1.join()

                # flash message and redirect user to their new profile page
                flash('Please check your email and follow the instructions to confirm your email address.', 'alert-success')
                return redirect(url_for('profile'))

            login = False

    return render_template('signup.html', sign_up=signup_form, sign_in=signin_form, login=login,
                           _url="https://s3-us-west-2.amazonaws.com/athlessary-images/defaults/login_photo.jpg")


@application.route('/recover', methods=['GET', 'POST'])
def recover():

    form = web_forms.EnterUserName()

    if form.validate_on_submit():

        # this will exist -- the form validates it
        username = form.data['username']

        user = db.select('users', ['ALL'], ['username'], [username])

        email_address = user['email']

        subject = "Password Reset Requested"

        token = ts.dumps(email_address, salt='recover-key')

        recover_url = url_for(
            'recover_password',
            token=token,
            _external=True)

        html = render_template('recover_email.html', recover_url=recover_url, user=user)

        # send user email
        util_basic.send_email(email_address, html, subject)
        flash('Password recovery directions have been sent to your email account.', 'alert-success')
        return redirect(url_for('new_signup'))

    return render_template('recover.html', form=form)


@application.route('/reset/<token>', methods=['GET', 'POST'])
def recover_password(token):
    try:
        email = ts.loads(token, salt="recover-key", max_age=86400)
    except:
        abort(404)

    password_form = web_forms.ChangePasswordForm()

    if password_form.validate_on_submit():
        # hash password
        password = hashes.hash_password(password_form.data['new_pass'])

        # change password in the database
        db.update('users', ['password'], [password], ['email'], [email])

        # make them sign in? or redirect to home?
        flash('Password Changed!', 'alert-success')
        return redirect(url_for('new_signup'))

    return render_template('password_recovery.html', pass_form=password_form, token=token)


@application.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def profile():
    form = web_forms.ProfileForm()

    if form.validate_on_submit():
        user_attrs = ['phone', 'team', 'num_seats']
        address_attrs = ['address', 'city', 'state', 'zip']
        profile_attrs = ['bio']

        profile_cols = []

        profile_update_values = []
        profile_update_col_names = []

        for attribute in user_attrs:
            curr_attr_value = getattr(current_user, attribute)
            if form.data[attribute] != curr_attr_value:
                profile_update_values.append(form.data[attribute])
                setattr(current_user, attribute, form.data[attribute])
                profile_update_col_names.append(attribute)

        address = verify_user_address('', form.data['address'], form.data['city'], form.data['state'], form.data['zip'])

        if 'error' in address:
            flash(address['error'], 'alert-error')
            print(address['error'])

        else:
            for attribute in address_attrs:
                curr_attr_value = getattr(current_user, attribute)
                if form.data[attribute] != curr_attr_value:
                    profile_update_values.append(address[attribute])
                    setattr(current_user, attribute, address[attribute])
                    profile_update_col_names.append(attribute)

            # update x and y coordinates
            current_user.init_coordinates()

        for attribute in profile_attrs:
            profile_cols.append((form.data[attribute]))

        if len(profile_update_values) > 0:
            db.update('users', profile_update_col_names, profile_update_values, ['user_id'], [current_user.user_id])

        db.update('profile', profile_attrs, profile_cols, ['user_id'], [current_user.user_id])

    # gather user profile
    user_profile = db.select('profile', ['ALL'], ['user_id'], [current_user.get_id()])

    if current_user.num_seats > 0:
        form.num_seats.data = int(current_user.num_seats)
    if form.team:
        form.team.data = current_user.team
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
    form.bio.data = user_profile['bio']

    return render_template('profile.html', form=form, profile=user_profile, sign_certificate=sign_certificate)


@application.route('/profile/view')
def view_profile():
    profile_stats = db.get_profile_stats(current_user.user_id)
    return render_template('user_overview.html', user=current_user, sign_certificate=sign_certificate,
                           stats=profile_stats)


@application.route('/workouts', methods=['GET', 'POST'])
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
            if request.form.get('workout_type') == 'meters':
                by_distance = True

            # add workout to database
            workout_name = create_workout(current_user.user_id, db, meters, minutes, seconds, by_distance)

            return Response(json.dumps({'name': workout_name}), status=201, mimetype='application/json')

    return render_template('workout.html')


@application.route('/team')
@login_required
def team():
    meters_ranking, most_minutes, best_split = util_basic.generate_leader_board(current_user.username)
    return render_template('team.html', meters_ranking=meters_ranking, most_minutes=most_minutes,
                           best_split=best_split)


@application.route('/profile/settings', methods=['GET', 'POST'])
@login_required
def settings():
    password_form = web_forms.ChangePasswordForm()
    email_form = web_forms.ChangeEmail()
    stats_form = util_basic.set_up_stats_form(current_user.user_id, web_forms.UserStatsForm())

    # see if there is a tab number in the URL string
    par = parse_qs(urlparse(request.url).query)
    if 'tab_num' in par:
        tab_num = int(par['tab_num'][0])
    else:
        tab_num = 0

    weight_list = range(75, 325, 25)
    height_list = range(60, 85, 6)

    if request.method == 'POST':
        if password_form.data['submit'] and password_form.validate():
            new_password = hash_password(password_form.data['new_pass'])
            db.update('users', ['password'], [new_password], ['user_id'], [current_user.user_id])

            flash('Password Changed!', 'alert-success')
            return redirect(url_for('profile'))

        if email_form.data['email_submit']:
            tab_num = 1
            if email_form.validate():

                # update the email address
                db.update('users', ['email'], [email_form.data['email']], ['user_id'], [current_user.user_id])
                current_user.email = email_form.data['email']

                subject = "Confirm Email Address Change"

                # generate token
                token = ts.dumps(email_form.data['email'], salt='email-confirm-key')

                # build url
                confirm_url = url_for('confirm_email', token=token, _external=True)

                # generate email
                html = render_template('validate_email.html', validate_url=confirm_url, user=current_user)

                # set up email sending
                util_basic.send_email(email_form.data['email'], html, subject)

                # flash message and return to settings page
                flash('Please check your email and follow the instructions to confirm your new email address.', 'alert-success')
                return render_template('user_settings.html', pass_form=password_form, email_form=email_form,
                                       stats_form=stats_form, range_list=weight_list, height_list=height_list,
                                       tab_num=tab_num)

    if stats_form.data['save_changes']:
        tab_num = 2
        if stats_form.validate():

            # create new birthday
            birth_day = list(map(int, stats_form.birthday.raw_data[0].split('-')))

            new_birthday = datetime.date(birth_day[0], birth_day[1], birth_day[2])

            # update the profile in the db
            db.update('profile', ['birthday', 'height', 'weight', 'show_age', 'show_height', 'show_weight'],
                      [new_birthday, float(stats_form.height.raw_data[0]), float(stats_form.weight.raw_data[0]),
                       bool(stats_form.show_age.raw_data), bool(stats_form.show_height.raw_data),
                       bool(stats_form.show_weight.raw_data)], ['user_id'], [current_user.user_id])
            return redirect(url_for('view_profile'))
        print(stats_form.errors)
    return render_template('user_settings.html', pass_form=password_form, email_form=email_form, stats_form=stats_form,
                           range_list=weight_list, height_list=height_list, tab_num=tab_num)


@application.route('/validate/<token>', methods=['GET', 'POST'])
def confirm_email(token):
    try:
        email = ts.loads(token, salt="email-confirm-key", max_age=86400)
    except:
        abort(404)

    # set "confirmed" to true then return
    user = db.select('users', ['ALL'], ['email'], [email])
    db.update('users', ['confirm_email'], [True], ['user_id'], [user['user_id']])

    flash('Your email has been confirmed!', 'alert-success')
    return redirect(url_for('new_signup'))


@application.route('/logout')
@login_required
def logout():
    log.info('Logging out user id:%s' % current_user.user_id)
    logout_user()
    return redirect(url_for('new_signup'))


@application.route('/get_a_workout', methods=['POST'])
@login_required
def get_a_workout():
    workout_id = request.form.get('workout_id')
    result = db.get_workouts_by_id(current_user.user_id, workout_id)
    js = json.dumps(result)
    return Response(js, status=200, mimetype='application/json')


@application.route('/get_all_workouts', methods=['GET'])
@login_required
def get_all_workouts():
    workouts = db.get_aggregate_workouts_by_id(current_user.user_id)
    return Response(json.dumps(workouts), status=200, mimetype='application/json')


@application.route('/edit_workout', methods=['POST'])
@login_required
def edit_workout():
    util_basic.edit_erg_workout(request, db)
    return Response(json.dumps({}), status=201, mimetype='application/json')


@application.route('/generate_graph_data', methods=['POST'])
@login_required
def generate_graph_data():
    if request.method == 'POST':
        workout_name = request.form.get('share')

        if workout_name:
            results = db.get_aggregate_workouts_by_name(current_user.user_id, workout_name)

            if results and len(results) > 0:
                js = build_graph_data(results, workout_name)

                return Response(js, status=200, mimetype='application/json')

    return Response({}, status=400, mimetype='application/json')


@application.route('/get_workout_names', methods=['GET'])
@login_required
def get_workout_names():
    workout_names = db.find_all_workout_names(current_user.user_id)
    js = json.dumps(workout_names)
    return Response(js, status=200, mimetype='application/json')


@application.route('/delete_workout', methods=['POST'])
@login_required
def delete_workout():
    workout_id = request.form.get('workout_id')
    db.delete_entry('workout', 'workout_id', workout_id)
    return Response(json.dumps({}), 201, mimetype='application/json')


@application.route('/get_all_athletes', methods=['GET'])
@login_required
def get_all_athletes():
    users = db.select('users', ['ALL'], fetchone=False)
    js = json.dumps(users)
    return Response(js, status=200, mimetype='application/json')


@application.route('/generate_individual_heatmap', methods=['GET'])
@login_required
def generate_individual_heatmap():
    heatmap = db.get_heat_map_calendar_results(current_user.user_id)
    js = json.dumps(heatmap)
    print(heatmap)
    print(js)
    return Response(js, status=200, mimetype='application/json')


@application.route('/get_past_three_workouts', methods=['GET'])
@login_required
def get_past_three_workouts():
    last_three = db.get_last_three_workouts(current_user.user_id)
    js = json.dumps(last_three)
    return Response(js, status=200, mimetype='application/json')


@application.route('/roster', methods=['GET', 'POST'])
@login_required
def roster():
    # if current_user.role != Role.CAPTAIN or Role.ADMIN:
    #     flash('No bueno...', 'alert-warning')
    #     return redirect(url_for('profile'))

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return render_template('roster.html')
        else:
            file = request.files['file']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and validate_filename(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(application.config['CSV_UPLOAD_FOLDER'], filename))
            return redirect(url_for('csv_upload',
                                    filename=filename))

    return render_template('roster.html')


@application.route('/csv_upload', methods=['GET', 'POST'])
@login_required
def csv_upload():
    filename = request.args.get('filename')
    path = os.path.join(application.config['CSV_UPLOAD_FOLDER'], filename)
    csv_to_db(path)
    return redirect(url_for('roster',
                            success=True))
    pass


@application.route('/save_img', methods=['POST'])
@login_required
def save_img():
    img = request.form.get('img')

    if img:
        pic_location = util_basic.upload_profile_image(img, current_user.user_id, current_user.picture)

        # update current user
        current_user.picture = pic_location

        # update the database
        db.update('profile', ['picture'], [pic_location], ['user_id'], [current_user.user_id])

        # sign certificate
        signed_url = sign_certificate(pic_location)

        return Response(json.dumps({'img_url': signed_url}), status=201, mimetype='application/json')

    return Response(json.dumps({}), status=400, mimetype='application/json')


@application.route('/save_erg_image', methods=['POST'])
@login_required
def save_erg_image():
    img = request.form.get('img')

    if img:
        log.info("Have new erg image")
        #picture_location = util_basic.upload_erg_image(img, current_user.user_id)
        img = img.split(',')[1]

        print(len(img))
        #nparr = np.fromstring(img, np.uint8)
        #img_np = cv2.imdecode(data, cv2.IMREAD_ANYDEPTH)
        #thread = threading.Thread(target=save_contour, args=(self.contours[cnt_idx], self.width, self.height, im_save_path))
        #thread.start()
        # update current user
        #current_user.picture = pic_location

        # update the database
        #db.update('profile', ['picture'], [pic_location], ['user_id'], [current_user.user_id])

        # sign certificate
        #signed_url = sign_certificate(pic_location)

        return Response(json.dumps({'data': 'hello_world'}), status=201, mimetype='application/json')

    return Response(json.dumps({}), status=400, mimetype='application/json')


@application.route('/drivers', methods=['POST'])
@login_required
def drivers():
    athletes = request.form.getlist('athletes[]')
    drivers = request.form.getlist('drivers[]')

    if drivers is [] or athletes is []:
        flash('Not enough drivers for selected athletes', 'alert-warning')
        return redirect(url_for('roster'))

    init_cars = generate_cars(athletes, drivers)
    if init_cars is None:
        flash('Not enough drivers for selected athletes', 'alert-warning')
        return redirect(url_for('roster'))

    drivers_arr, athlete_dict = init_cars

    assigned_cars = modified_k_means(drivers_arr, athlete_dict)
    return Response(json.dumps({'cars': assigned_cars}), status=201, mimetype='application/json')


@application.route('/cars', methods=['GET'])
@login_required
def cars():
    assigned_cars = json.loads(request.args.get('cars'))['cars']
    full_car_info = []
    for driver_id in list(assigned_cars.keys()):
        car_info = {}
        result = db.select('users', ['first', 'last', 'phone'], ['user_id'], [driver_id], fetchone=True)
        driver = result
        car_info['driver'] = driver
        athletes = []
        car_string = ''
        for athlete in assigned_cars[driver_id]['athletes']:
            curr_athlete = athlete[0]
            result = db.select('users', ['first', 'last', 'address', 'city', 'state', 'phone'], ['user_id'],
                               [curr_athlete],
                               fetchone=True)
            athletes.append(result)
            car_string += (
                '{} {}: {}, {} - {}\n'.format(result['first'],
                                              result['last'],
                                              result['address'],
                                              result['city'],
                                              result['phone']))

        car_info['athletes'] = athletes
        twilio_client.messages.create(
            to="+1{}".format(driver['phone']),
            from_=twilio_number,
            body="Hi {}, your car tomorrow is: {}".format(driver['first'], car_string))
        full_car_info.append(car_info)

    return render_template('cars.html', car_info=full_car_info)


def validate_filename(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@application.route('/no_login')
def no_login():
    return 'no login required'


if __name__ == '__main__':
    log.info('Begin Main')
    application.run()
