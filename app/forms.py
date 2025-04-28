from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    TextAreaField, IntegerField, SelectField, DecimalField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, \
    Length, NumberRange
from flask_babel import _, lazy_gettext as _l
from app.models import User, CustomerOrder, Product


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
    UAddress = StringField(_l('Address'), validators=[DataRequired()])
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
    useraddress = StringField(_l('Useraddress'), validators=[DataRequired()])
    cardnumber = StringField(_l('Cardnumber'), validators=[DataRequired()])
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
    address = StringField(_l('enter the address in here'), validators=[DataRequired()])
    submit = SubmitField(_l('Submit'))

class UserAddressForm(FlaskForm):
    UAddress = StringField(_l('enter the address in here'), validators=[DataRequired()])
    submit = SubmitField(_l('Submit'))

class ProductForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = StringField('Description')
    price = DecimalField('Price')
    image = StringField('Image URL')
    category = SelectField('Category', coerce=int)  # 類別下拉框
    new_category = StringField('New Category')  # 新類別輸入框
    brand = SelectField('Brand', coerce=int)  # 現有品牌選擇
    new_brand = StringField('New Brand')  # 新品牌
    submit = SubmitField('Submit')

class CategoryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = StringField('Description')  # 類別描述
    submit = SubmitField('Submit')

class BrandForm(FlaskForm):
    name = StringField(_l('Brand Name'), validators=[DataRequired()])
    description = StringField('Description')
    submit = SubmitField(_l('View Brand'))

class ProductReviewForm(FlaskForm):
    name = StringField('Review Title', validators=[DataRequired()])  # 評論名稱
    content = TextAreaField('Review Content', validators=[DataRequired()])  # 評論內容
    rating = IntegerField('Rating', validators=[DataRequired(), NumberRange(min=1, max=5)])  # 評分 (1-5)
    product_id = SelectField('Product', coerce=int, validators=[DataRequired()])  # 關聯產品
    submit = SubmitField('Submit Review')

class OrderDetailsForm(FlaskForm):
    id = StringField(_l('Order ID'), validators=[DataRequired()])
    customer_name = StringField(_l('Customer Name'), validators=[DataRequired()])
    address = TextAreaField(_l('Shipping Address'), validators=[DataRequired()])
    submit = SubmitField(_l('Confirm Order'))
    
class OrderStatusForm(FlaskForm):
    status = SelectField(
        _l('Order Status'),
        choices=[('Pending', 'Pending'), ('Shipped', 'Shipped'), ('Delivering', 'Delivering')],
        validators=[DataRequired()]
    )
    product_id = SelectField(
        _l('Product'),
        coerce=int,
        validators=[DataRequired()]
    )  # 选择产品
    order_id = SelectField(
        _l('Order'),
        coerce=int,
        validators=[DataRequired()]
    )  # 选择订单
    submit = SubmitField(_l('Update Status'))

    def __init__(self, *args, **kwargs):
        super(OrderStatusForm, self).__init__(*args, **kwargs)
        self.product_id.choices = [(p.id, p.name) for p in Product.query.all()]
        self.order_id.choices = [(o.id, f"Order #{o.id}") for o in CustomerOrder.query.all()]


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

class ReturnsForm(FlaskForm):
    order_id = SelectField(
        _l('Order ID'),
        coerce=int,
        validators=[DataRequired()]
    )
    reason = TextAreaField(_l('Reason for Return'), validators=[DataRequired()])
    submit = SubmitField(_l('Submit Return'))

    def __init__(self, *args, **kwargs):
        super(ReturnsForm, self).__init__(*args, **kwargs)
        self.order_id.choices = [(order.id, f"Order #{order.id}") for order in CustomerOrder.query.all()]