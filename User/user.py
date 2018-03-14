import os

from werkzeug.utils import secure_filename

from Utils import hashes
from Utils.db import Database


class User:

    db = Database("athlessary-database.db")

    def __init__(self, user_id, active=True):

        # result = self.db.get_user(user_id)
        result = self.db.select('users', ['ALL'], ['user_id'], [user_id])

        # TODO what if the user id does not exist??

        self.first = result['first']
        self.last = result['last']
        self.username = result['username']
        # self.password = result['password']
        # self.picture = result['picture']
        self.address = result['address']
        self.city = result['city']
        self.state = result['state']
        self.zip = result['zip']
        self.num_seats = result['num_seats']
        self.team = result['team']
        self.phone = result['phone']
        self.user_id = user_id
        self.active = active

    @classmethod
    def user_from_form(cls, form_data, active=True):

        form_data['password'] = hashes.hash_password(form_data['password'])

        print(form_data['password'])

        # wanted_attrs = ['first', 'last', 'username', 'password', 'address', 'has_car', 'num_seats']
        wanted_attrs = ['first', 'last', 'username', 'password']
        attr_dict = {x: str(form_data[x]) for x in wanted_attrs}

        col_names = attr_dict.keys()
        col_vals = attr_dict.values()

        user_id = cls.db.insert('users', col_names, col_vals)

        bio_string = 'Hi, my name is %s!' % form_data['first']
        cls.db.insert('profile', ['bio', 'user_id'], [bio_string, user_id])

        return cls(user_id, None)

    def __repr__(self):
        return '<User %s>' % self.username

    def is_authenticated(self):
        return True

    def is_active(self):
        return self.active

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.user_id)

    def change_profile_picture(self, form):
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
        directory = os.getcwd() + '/static/images/%s' % self.user_id

        # create directory if it does not exist
        if not os.path.exists(directory):
            os.makedirs(directory)

        # delete old file
        if self.picture != 'images/defaults/profile_square.jpg':
            try:
                os.remove(os.getcwd() + '/static/' + self.picture)
            except OSError:
                pass

        # save image out to disk
        f.save(os.path.join(directory, filename))

        # update current user
        pic_location = 'images/%s/%s' % (self.user_id, filename)
        self.picture = pic_location

        # update the database
        self.db.update('users', ['picture'], [pic_location], ['user_id'], [self.user_id])

        # return location to update the current user
        return pic_location
