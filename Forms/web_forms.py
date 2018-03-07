from flask_uploads import UploadSet, IMAGES
from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed
from wtforms import StringField, PasswordField, validators, IntegerField, SelectField, BooleanField, TextAreaField
from wtforms import SubmitField, FileField
from wtforms.fields.html5 import TelField
from wtforms.validators import InputRequired, Length

photos = UploadSet('photos', IMAGES)


class SignInForm(FlaskForm):
    username_field = StringField('username')
    password_field = PasswordField('Password')
    submit_bttn = SubmitField('Sign In')


class SignUpForm(FlaskForm):
    username = StringField('username', validators=[Length(min=1, max=25, message="must be less than 25 chars"), InputRequired("must not be empty")])
    password = PasswordField('New Password', [
        validators.InputRequired(),
        validators.EqualTo('retype_pass', message='Passwords must match')
    ])
    retype_pass = PasswordField('retype password')
    # address = StringField('address', validators=[validators.InputRequired()])
    first = StringField('First Name', validators=[validators.InputRequired()])
    last = StringField('last name', validators=[validators.InputRequired()])
    # has_car = BooleanField('do you have a car?', validators=[validators.InputRequired()])
    # num_seats = IntegerField('num seats', validators=[validators.InputRequired()])
    submit = SubmitField(u'Create Account')


class PhotoForm(FlaskForm):
    photo = FileField('Update Your Profile Pic', validators=[FileAllowed(photos, u'Image only!'), FileRequired(u'File was empty!')])
    submit = SubmitField(u'Upload')


class ProfileForm(FlaskForm):
    bio = TextAreaField('bio', validators=[Length(max=250), validators.InputRequired()])
    address = StringField('address', validators=[validators.InputRequired()])
    city = StringField('city', validators=[validators.InputRequired()])
    state = StringField('state', validators=[validators.InputRequired()])
    zip = IntegerField('zip code', validators=[validators.InputRequired()])
    phone = TelField('phone', validators=[validators.InputRequired()])
    choices_arr = ['Varsity Men', 'Varsity Women']
    team = SelectField('team', choices=[('vm', 'Varsity Men'), ('vw', 'Varsity Women'), ('nm', 'Novice Men'),
                                        ('nw', 'Novice Women'), ('cox', 'Coxswain')])
    choices_arr = [(i, str(i)) for i in range(9)]
    num_seats = SelectField('num_seats', choices=choices_arr)
    can_drive = BooleanField('has_car', validators=[validators.InputRequired()])
    submit = SubmitField(u'Update')


