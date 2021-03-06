import os
from urllib.parse import quote

from geopy.exc import GeocoderServiceError
from geopy.geocoders import Nominatim
from werkzeug.utils import secure_filename

from User.roles import Role
from Utils import hashes
from Utils.config import db
from Utils.log import log


class User:

    def __init__(self, user_id, active=True):

        result = db.get_user(user_id)

        # if user is not found, a session for an anonymous user will be created
        if not result:
            raise ValueError('Could Not Find User')

        self.first = result['first']
        self.last = result['last']
        self.username = result['username']
        self.x = result['x']
        self.y = result['y']
        self.address = result['address']
        self.city = result['city']
        self.state = result['state']
        self.zip = result['zip']
        self.num_seats = result['num_seats']
        self.team = result['team']
        self.phone = result['phone']
        self.picture = result['picture']
        self.email = result['email']
        self.role = Role(result['role'])
        self.bio = result['bio']

        self.user_id = user_id
        self.active = active
        self.is_anonymous = False
        self.is_authenticated = True

        if not self.x and self.address:
            self.init_coordinates()

    def init_coordinates(self):
        geolocator = Nominatim(scheme='http')
        address = ' '.join([self.address, self.city, self.state, str(self.zip)])
        log.info(quote(address))
        query = {
            'street': self.address,
            'city': self.city,
            'state': self.state,
            'postalcode': str(self.zip)
        }
        try:
            location = geolocator.geocode(query)
        except GeocoderServiceError as e:
            log.error(e)
            log.error('Address {},{},{},{} could not be found using geopy.'.format(self.address, self.city, self.state,
                                                                                   self.zip))
            location = None
        if location:
            self.x = location.latitude
            self.y = location.longitude
            db.update('users', update_cols=['x', 'y'], update_params=[self.x, self.y],
                      where_cols=['user_id'], where_params=[self.user_id])
        else:
            log.error("Address {} {}, {} {} could not be located".format(self.address, self.city, self.state, self.zip))

    @classmethod
    def user_from_form(cls, form_data, active=True):

        form_data['password'] = hashes.hash_password(form_data['password'])

        wanted_attrs = ['first', 'last', 'username', 'password', 'email']
        attr_dict = {x: str(form_data[x]) for x in wanted_attrs}

        col_names = attr_dict.keys()
        col_vals = attr_dict.values()
        user_id = db.insert('users', col_names, col_vals, 'user_id')

        bio_string = 'Hi, my name is %s!' % form_data['first']
        db.insert('profile', ['bio', 'user_id'], [bio_string, user_id], 'user_id')

        return cls(user_id, active)

    @classmethod
    def user_from_csv_row(cls, csv_data, active=True):
        csv_data = {k: v for k, v in csv_data.items() if v is not None}
        col_names = list(csv_data.keys())
        col_values = list(csv_data.values())

        username_select = db.select(table_name='users', select_cols=['user_id'], where_cols=['username'],
                                    where_params=[csv_data['username']])
        if username_select is not None:
            user_id = username_select['user_id']
            db.update('users', col_names, col_values, where_cols=['user_id'], where_params=[user_id], operators=['='])
            log.info('Updated {}'.format(user_id))
        else:
            user_id = db.insert('users', col_names, col_values, 'user_id')
            bio_string = 'Hi, my name is %s!' % csv_data['first']
            db.insert('profile', ['bio', 'user_id'], [bio_string, user_id], 'user_id')
            log.info('Inserted new user {}'.format(user_id))

    def __repr__(self):
        return '<User %s>' % self.username

    def is_authenticated(self):
        return self.is_authenticated

    def is_active(self):
        return self.active

    def is_anonymous(self):
        return self.is_anonymous

    def get_id(self):
        return str(self.user_id)

    def is_profile_complete(self):
        """
        make sure user has completed fields Athlessary needs to function
        :return: boolean; True if all important fields are not null, False otherwise
        """

        if self.address is None:
            return False
        if self.team is None:
            return False
        return True

    @DeprecationWarning
    def change_profile_picture(self, form):
        """
        takes form data and the current user
        :param form: data from the flask photo form
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
        db.update('users', ['picture'], [pic_location], ['user_id'], [self.user_id])

        # return location to update the current user
        return pic_location
