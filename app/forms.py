from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    TextAreaField, FloatField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, \
    Length
from flask_babel import _, lazy_gettext as _l
from app.models import User


class LoginForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Sign In'))


class RegistrationForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('Repeat Password'), validators=[DataRequired(),
                                           EqualTo('password')])
    submit = SubmitField(_l('Register'))

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(_('Please use a different username.'))

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(_('Please use a different email address.'))


class ResetPasswordRequestForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Request Password Reset'))


class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('Repeat Password'), validators=[DataRequired(),
                                           EqualTo('password')])
    submit = SubmitField(_l('Request Password Reset'))


class EditProfileForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    about_me = TextAreaField(_l('About me'),
                             validators=[Length(min=0, max=140)])
    submit = SubmitField(_l('Submit'))

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError(_('Please use a different username.'))


class PostForm(FlaskForm):
    post = TextAreaField(_l('Say something'), validators=[DataRequired()])
    submit = SubmitField(_l('Submit'))

class PaymentForm(FlaskForm):
    payment = StringField(_l('enter the name of payment in here'), validators=[DataRequired()])
    logo = StringField(_l('paste the image link in here'), validators=[DataRequired()])
    submit = SubmitField(_l('Submit'))

class ShippingAddressesForm(FlaskForm):
    SAddress = StringField(_l('enter the address in here'), validators=[DataRequired()])
    submit = SubmitField(_l('Submit'))

class UserAddressForm(FlaskForm):
    UAddress = StringField(_l('enter the address in here'), validators=[DataRequired()])
    submit = SubmitField(_l('Submit'))

class ProductForm(FlaskForm):
    name = StringField(_l('Name'), validators=[DataRequired()])
    price = FloatField(_l('Price'), validators=[DataRequired()])
    description = StringField(_l('Description'), validators=[DataRequired()])
    #brand = StringField(_l('enter the brand of product in here'), validators=[DataRequired()])
    #cart = StringField(_l('enter the cart of product in here'), validators=[Data.Required()])
    #Productreviews = StringField(_l('enter the reviews of product in here'), validators=[DataRequired()])
    image = StringField(_l('Image URL'), validators=[DataRequired()])
    submit = SubmitField(_l('Submit'))

class CategoryForm(FlaskForm):
    name = StringField(_l('enter the name of category in here'), validators=[DataRequired()])
    brand = StringField(_l('enter the brand of category in here'), validators=[DataRequired()])
    submit = SubmitField(_l('Submit'))

class BrandForm(FlaskForm):
    #productForm = StringField(_l('enter the name of product in here'), validators=[DataRequired()])
    name = StringField(_l('enter the name of brand in here'), validators=[DataRequired()])
    submit = SubmitField(_l('Submit'))

class OrderdetailsForm(FlaskForm):
    order = StringField(_l('enter the order in here'), validators=[DataRequired()])
    submit = SubmitField(_l('Submit'))

class ProductreviewsForm(FlaskForm):
    review = StringField(_l('enter the review in here'), validators=[DataRequired()])
    rating = StringField(_l('enter the rating in here'), validators=[DataRequired()])
    submit = SubmitField(_l('Submit'))

class OrderstatusForm(FlaskForm):
    status = StringField(_l('enter the status in here'), validators=[DataRequired()])
    submit = SubmitField(_l('Submit'))