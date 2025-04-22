
from datetime import datetime, timedelta, timezone
from hashlib import md5
from app import app, db, login
import jwt

from flask_login import UserMixin

from werkzeug.security import generate_password_hash, check_password_hash


followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')
    payments = db.relationship('Payment', backref='author', lazy='dynamic')
    useraddress = db.relationship('ShippingAddresses', backref='author', lazy='dynamic')
    wishitems = db.relationship('Wishlist', backref='author', lazy='dynamic')

    def __repr__(self) -> str:
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode("utf-8")).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        followed = Post.query.join(
            followers, followers.c.followed_id == Post.user_id
        ).filter(followers.c.follower_id == self.id)
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode({"reset_password": self.id,
                           "exp": datetime.now(tz=timezone.utc) + timedelta(seconds=expires_in)},
                          app.config["SECRET_KEY"], algorithm="HS256")

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config["SECRET_KEY"], algorithms="HS256")[
                "reset_password"]
        except:           
            return None
        return User.query.get(id)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    title = db.Column(db.String(100))
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self) -> str:
        return f'<Post {self.body}>'

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    payment = db.Column(db.String(140))
    logo = db.Column(db.String(200))
    cardnumber = db.Column(db.Integer)
    carddate = db.Column(db.DateTime, index=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self) -> str:
        return f'<Payment {self.payment}>'
    
class CustomerOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship(
        'Product',
        backref='order',
        lazy='dynamic',
        foreign_keys='Product.customerorder_id'  # 指定外鍵
    )
    Details = db.relationship('OrderDetails', backref='author', lazy='dynamic')
    status = db.relationship('OrderStatus', backref='author', lazy='dynamic')
    cost = db.Column(db.Float(9))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self) -> str:
        return f'<CustomerOrder {self.id}>'

class ShippingAddresses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    SAddress = db.Column(db.String(140))
    UAddress = db.Column(db.String(140))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


    def __repr__(self) -> str:
        return f'<shippingAddresses {self.Address}>'

class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wishitem =  db.Column(db.String(140))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self) -> str:
        return f'<Wishlist {self.wishitem}>'

class Product(db.Model):    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)            # 商品名称
    description = db.Column(db.Text)                             # 详细描述
    price = db.Column(db.Numeric(10,2), nullable=False)          # 价格
    stock = db.Column(db.Integer, default=0)                     # 库存
    main_image = db.Column(db.String(500))                      # 主图URL
    is_featured = db.Column(db.Boolean, default=False)          # 是否推荐
    is_active = db.Column(db.Boolean, default=True)             # 是否上架
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    images = db.relationship('ProductImage', backref='product', cascade='all, delete-orphan')
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category', back_populates='products')
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))
    brand = db.relationship('Brand', back_populates='products')
    customerorder_id = db.Column(db.Integer, db.ForeignKey('customer_order.id'))
    image = db.Column(db.String(200))
    reviews = db.relationship('ProductReview', backref='product', lazy='dynamic')
    order_id = db.Column(db.Integer, db.ForeignKey('customer_order.id'))
    Cart_items = db.relationship('Cart', backref='author', lazy='dynamic')

    def __repr__(self) -> str:
        return f'<Product {self.name}>'
    
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True)
    products = db.relationship('Product', back_populates='category')

    def __repr__(self) -> str:
        return f'<Category {self.name}>'
    
class Brand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    logo = db.Column(db.String(500))
    products = db.relationship('Product', back_populates='brand')

    def __repr__(self) -> str:
        return f'<Brand {self.name}>'

class ProductReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer)
    comment = db.Column(db.String(500))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self) -> str:
        return f'<ProductReview {self.comment}>'
    
class OrderDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('customer_order.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer)

    def __repr__(self) -> str:
        return f'<OrderDetails {self.id}>'
    
class OrderStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(140))
    order_id = db.Column(db.Integer, db.ForeignKey('customer_order.id'))

    def __repr__(self) -> str:
        return f'<OrderStatus {self.status}>'
    
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer, default=1)

    def __repr__(self) -> str:
        return f'<Cart {self.id}>'
    
class Coupon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_percentage = db.Column(db.Float, nullable=False)
    expiration_date = db.Column(db.DateTime, nullable=False)

    def __repr__(self) -> str:
        return f'<Coupon {self.code}>'
    
class ProductImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    is_main = db.Column(db.Boolean, default=False)  
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))

    def __repr__(self) -> str:
        return f'<ProductImage {self.url}>'