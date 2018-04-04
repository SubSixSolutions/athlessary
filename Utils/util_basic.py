import base64
import datetime
import json
import os
import time

from Forms import web_forms


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
                           [user_id, utc_date_stamp, by_distance, name])

    # create erg workout
    for meter, minute, second in zip(meters, minutes, seconds):
        db.insert('erg', ['workout_id', 'distance', 'minutes', 'seconds'], [workout_id, meter, minute, second])

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


def upload_profile_image(img, user_id):
    """
    save a new profile picture uploaded by the user
    :param img: byte string from web
    :param user_id: id fo the current user
    :return:
    """

    img = img.split(',')[1]

    data = img.encode()
    data = base64.b64decode(data)

    # specify the directory
    directory = os.getcwd() + '/static/images/%s' % user_id

    # create directory if it does not exist
    if not os.path.exists(directory):
        os.makedirs(directory)

    imgFile = open(directory + '/profile.png', 'wb')
    imgFile.write(data)

    # update current user
    pic_location = 'images/%s/%s' % (user_id, 'profile.png')

    return pic_location
