import re

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, validators, IntegerField, SelectField, BooleanField, TextAreaField
from wtforms import SubmitField, ValidationError
from wtforms.fields.html5 import TelField
from wtforms.validators import InputRequired, Length

from Utils.config import db


class SignInForm(FlaskForm):
    username_field = StringField('username', validators=[validators.InputRequired()])
    password_field = PasswordField('Password', validators=[validators.InputRequired()])
    submit_bttn = SubmitField('Sign In')


def password_contains_number(form, field):
    regex = re.compile('.*[0-9].*')
    if not regex.match(field.data):
        raise ValidationError(u'Password must contain at least one number.')


def username_start_with_letter(form, field):
    p = re.compile('[a-zA-Z].')
    if not p.match(field.data):
        raise ValidationError('Username must begin with a letter.')


def unique_user_name(form, field):
    names = db.get_names()
    if names and field.data in names:
        raise ValidationError('Username \'%s\' is taken!' % field.data)


def can_drive_check(form, field):
    if int(form.num_seats.data) > 0:
        if not field.data:
            raise ValidationError('This field is required.')


def make_selection(form, field):
    if field.data == 'blank':
        raise ValidationError('Please make a selection.')


class ChangePasswordForm(FlaskForm):
    new_pass = PasswordField('New Password', [
        validators.InputRequired(),
        validators.EqualTo('retype_new_pass', message='Passwords must match.'),
        Length(min=5, max=25, message='Password must be between 5 and 25 characters long.'),
        password_contains_number
    ])
    retype_new_pass = PasswordField('retype password',
            validators=[InputRequired(),
                        Length(min=5, max=25, message='Password must be between 5 and 25 characters long.'),
                        password_contains_number])
    submit = SubmitField(u'Change Password')


class SignUpForm(FlaskForm):
    username = StringField('username',
                           validators=[Length(min=1, max=25, message="Username must be less than 25 characters."),
                                       InputRequired(), username_start_with_letter, unique_user_name])
    password = PasswordField('New Password', [
        validators.InputRequired(),
        validators.EqualTo('retype_pass', message='Passwords must match.')
    ])
    retype_pass = PasswordField('retype password', validators=[InputRequired()])
    first = StringField('First Name', validators=[validators.InputRequired()])
    last = StringField('last name', validators=[validators.InputRequired()])
    submit = SubmitField(u'Create Account')


class ProfileForm(FlaskForm):
    state_options = [('blank', 'Choose a State'), ('Alaska', 'Alaska'), ('Alabama', 'Alabama'),
                     ('Arkansas', 'Arkansas'),
                     ('Arizona', 'Arizona'), ('California', 'California'),
                     ('Colorado', 'Colorado'), ('Connecticut', 'Connecticut'),
                     ('District of Columbia', 'District of Columbia'), ('Delaware', 'Delaware'), ('Florida', 'Florida'),
                     ('Georgia', 'Georgia'), ('Hawaii', 'Hawaii'), ('Iowa', 'Iowa'),
                     ('Idaho', 'Idaho'), ('Illinois', 'Illinois'), ('Indiana', 'Indiana'), ('Kansas', 'Kansas'),
                     ('Kentucky', 'Kentucky'), ('Louisiana', 'Louisiana'), ('Massachusetts', 'Massachusetts'),
                     ('Maryland', 'Maryland'), ('Maine', 'Maine'), ('Michigan', 'Michigan'), ('Minnesota', 'Minnesota'),
                     ('Missouri', 'Missouri'), ('Mississippi', 'Mississippi'), ('Montana', 'Montana'),
                     ('North Carolina', 'North Carolina'), ('North Dakota', 'North Dakota'), ('Nebraska', 'Nebraska'),
                     ('New Hampshire', 'New Hampshire'), ('New Jersey', 'New Jersey'), ('New Mexico', 'New Mexico'),
                     ('Nevada', 'Nevada'), ('New York', 'New York'), ('Ohio', 'Ohio'), ('Oklahoma', 'Oklahoma'),
                     ('Oregon', 'Oregon'), ('Pennsylvania', 'Pennsylvania'),
                     ('Rhode Island', 'Rhode Island'), ('South Carolina', 'South Carolina'),
                     ('South Dakota', 'South Dakota'), ('Tennessee', 'Tennessee'), ('Texas', 'Texas'), ('Utah', 'Utah'),
                     ('Virginia', 'Virginia'), ('Virgin Islands', 'Virgin Islands'), ('Vermont', 'Vermont'),
                     ('Washington', 'Washington'), ('Wisconsin', 'Wisconsin'), ('West Virginia', 'West Virginia'),
                     ('Wyoming', 'Wyoming')]

    seat_options = [(i, str(i)) for i in range(9)]

    teams = [('blank', 'Team Name'), ('vm', 'Varsity Men'), ('vw', 'Varsity Women'), ('nm', 'Novice Men'),
             ('nw', 'Novice Women'), ('cox', 'Coxswain')]

    bio = TextAreaField('bio', validators=[Length(min=5, max=250, message='Bio must be 5-250 characters long.'), validators.InputRequired()])

    address = StringField('address', validators=[validators.InputRequired()])
    city = StringField('city', validators=[validators.InputRequired()])
    state = SelectField('state', choices=state_options, validators=[make_selection])
    zip = IntegerField('zip code', validators=[validators.InputRequired()])
    phone = TelField('phone', validators=[validators.InputRequired(),
                                          Length(min=10, max=10, message='Must be 10 digit phone number.')])

    team = SelectField('team', choices=teams, validators=[make_selection])

    num_seats = SelectField('num_seats', coerce=int, choices=seat_options)
    can_drive = BooleanField('has_car', validators=[can_drive_check])

    submit = SubmitField(u'Update')
