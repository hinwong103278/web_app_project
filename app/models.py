
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
    useraddress = db.Column(db.String(140))
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
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self) -> str:
        return f'<Post {self.body}>'

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    payment = db.Column(db.String(140))
    logo = db.Column(db.String(200))

    def __repr__(self) -> str:
        return f'<Payment {self.payment}>'
    
class CustomerOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    cost = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    products = db.relationship('OrderDetails', backref='order', lazy=True)  # 讓訂單擁有多個商品
    status = db.Column(db.String(20), default='Pending')  # 訂單狀態：Pending, Completed, Canceled

    def __repr__(self):
        return f'<Order {self.id}, User {self.user_id}, Status: {self.status}>'

class ShippingAddresses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(140))

    def __repr__(self) -> str:
        return f'<shippingAddresses {self.address}>'

class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    Product = db.relationship('Product', backref='wishlist_items', lazy=True)

    def __repr__(self) -> str:
        return f'<Wishlist {self.wishitem}>'

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140))
    description = db.Column(db.String(140))
    price = db.Column(db.Float(9))
    image = db.Column(db.String(500))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'))  # 添加品牌外鍵
    reviews = db.relationship('ProductReview', backref='product', lazy='dynamic')
    order_id = db.Column(db.Integer, db.ForeignKey('customer_order.id'))
    Cart_items = db.relationship('Cart', backref='author', lazy='dynamic')
    wish_item = db.relationship('Wishlist', backref='rela_product', lazy='dynamic')

    def __repr__(self) -> str:
        return f'<Product {self.name}>'
    
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140))
    description = db.Column(db.String(140))
    products = db.relationship('Product', backref='category', lazy='dynamic')

    def __repr__(self) -> str:
        return f'<Category {self.name}>'
    
class Brand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)
    products = db.relationship('Product', backref='brand', lazy='dynamic')  # 與產品關聯

    def __repr__(self):
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
    order_id = db.Column(db.Integer, db.ForeignKey('customer_order.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id', ondelete='CASCADE'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

    product = db.relationship('Product')  # 用於獲取產品的詳細信息

    def __repr__(self):
        return f'<OrderDetails Order {self.order_id}, Product {self.product_id}, Quantity {self.quantity}>'


    
class OrderStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(140))
    order_id = db.Column(db.Integer, db.ForeignKey('customer_order.id'))

    def __repr__(self) -> str:
        return f'<OrderStatus {self.status}>'
    
class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    
    user = db.relationship('User', backref='cart_items', lazy=True)
    product = db.relationship('Product', backref='cart_items', lazy=True)
    
    def total_price(self):
        return self.product.price * self.quantity

    def __repr__(self):
        return f'<Cart User: {self.user_id}, Product: {self.product_id}, Quantity: {self.quantity}>'
    
class Coupon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_percentage = db.Column(db.Float, nullable=False)
    expiration_date = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Coupon {self.code}, Discount: {self.discount_percentage}%>'


