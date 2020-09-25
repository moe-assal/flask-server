from flask_wtf import FlaskForm
from wtforms.widgets import TextArea
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, AnyOf, ValidationError
from datetime import datetime

governorates_of_lebanon = ['Akkar', 'Baalbek-Hermel', 'Beirut', 'Beqaa', 'Mount Lebanon', 'Nabatieh', 'North', 'South']
districts = {
    'Akkar': [''],
    'Baalbek-Hermel': ['Baalbek', 'Hermel'],
    'Beirut': [''],
    'Beqaa': ['Rashaya', 'Western Beqaa', 'Zahle'],
    'Mount Lebanon': ['Aley', 'Baabda', 'Byblos', 'Chouf', 'Keserwan', 'Matn'],
    'Nabatieh': ['Bint Jbeil', 'Hasbaya', 'Marjeyoun', 'Nabatieh'],
    'North': ['Batroun', 'Bsharri', 'Koura', 'Miniyeh-Danniyeh District', 'Tripoli', 'Zgharta'],
    'South': ['Sidon', 'Jezzine', 'Tyre']
}


class Integer(object):
    def __init__(self, message=None):
        self.message = message
        if not self.message:
            self.message = "Input must be an Integer"

    def __call__(self, form, field):
        data = field.data
        try:
            int(data)
        except ValueError:
            raise ValidationError(self.message)


class SignupForm(FlaskForm):
    membership_id = StringField('Membership ID', validators=[DataRequired(), Length(min=0, max=10), Integer()])
    username = StringField('Username', validators=[DataRequired(), Length(min=10, max=30)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    gender = StringField('Gender', validators=[DataRequired(), AnyOf(['male', 'female'])])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])

    phone_number = StringField('', validators=[DataRequired(), Integer()])

    governorate = StringField('Governorate', validators=[DataRequired(), AnyOf(governorates_of_lebanon)])
    district = StringField('District')
    civil_registry_num = StringField('No. Civil Registry', validators=[DataRequired(), Integer()])
    national_identity_num = StringField('No. National Identity', validators=[DataRequired(), Length(min=0, max=12),
                                                                             Integer()])
    birth_date = StringField('Birth Date', validators=[DataRequired()])

    remember = BooleanField('remember me')
    submit = SubmitField('Sign Up')

    @staticmethod
    def validate_district(form, field):
        governorate = form.governorate.data
        if governorate in governorates_of_lebanon:
            message = "Districts Allowed for governorate " + governorate + " are " + \
                           ", ".join(districts[governorate]) + "."
            if governorate in ['Beirut', 'Akkar']:
                message = "Governorate " + governorate + " has no districts."
        else:
            return

        district = field.data
        if district is None:
            district = field.data = ''

        if district not in districts[governorate]:
            raise ValidationError(message)

    @staticmethod
    def validate_birth_date(form, field):
        message = 'Date format is YYYY-MM-DD'
        try:
            year, month, day = field.data.split('-')
            year, month, day = int(year), int(month), int(day)
            date = datetime(year=year, month=month, day=day, hour=12, minute=0, second=0, microsecond=0)
        except:
            raise ValidationError(message)

        field.data = date

    @staticmethod
    def validate_phone_number(form, field):
        message = 'Phone No. format is +country_code******'
        num = field.data
        if not num[0] == '+':
            raise ValidationError(message)

        message = "wrong lebanese number format"
        if num[0:4] == "+961":
            if num.__len__() != 12:
                raise ValidationError(message)

    @staticmethod
    def validate_username(form, field):
        message = "Username format is 'First-Name Middle-Name Last-Name'"
        if field.data.split(' ').__len__() < 3:
            raise ValidationError(message)


class LoginForm(FlaskForm):
    membership_id = StringField('Membership ID', validators=[DataRequired(), Length(min=5, max=5)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('remember me')
    submit = SubmitField('Log In')


class EditProfileForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    description = StringField('Description', validators=[DataRequired(), Length(min=5, max=500)], widget=TextArea())
    picture = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')


class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Reset Email')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')
