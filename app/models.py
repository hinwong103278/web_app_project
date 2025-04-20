
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
    
##class Order(db.Model):
##    id = db.Column(db.Integer, primary_key=True)
##    date = db.Column(db.Datetime, index=True, default=datetime.utcnow)
##    # items = db.Column(db.String, db.ForeignKey('product.name'))
##    cost = db.Column(db.Float(9))

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
    #product_id = db.Column(db.Integer, db.ForeignKey(''))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self) -> str:
        return f'<Wishlist {self.wishitem}>'
    
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140))
    price = db.Column(db.Float)
    description = db.Column(db.String(140))
    image = db.Column(db.String(200))
    category = db.Column(db.String(140))
    stock = db.Column(db.Integer)
    #wishlist = db.relationship('Wishlist', backref='author', lazy='dynamic')
    #cart = db.relationship('Cart', backref='author', lazy='dynamic')
    #order = db.relationship('Order', backref='author', lazy='dynamic')
    
    def __repr__(self) -> str:
        return f'<Product {self.name}>'
    
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140))
    #product = db.relationship('Product', backref='category', lazy='dynamic')
    
    def __repr__(self) -> str:
        return f'<Category {self.name}>'
    
class Brand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140))
    #product = db.relationship('Product', backref='author', lazy='dynamic')
    
    def __repr__(self) -> str:
        return f'<Brand {self.name}>'
    
class Productreviews(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    review = db.Column(db.String(140))
    rating = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    #product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    
    def __repr__(self) -> str:
        return f'<Productreviews {self.review}>'
    
class Orderdetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    #order_id = db.Column(db.Integer, db.ForeignKey('oreder.id'))
    
    def __repr__(self) -> str:
        return f'<Orderdetails {self.quantity}>'

class Orderstatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(140))
    #order_id = db.Column(db.Integer, db.ForeignKey(''))
    
    def __repr__(self) -> str:
        return f'<Orderstatus {self.status}>'