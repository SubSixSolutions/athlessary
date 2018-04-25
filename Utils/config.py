import os, sys

from Utils.db import Database
from Utils.log import log

TESTING = bool(os.environ.get('TESTING'))
DB_INIT = bool(os.environ.get('REQ_DB_INIT'))

db = Database(TESTING)

environ_twilio = True
try:
    twilio_sid = os.environ['TWILIO_SID']
    twilio_auth_token = os.environ['TWILIO_AUTH_TOKEN']
    twilio_number = os.environ['TWILIO_NUMBER']

except KeyError:
    environ_twilio = False
    try:
        from Utils.secret_config import twilio_sid, twilio_auth_token, twilio_number

    except ModuleNotFoundError:
        sys.stderr.write('Could Not Find Twilio Credentials')
        sys.exit(1)

log.info('TWILIO_ENVIRON: {}\nTESTING: {}\nDB_INIT: {}'.format(environ_twilio, TESTING, DB_INIT))