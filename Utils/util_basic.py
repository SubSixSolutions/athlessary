import base64
import datetime
import json
import os
import sys
import time

import boto3
from werkzeug.utils import secure_filename

from Forms import web_forms

# get s3 bucket name
try:
    bucket_name = os.environ['S3_BUCKET']
except KeyError:
    try:
        from Utils.secret_config import bucket_name
    except ModuleNotFoundError:
        sys.stderr.write('Could Not Establish Database Connection')
        sys.exit(1)


def save_photo(db, form, current_user):
    """
    takes form data and the current user
    :param db: data base object to connect to
    :param form: data from the flask photo form
    :param current_user: pointer to the current user
    :return:
    """
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
    if current_user.picture != 'images/defaults/profile_square.jpg':
        try:
            os.remove(os.getcwd() + '/static/' + current_user.picture)
        except OSError:
            pass

    # save image out to disk
    f.save(os.path.join(directory, filename))

    # update current user
    pic_location = 'images/%s/%s' % (current_user.user_id, filename)

    # update the database
    db.update('users', ['picture'], [pic_location], ['user_id'], [current_user.user_id])

    # return location to update the current user
    return pic_location


def create_workout(user_id, db, meters, minutes, seconds, by_distance):
    # TODO should this be a part of user??

    # get time stamp without seconds
    utc_date_stamp = time.time() // 1

    # name the piece
    name = str(len(meters)) + 'x'
    if by_distance:
        name += str(meters[0]) + 'm'
    else:
        if int(minutes[0]) > 0:
            name += str(minutes[0]) + '\''
        else:
            name += str(seconds[0]) + '\"'

    # create workout
    workout_id = db.insert('workout', ['user_id', 'time', 'by_distance', 'name'],
                           [user_id, utc_date_stamp, by_distance, name], 'workout_id')

    # create erg workout
    for meter, minute, second in zip(meters, minutes, seconds):
        db.insert('erg', ['workout_id', 'distance', 'minutes', 'seconds'], [workout_id, meter, minute, second], 'erg_id')


def build_graph_data(results, workout_name):
    data_arr = []
    label_arr = []
    _ids = []

    y_axis = ''

    for res in results:
        if res['by_distance'] == 0:
            data_arr.append(res['distance'])
            y_axis = 'Meters'
        else:
            data_arr.append(float(res['total_seconds'])/float(60))
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

    return js


def edit_time_stamp(new_date, new_time, old_stamp):
    """
    takes a new TIME, new DATE, and a time stamp
    :param new_date: date in format yyyy-mm-dd
    :param new_time: time in form hh:mm
    :param old_stamp: time stamp in seconds since epoch
    :return:
    """

    # convert old stamp into a date
    old_date = datetime.datetime.fromtimestamp(float(old_stamp))

    # break up date and time strings
    new_date_arr = new_date.split('-')
    new_time_arr = new_time.split(':')

    # create new date time object from strings
    new_date_obj = datetime.datetime(int(new_date_arr[0]), int(new_date_arr[1]), int(new_date_arr[2]), int(new_time_arr[0]), int(new_time_arr[1]), old_date.second)

    # format new time stamp
    new_stamp = time.mktime(new_date_obj.timetuple())

    return new_stamp


def edit_erg_workout(request, db):
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

    new_date = request.form.get('new_date')
    new_time = request.form.get('time')
    old_stamp = float(request.form.get('old_date'))

    new_stamp = edit_time_stamp(new_date, new_time, old_stamp)

    if old_stamp != new_stamp:
        workout_id = request.form.get('workout_id')
        db.update('workout', ['time'], [int(new_stamp)], ['workout_id'], [workout_id])


def set_up_profile_form(user, profile):
    """
    set up the profile form object
    :param user: the current user
    :param profile: the profile for the current user
    :return: a form object that has been set with the proper defaults
    """

    form_obj = web_forms.ProfileForm()

    if form_obj.team:
        form_obj.team.default = user.team
        form_obj.process()
    if user.address:
        form_obj.address.data = user.address
    if user.state:
        form_obj.state.data = user.state
    if user.city:
        form_obj.city.data = user.city
    if user.zip:
        form_obj.zip.data = user.zip
    if user.phone:
        form_obj.phone.data = user.phone

    form_obj.num_seats.data = user.num_seats
    form_obj.bio.data = profile['bio']

    return form_obj


def upload_profile_image(img, user_id, pic_location):
    """
    save a new profile picture uploaded by the user
    :param img: byte string from web
    :param user_id: id fo the current user
    :param pic_location: the location of the current user profile picture
    :return:
    """

    img = img.split(',')[1]

    data = img.encode()
    data = base64.b64decode(data)

    # create new picture location
    mseconds = datetime.datetime.now().microsecond
    new_location = 'users/{0}/profile-{1}.png'.format(user_id, mseconds)

    # open s3 client
    client = boto3.client('s3')

    # delete old image
    if 'default' not in pic_location:
        client = boto3.client('s3')
        client.delete_object(
            Bucket=bucket_name,
            Key=pic_location
        )

    # save new image
    client.put_object(Body=data, Bucket=bucket_name, Key=new_location)

    return new_location
