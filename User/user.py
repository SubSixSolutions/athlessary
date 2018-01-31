from Utils import hashes
from Utils.db import Database


class User:

    db = Database("athlessary-database.db")

    def __init__(self, user_id, active=True):

        result = self.db.select('users', ['ALL'], ['id'], [user_id])

        # TODO what if the user id does not exist??

        self.first = result['first']
        self.last = result['last']
        self.username = result['username']
        self.password = result['password']
        self.picture = result['picture']
        self.address = result['address']
        self.has_car = result['has_car']
        self.num_seats = result['num_seats']
        self.user_id = user_id
        self.active = active

    @classmethod
    def user_from_form(cls, form_data, active=True):

        first = form_data['first']
        last = form_data['last']
        username = form_data['username']
        password = hashes.hash_password(form_data['password'])
        address = form_data['address']
        has_car = form_data['has_car']
        num_seats = form_data['num_seats']

        wanted_attrs = ['first', 'last', 'username', 'password', 'address', 'has_car', 'num_seats']
        attr_dict = {x: form_data[x] for x in wanted_attrs}

        col_names = attr_dict.keys()
        col_vals = attr_dict.values()

        user_id = cls.db.insert('users', col_names, col_vals)

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