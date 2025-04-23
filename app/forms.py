from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    TextAreaField, IntegerField, SelectField, DecimalField, FileField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, \
    Length, NumberRange, Optional, URL
from flask_wtf.file import FileField, FileAllowed
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
    name = StringField('Product Name*', validators=[DataRequired()],render_kw={"placeholder": "Enter product name"})
    sku = StringField('SKU*', validators=[DataRequired()],render_kw={"placeholder": "Unique product identifier"})
    description = TextAreaField('Description',render_kw={"rows": 4, "placeholder": "Product details..."})
    price = DecimalField('Price*', places=2,validators=[DataRequired(), NumberRange(min=0.01)],render_kw={"step": "0.01", "min": "0.01"})
    stock = IntegerField('Stock*',validators=[DataRequired(), NumberRange(min=0)],render_kw={"min": "0"})
    category = SelectField('Category*', coerce=int,validators=[DataRequired()],description="Select product category")
    brand = SelectField('Brand*', coerce=int,validators=[DataRequired()],description="Select product brand")
    images = FileField('Product Images (max 5)',validators=[DataRequired(),FileAllowed(['jpg', 'jpeg', 'png', 'avif'], 'Images only!')],render_kw={'multiple': True,'accept': 'image/*','data-max-files': 5})
    is_featured = BooleanField('Featured Product')
    is_active = BooleanField('Active Product', default=True)
    submit = SubmitField('Save Product')

class CategoryForm(FlaskForm):
    # Required fields
    name = StringField(_l('Category Name'), validators=[DataRequired()])
    image = StringField(_l('Category Image URL'), validators=[DataRequired(), URL(message=_l('Invalid URL format.'))])
    # Parent category dropdown (populated dynamically)
    parent_category = SelectField(_l('Parent Category'), choices=[], coerce=int,  # Ensure integer values
        validators=[DataRequired()])
    # Optional: Retain "count" only if manual entry is required
    count = IntegerField(_l('Product Count'), validators=[NumberRange(min=0, message=_l('Product count cannot be negative.'))])
    submit = SubmitField(_l('Add Category'))

class BrandForm(FlaskForm):
    name = StringField(_l('Brand Name'),validators=[DataRequired(),
            Length(max=100, message=_l('Brand name must be under 100 characters'))],
            render_kw={"placeholder": _l("Enter brand name")})
    logo = StringField(_l('Brand Logo URL'),
        validators=[DataRequired(),URL(message=_l('Invalid URL format')),
            Length(max=200, message=_l('URL must be under 200 characters'))],
    render_kw={"placeholder": _l("https://example.com/logo.png"),"pattern": "https?://.+"})
    submit = SubmitField(_l('Create Brand'),render_kw={"class": "btn btn-primary"})

class ProductReviewForm(FlaskForm):
    text = TextAreaField(_l('Write your review'), validators=[DataRequired(), Length(max=500)])
    Rating = SelectField(_l('Rating'), choices=[(5, '5'), (4, '4'), (3, '3'), (2, '2'), (1, '1')], coerce=int, validators=[DataRequired()])
    submit = SubmitField(_l('Submit Review'))

class OrderDetailsForm(FlaskForm):
    id = StringField(_l('Order ID'), validators=[DataRequired()])
    customer_name = StringField(_l('Customer Name'), validators=[DataRequired()])
    address = TextAreaField(_l('Shipping Address'), validators=[DataRequired()])
    
class OrderStatusForm(FlaskForm):
    id = StringField(_l('Order ID'), validators=[DataRequired()])
    status = SelectField(_l('Status'), choices=[('Pending', 'Pending'), ('Shipped', 'Shipped'), ('Delivered', 'Delivered')], validators=[DataRequired()])
    

class CartForm(FlaskForm):
    user_id = IntegerField(_l('User ID'), validators=[DataRequired()])
    product_id = IntegerField(_l('Product ID'), validators=[DataRequired()])
    quantity = IntegerField(_l('Quantity'), validators=[DataRequired()], default=1)
    submit = SubmitField(_l('Add to Cart'))

class CouponForm(FlaskForm):
    code = StringField(_l('Coupon Code'), validators=[DataRequired()])
    discount_percentage = IntegerField(_l('Discount Percentage'), validators=[DataRequired()])
    expiration_date = StringField(_l('Expiration Date (YYYY-MM-DD)'), validators=[DataRequired()])
    submit = SubmitField(_l('Create Coupon'))

class CustomerOrderForm(FlaskForm):
    date = StringField(_l('Order Date (YYYY-MM-DD)'), validators=[DataRequired()])
    user_id = IntegerField(_l('User ID'), validators=[DataRequired()])
    cost = IntegerField(_l('Total Cost'), validators=[DataRequired()])
    submit = SubmitField(_l('Place Order'))