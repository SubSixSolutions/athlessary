import base64
import datetime
import json
import os
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import boto3
import xml.etree.ElementTree as ET
import numpy as np
import requests

from Forms import web_forms
from Utils.log import log

from Utils.config import db
from Utils.config import password_recovery_email, password_recovery_email_creds


# get s3 bucket name
try:
    bucket_name = os.environ['S3_BUCKET']
    log.info('bucket {} found from environment'.format(bucket_name))
except KeyError:
    try:
        from Utils.secret_config import bucket_name
        log.info('bucket {} found from config file'.format(bucket_name))
    except ModuleNotFoundError:
        sys.stderr.write('Could Not Establish Bucket Connection')
        sys.exit(1)


def create_workout(user_id, db, meters, minutes, seconds, by_distance):
    # TODO should this be a part of user??

    # get time stamp without seconds
    date_stamp = datetime.datetime.utcnow()
    stamp = "{}-{}-{} {}:{}:{}".format(date_stamp.year, date_stamp.month, date_stamp.day, date_stamp.hour,
                                           date_stamp.minute, date_stamp.second)
    # stamp = '0000-00-00 00:00:00'
    print(stamp)
    # utc_date_stamp = time.time() // 1

    # name the piece
    name = str(len(meters)) + 'x'
    if by_distance:
        name += str(meters[0]) + 'm'
    else:
        if int(minutes[0]) > 0:
            name += str(minutes[0]) + '\''
        else:
            name += str(seconds[0]) + '\"'

    # create workout
    workout_id = db.insert('workout', ['user_id', 'time', 'by_distance', 'name'],
                           [user_id, stamp, by_distance, name], 'workout_id')

    # create erg workout
    for meter, minute, second in zip(meters, minutes, seconds):
        print(meter, minute, second)
        db.insert('erg', ['workout_id', 'distance', 'minutes', 'seconds'], [workout_id, meter, minute, second], 'erg_id')

    return name


def build_graph_data(results, workout_name):
    data_arr = []
    label_arr = []
    _ids = []

    y_axis = ''

    for res in results:
        if res['by_distance'] == 0:
            data_arr.append(float(res['distance']))
            y_axis = 'Meters'
        else:
            data_arr.append(float(res['total_seconds'])/float(60))
            y_axis = 'Minutes'
        label_arr.append(res['time'].strftime('%m-%d-%y'))
        _ids.append(res['workout_id'])

    data = {
        'data': data_arr,
        'labels': label_arr,
        'name': workout_name,
        'y_axis': y_axis,
        '_ids': _ids
    }
    js = json.dumps(data)

    return js


def edit_erg_workout(request, db):
    by_distance = int(request.form.get('by_distance'))
    erg_ids = request.form.getlist('erg_ids[]')

    if by_distance == 1:
        meters = request.form.getlist('meters[]')
        for i in range(len(erg_ids)):
            db.update('erg', ['distance'], [int(meters[i])], ['erg_id'], [int(erg_ids[i])])
    else:
        minutes = request.form.getlist('minutes[]')
        seconds = request.form.getlist('seconds[]')

        for i in range(len(erg_ids)):
            db.update('erg', ['minutes', 'seconds'], [int(minutes[i]), float(seconds[i])], ['erg_id'], [erg_ids[i]])

    workout_id = request.form.get('workout_id')
    if workout_id:
        new_date = request.form.get('new_date') + ":00"
        print(new_date)
        db.update('workout', ['time'], [new_date], ['workout_id'], [workout_id])


def set_up_profile_form(user, profile):
    """
    set up the profile form object
    :param user: the current user
    :param profile: the profile for the current user
    :return: a form object that has been set with the proper defaults
    """

    form_obj = web_forms.ProfileForm()

    if form_obj.team:
        form_obj.team.default = user.team
        form_obj.process()
    if user.address:
        form_obj.address.data = user.address
    if user.state:
        form_obj.state.data = user.state
    if user.city:
        form_obj.city.data = user.city
    if user.zip:
        form_obj.zip.data = user.zip
    if user.phone:
        form_obj.phone.data = user.phone

    form_obj.num_seats.data = user.num_seats
    form_obj.bio.data = profile['bio']

    return form_obj


def set_up_stats_form(user_id, form):

    user_profile = db.get_user(user_id)

    if user_profile['birthday']:
        form.birthday.data = user_profile['birthday']
    if user_profile['height'] != 0:
        form.height.data = user_profile['height']
    if user_profile['weight'] != 0:
        form.weight.data = user_profile['weight']

    if user_profile['show_age']:
        form.show_age.data = True
    if user_profile['show_height']:
        form.show_height.data = True
    if user_profile['show_weight']:
        form.show_weight.data = True

    return form


