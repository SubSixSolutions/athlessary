import re

from flask_uploads import UploadSet, IMAGES
from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed
from wtforms import StringField, PasswordField, validators, IntegerField, SelectField, BooleanField, TextAreaField
from wtforms import SubmitField, FileField, ValidationError
from wtforms.fields.html5 import TelField
from wtforms.validators import InputRequired, Length

photos = UploadSet('photos', IMAGES)


class SignInForm(FlaskForm):
    username_field = StringField('username', validators=[validators.InputRequired()])
    password_field = PasswordField('Password', validators=[validators.InputRequired()])
    submit_bttn = SubmitField('Sign In')


def username_start_with_letter(form, field):
    p = re.compile('[a-zA-Z].')
    if not p.match(field.data):
        raise ValidationError('Username must begin with a letter.')


class SignUpForm(FlaskForm):
    username = StringField('username', validators=[Length(min=1, max=25, message="must be less than 25 chars"),
                                                   InputRequired(), username_start_with_letter])
    password = PasswordField('New Password', [
        validators.InputRequired(),
        validators.EqualTo('retype_pass', message='Passwords must match.')
    ])
    retype_pass = PasswordField('retype password', validators=[InputRequired()])
    first = StringField('First Name', validators=[validators.InputRequired()])
    last = StringField('last name', validators=[validators.InputRequired()])
    submit = SubmitField(u'Create Account')


class PhotoForm(FlaskForm):
    photo = FileField('Update Your Profile Pic', validators=[FileAllowed(photos, u'Image only!'), FileRequired(u'File was empty!')])
    submit = SubmitField(u'Upload')


def can_drive_check(form, field):
    if int(form.num_seats.data) > 0:
        if not field.data:
            raise ValidationError('This field is required.')


class ProfileForm(FlaskForm):
    bio = TextAreaField('bio', validators=[Length(min=1, max=250, message='hey!'), validators.InputRequired()])
    address = StringField('address', validators=[validators.InputRequired()])
    city = StringField('city', validators=[validators.InputRequired()])
    state_options = [('Alaska', 'Alaska'), ('Alabama', 'Alabama'), ('Arkansas', 'Arkansas'), ('American Samoa', 'American Samoa'), ('Arizona', 'Arizona'), ('California', 'California'), ('Colorado', 'Colorado'), ('Connecticut', 'Connecticut'), ('District of Columbia', 'District of Columbia'), ('Delaware', 'Delaware'), ('Florida', 'Florida'), ('Georgia', 'Georgia'), ('Guam', 'Guam'), ('Hawaii', 'Hawaii'), ('Iowa', 'Iowa'), ('Idaho', 'Idaho'), ('Illinois', 'Illinois'), ('Indiana', 'Indiana'), ('Kansas', 'Kansas'), ('Kentucky', 'Kentucky'), ('Louisiana', 'Louisiana'), ('Massachusetts', 'Massachusetts'), ('Maryland', 'Maryland'), ('Maine', 'Maine'), ('Michigan', 'Michigan'), ('Minnesota', 'Minnesota'), ('Missouri', 'Missouri'), ('Mississippi', 'Mississippi'), ('Montana', 'Montana'), ('North Carolina', 'North Carolina'), ('North Dakota', 'North Dakota'), ('Nebraska', 'Nebraska'), ('New Hampshire', 'New Hampshire'), ('New Jersey', 'New Jersey'), ('New Mexico', 'New Mexico'), ('Nevada', 'Nevada'), ('New York', 'New York'), ('Ohio', 'Ohio'), ('Oklahoma', 'Oklahoma'), ('Oregon', 'Oregon'), ('Pennsylvania', 'Pennsylvania'), ('Puerto Rico', 'Puerto Rico'), ('Rhode Island', 'Rhode Island'), ('South Carolina', 'South Carolina'), ('South Dakota', 'South Dakota'), ('Tennessee', 'Tennessee'), ('Texas', 'Texas'), ('Utah', 'Utah'), ('Virginia', 'Virginia'), ('Virgin Islands', 'Virgin Islands'), ('Vermont', 'Vermont'), ('Washington', 'Washington'), ('Wisconsin', 'Wisconsin'), ('West Virginia', 'West Virginia'), ('Wyoming', 'Wyoming')]
    state = SelectField('state', choices=state_options)
    # state = StringField('state', validators=[validators.InputRequired()])
    zip = IntegerField('zip code', validators=[validators.InputRequired()])
    phone = TelField('phone', validators=[validators.InputRequired()])
    choices_arr = ['Varsity Men', 'Varsity Women']
    team = SelectField('team', choices=[('blank', '...'), ('vm', 'Varsity Men'), ('vw', 'Varsity Women'), ('nm', 'Novice Men'),
                                        ('nw', 'Novice Women'), ('cox', 'Coxswain')])
    choices_arr = [(i, str(i)) for i in range(9)]
    print(choices_arr)
    num_seats = SelectField('num_seats', coerce=int, choices=choices_arr)
    can_drive = BooleanField('has_car', validators=[can_drive_check])
    submit = SubmitField(u'Update')


