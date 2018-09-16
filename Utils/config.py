import os
import sys

from Utils.db import Database
from Utils.log import log

TESTING = bool(os.environ.get('TESTING'))

try:
    DB_INIT = os.environ['REQ_DB_INIT']
except KeyError:
    DB_INIT = False

log.info('DB_INIT: {}\nTESTING: {}\n'.format(DB_INIT, TESTING))

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
        log.error('Could Not Find Twilio Credentials')
        sys.exit(1)

try:
    password_recovery_email = os.environ['RECOVERY_EMAIL']
    password_recovery_email_creds = os.environ['RECOVERY_PASS']
    log.info(password_recovery_email)
    log.info(password_recovery_email_creds)
except KeyError:
    try:
        from Utils.secret_config import password_recovery_email, password_recovery_email_creds
    except ModuleNotFoundError:
        log.error('Could not find password recovery credentials')
        sys.exit(1)

try:
    USPS_API_user_name = os.environ['USPS_API_KEY']
except KeyError:
    try:
        from Utils.secret_config import USPS_API_user_name
    except ModuleNotFoundError:
        log.error('Could not find USPS API Key.')
        sys.exit(1)

