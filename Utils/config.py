import os

from Utils.db import Database

TESTING = bool(os.environ.get('TESTING'))

db = Database(TESTING)
