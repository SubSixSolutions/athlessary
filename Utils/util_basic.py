import os
import time

from werkzeug.utils import secure_filename


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
    db.update('users', ['picture'], [pic_location], ['id'], [current_user.user_id])

    # return location to update the current user
    return pic_location


def create_workout(user_id, db, meters, minutes, seconds, by_distance):
    # TODO should this be a part of user??

    # get time stamp
    utc_date_stamp = time.time()

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
