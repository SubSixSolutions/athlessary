import base64
import datetime
import json
import os
import sys

import boto3

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


def create_workout(user_id, db, meters, minutes, seconds, by_distance):
    # TODO should this be a part of user??

    # get time stamp without seconds
    date_stamp = datetime.datetime.utcnow()
    stamp = "{}-{}-{} {}:{}:{}".format(date_stamp.year, date_stamp.month, date_stamp.day, date_stamp.hour,
                                           date_stamp.minute, date_stamp.second)
    # stamp = '0000-00-00 00:00:00'
    print(stamp)
    # utc_date_stamp = time.time() // 1

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
                           [user_id, stamp, by_distance, name], 'workout_id')

    # create erg workout
    for meter, minute, second in zip(meters, minutes, seconds):
        print(meter, minute, second)
        db.insert('erg', ['workout_id', 'distance', 'minutes', 'seconds'], [workout_id, meter, minute, second], 'erg_id')

    return name


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
        label_arr.append(res['time'].strftime('%Y-%m-%d %H:%M'))
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

    workout_id = request.form.get('workout_id')
    if workout_id:
        new_date = request.form.get('new_date') + ":00"
        print(new_date)
        db.update('workout', ['time'], [new_date], ['workout_id'], [workout_id])


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
