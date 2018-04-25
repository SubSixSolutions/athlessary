import os, sys

from Utils.db import Database

TESTING = bool(os.environ.get('TESTING'))
DB_INIT = bool(os.environ.get('REQ_DB_INIT'))

db = Database(TESTING)

try:
    twilio_sid = os.environ['TWILIO_SID']
    twilio_auth_token = os.environ['TWILIO_AUTH_TOKEN']
    twilio_number = os.environ['TWILIO_NUMBER']

except KeyError:
    try:
        from Utils.secret_config import twilio_sid, twilio_auth_token, twilio_number

    except ModuleNotFoundError:
        sys.stderr.write('Could Not Find Twilio Credentials')
        sys.exit(1)