def upload_profile_image(img, user_id, pic_location):
    """
    save a new profile picture uploaded by the user
    :param img: byte string from web
    :param user_id: id fo the current user
    :param pic_location: the location of the current user profile picture
    :return:
    """

    img = img.split(',')[1]

    data = img.encode()
    data = base64.b64decode(data)

    # create new picture location
    mseconds = datetime.datetime.now().microsecond
    new_location = 'users/{0}/profile-{1}.png'.format(user_id, mseconds)

    # open s3 client
    client = boto3.client('s3')

    # delete old image
    if 'default' not in pic_location:
        client = boto3.client('s3')
        client.delete_object(
            Bucket=bucket_name,
            Key=pic_location
        )

    # save new image
    client.put_object(Body=data, Bucket=bucket_name, Key=new_location)

    return new_location


def upload_erg_image(img, user_id):
    """
    save the erg screen image from the user
    :param img: byte string from web
    :param user_id: id fo the current user
    :return:
    """

    img = img.split(',')[1]

    data = img.encode()
    data = base64.b64decode(data)

    # create new picture location
    mseconds = datetime.datetime.now().microsecond
    new_location = 'users/{}/erg_pics/{}.png'.format(user_id, mseconds)

    # open s3 client
    client = boto3.client('s3')
    # save new image
    client.put_object(Body=data, Bucket=bucket_name, Key=new_location)

    return new_location


def get_last_sunday(curr_date):
    last_sunday = curr_date - datetime.timedelta(curr_date.isoweekday())
    last_sunday_stamp = datetime.datetime(last_sunday.year, last_sunday.month, last_sunday.day, 23, 59, 59)
    return last_sunday_stamp


def format_leader_arr(arr, key_name, username):
    """

    :param arr:
    :param key_name:
    :param username:
    :return:
    """

    ret_val = []
    found_user = False
    count = 0

    for user in arr:
        if count < 5:
            ret_val.append(user)
            count += 1
        elif count < 6 and found_user:
            ret_val.append(user)
            count += 1
        if user['username'] == username:
            found_user = True
        if count > 5:
            break

    if not found_user:
        ret_val.append({'username': username, key_name: 0})

    while len(ret_val) < 6:
        ret_val.append({'username': 'Unclaimed', key_name: 0})

    return ret_val


def generate_leader_board(username):
    """

    :param username:
    :return:
    """

    last_sunday = get_last_sunday(datetime.datetime.utcnow())

    agg_meters = db.get_leader_board_meters(last_sunday)
    meters = format_leader_arr(agg_meters, 'total_meters', username)

    agg_minutes = db.get_leader_board_minutes(last_sunday)
    minutes = format_leader_arr(agg_minutes, 'total_seconds', username)

    agg_split = db.get_leader_board_split(last_sunday)
    split = format_leader_arr(agg_split, 'split', username)

    return meters, minutes, split


def send_email(email_address, html, subject):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = password_recovery_email
    msg['To'] = email_address
    body = MIMEText(html, 'html')
    msg.attach(body)
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(password_recovery_email, password_recovery_email_creds)
    problems = server.sendmail(password_recovery_email, email_address, msg.as_string())
    server.quit()


def lookup_user_address(line_1, line_2, city, state, zip_code):
    """

    :param line_1:
    :param line_2:
    :param city:
    :param state:
    :param zip_code:
    :return:
    """

    from Utils.config import USPS_API_user_name as API_key

    url = 'http://production.shippingapis.com/ShippingAPI.dll'

    xml_string = '''<AddressValidateRequest USERID="{}">
                    <Address>
                        <Address1>{}</Address1> 
                        <Address2>{}</Address2> 
                        <City>{}</City> 
                        <State>{}</State> 
                        <Zip5>{}</Zip5> 
                        <Zip4></Zip4> 
                    </Address> 
                
                </AddressValidateRequest>'''.format(API_key, line_1, line_2, city, state, zip_code)

    query_params = {'API': 'Verify', 'XML': xml_string}

    response = requests.get(url, params=query_params)

    return response


def verify_user_address(line_1, line_2, city, state, zip_code):
    address = lookup_user_address(line_1, line_2, city, state, zip_code)

    if not address or address.status_code != 200:
        return {'error': 'The server is not responding! Please try updating your profile again later.'}

    root = ET.fromstring(address.text)

    address_parse = root.findall('Address')

    if len(address_parse) != 1:
        return {'error': 'The server is not responding! Please try updating your profile again later.'}

    error = address_parse[0].findall('Error')

    if len(error) > 0:
        for err in error[0].findall('Description'):
            print(err.text)

        return {'error': 'Your address could not be found! Please check your spelling.'}

    ret_val = {
        'address': address_parse[0].findtext('Address2'),
        'zip': address_parse[0].findtext('Zip5'),
        # 'state': address_parse[0].findtext('State'),
        'state': state,  # trust state given from frontend TODO: look into changing this
        'city': address_parse[0].findtext('City'),
        'msg': address_parse[0].findtext('ReturnText')
    }

    return ret_val
