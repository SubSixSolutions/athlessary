import os
import sys

from Utils.db import Database
from Utils.log import log

TESTING = bool(os.environ.get('TESTING'))

db = Database(TESTING)

try:
    twilio_sid = os.environ['TWILIO_SID']
    twilio_auth_token = os.environ['TWILIO_AUTH_TOKEN']
    twilio_number = os.environ['TWILIO_NUMBER']
except KeyError:
    try:
        from Utils.secret_config import twilio_sid, twilio_auth_token, twilio_number

    except ModuleNotFoundError:
        log.error('Could Not Find Twilio Credentials')
        sys.exit(1)

try:
    DB_INIT = os.environ['REQ_DB_INIT']
except KeyError:
    DB_INIT = False

log.info('DB_INIT: {}\nTESTING: {}\n')
