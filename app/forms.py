from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    TextAreaField, DecimalField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from flask_babel import _, lazy_gettext as _l
from app.models import User  


class LoginForm(FlaskForm):
    username = StringField(_l('用户名'), validators=[DataRequired()])
    password = PasswordField(_l('密码'), validators=[DataRequired()])
    remember_me = BooleanField(_l('记住我'))
    submit = SubmitField(_l('登录'))


class RegistrationForm(FlaskForm):
    username = StringField(_l('用户名'), validators=[DataRequired()])
    email = StringField(_l('电子邮件'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('密码'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('重复密码'), validators=[DataRequired(), EqualTo('password')]
    )
    submit = SubmitField(_l('注册'))

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError(_('该用户名已被使用，请选择其他用户名。'))

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError(_('该电子邮件已被使用，请选择其他电子邮件地址。'))


class ResetPasswordRequestForm(FlaskForm):
    email = StringField(_l('电子邮件'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('请求重置密码'))


class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l('密码'), validators=[DataRequired()])
    password2 = PasswordField(
        _l('重复密码'), validators=[DataRequired(), EqualTo('password')]
    )
    submit = SubmitField(_l('重置密码'))


class EditProfileForm(FlaskForm):
    username = StringField(_l('用户名'), validators=[DataRequired()])
    about_me = TextAreaField(_l('关于我'), validators=[Length(min=0, max=140)])
    submit = SubmitField(_l('提交'))

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError(_('该用户名已被使用，请选择其他用户名。'))


class AddProductForm(FlaskForm):
    name = StringField(_l('商品名称'), validators=[DataRequired()])
    price = DecimalField(_l('价格'), validators=[DataRequired()])
    category = SelectField(
        _l('类别'), 
        choices=[('fruits', '水果'), ('vegetables', '蔬菜'), ('dairy', '乳制品')],
        validators=[DataRequired()]
    )
    description = TextAreaField(_l('商品描述'), validators=[Length(max=200)])
    submit = SubmitField(_l('添加商品'))


class SearchProductForm(FlaskForm):
    search_query = StringField(_l('搜索商品'), validators=[DataRequired()])
    submit = SubmitField(_l('搜索'))


class ProductDetailForm(FlaskForm):
    product_id = StringField(_l('商品 ID'), validators=[DataRequired()])
    submit = SubmitField(_l('查看详情'))


class ReviewForm(FlaskForm):
    product_id = StringField(_l('商品 ID'), validators=[DataRequired()])
    rating = SelectField(
        _l('评分'), 
        choices=[(1, '1星'), (2, '2星'), (3, '3星'), (4, '4星'), (5, '5星')],
        validators=[DataRequired()]
    )
    comment = TextAreaField(_l('评论'), validators=[Length(max=500)])
    submit = SubmitField(_l('提交评价'))


class OrderForm(FlaskForm):
    product_ids = StringField(_l('商品 ID (逗号分隔)'), validators=[DataRequired()])
    quantities = StringField(_l('数量 (逗号分隔)'), validators=[DataRequired()])
    submit = SubmitField(_l('提交订单'))


class CartContentForm(FlaskForm):
    submit = SubmitField(_l('查看购物车'))


class CheckoutForm(FlaskForm):
    address = StringField(_l('收货地址'), validators=[DataRequired()])
    payment_method = SelectField(
        _l('支付方式'), 
        choices=[('credit_card', '信用卡'), ('paypal', 'PayPal')],
        validators=[DataRequired()]
    )
    submit = SubmitField(_l('结账'))