class User:

    def __init__(self, user_id, cur, active=True):
        sql = '''
              SELECT *
              FROM users
              WHERE id = ?
              '''

        params = (user_id,)
        cur.execute(sql, params)
        result = cur.fetchone()

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