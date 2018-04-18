import os

from Utils.db import Database

TESTING = bool(os.environ.get('TESTING'))
DB_INIT = bool(os.environ.get('REQ_DB_INIT'))

db = Database(TESTING)