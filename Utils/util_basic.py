import os

from werkzeug.utils import secure_filename


def save_photo(db, form, current_user):
    """
    takes form data and the current user
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
    if current_user.picture != 'images/defaults/profile.jpg':
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
