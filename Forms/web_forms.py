from flask_uploads import UploadSet, IMAGES
from flask_wtf import FlaskForm
from flask_wtf.file import FileRequired, FileAllowed
from wtforms import BooleanField, StringField, PasswordField, validators
from wtforms import IntegerField, SubmitField, FileField
from wtforms.validators import InputRequired, Length

photos = UploadSet('photos', IMAGES)


class SignUpForm(FlaskForm):
    username = StringField('username', validators=[Length(min=1, max=25, message="must be less than 5 chars"), InputRequired("must not be empty")])
    password = PasswordField('New Password', [
        validators.InputRequired(),
        validators.EqualTo('retype_pass', message='Passwords must match')
    ])
    retype_pass = PasswordField('retype password')
    address = StringField('address', validators=[validators.InputRequired()])
    first = StringField('first name', validators=[validators.InputRequired()])
    last = StringField('last name', validators=[validators.InputRequired()])
    has_car = BooleanField('do you have a car?', validators=[validators.InputRequired()])
    num_seats = IntegerField('num seats', validators=[validators.InputRequired()])
    submit = SubmitField(u'Create Account')


class PhotoForm(FlaskForm):
    photo = FileField('Update Your Profile Pic', validators=[FileAllowed(photos, u'Image only!'), FileRequired(u'File was empty!')])
    submit = SubmitField(u'Upload')
