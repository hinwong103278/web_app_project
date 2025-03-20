
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
    
class Orders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(64), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    user = db.relationship('User', backref='orders')
    order_details = db.relationship('OrderDetails', backref='order', lazy='dynamic')

    def __repr__(self):
        return f'<Order {self.id} - User {self.user_id}>'

    def update_status(self, new_status):
        """更新訂單狀態"""
        self.status = new_status
        db.session.commit()

    @staticmethod
    def get_orders_by_user(user_id):
        """根據用戶 ID 獲取訂單"""
        return Orders.query.filter_by(user_id=user_id).all()


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    user = db.relationship('User', backref='cart_items')
    product = db.relationship('Product', backref='cart_items')

    def __repr__(self):
        return f'<Cart {self.id} - User {self.user_id} - Product {self.product_id}>'

    def update_quantity(self, quantity):
        """更新購物車中產品的數量"""
        self.quantity = quantity
        db.session.commit()

    @staticmethod
    def get_cart_by_user(user_id):
        """根據用戶 ID 獲取購物車內容"""
        return Cart.query.filter_by(user_id=user_id).all()


class Coupons(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(64), unique=True, nullable=False)
    discount = db.Column(db.Float, nullable=False)
    expiration_date = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<Coupon {self.code}>'

    def is_valid(self):
        """檢查優惠券是否有效"""
        return datetime.utcnow() <= self.expiration_date

    @staticmethod
    def get_coupon_by_code(code):
        """根據代碼獲取優惠券"""
        return Coupons.query.filter_by(code=code).first()


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    payment_method = db.Column(db.String(64), nullable=False)
    payment_status = db.Column(db.String(64), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    order = db.relationship('Orders', backref='payment')

    def __repr__(self):
        return f'<Payment {self.id} - Order {self.order_id}>'

    def update_status(self, new_status):
        """更新付款狀態"""
        self.payment_status = new_status
        db.session.commit()


class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    product = db.relationship('Product', backref='inventory')

    def __repr__(self):
        return f'<Inventory {self.id} - Product {self.product_id}>'

    def update_stock(self, quantity):
        """更新庫存數量"""
        self.stock = quantity
        db.session.commit()

    @staticmethod
    def get_stock_by_product(product_id):
        """根據產品 ID 獲取庫存"""
        return Inventory.query.filter_by(product_id=product_id).first()


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'), nullable=False)
    category = db.relationship('Category', backref='products')
    brand = db.relationship('Brand', backref='products')

    def __repr__(self):
        return f'<Product {self.name}>'

    @staticmethod
    def get_products_by_category(category_id):
        """根據分類 ID 獲取產品"""
        return Product.query.filter_by(category_id=category_id).all()


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)

    def __repr__(self):
        return f'<Category {self.name}>'


class Brand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)

    def __repr__(self):
        return f'<Brand {self.name}>'


class OrderDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    product = db.relationship('Product', backref='order_details')

    def __repr__(self):
        return f'<OrderDetails {self.id} - Order {self.order_id} - Product {self.product_id}>'


class ProductReviews(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    product = db.relationship('Product', backref='reviews')
    user = db.relationship('User', backref='reviews')

    def __repr__(self):
        return f'<ProductReview {self.id} - Product {self.product_id} - User {self.user_id}>'

    def update_review(self, rating, review):
        """更新評價和評論"""
        self.rating = rating
        self.review = review
        db.session.commit()

    @staticmethod
    def get_reviews_by_product(product_id):
        """根據產品 ID 獲取所有評論"""
        return ProductReviews.query.filter_by(product_id=product_id).all()

    @staticmethod
    def get_average_rating(product_id):
        """計算產品的平均評分"""
        reviews = ProductReviews.query.filter_by(product_id=product_id).all()
        if not reviews:
            return 0
        total_rating = sum(review.rating for review in reviews)
        return total_rating / len(reviews)


class OrderStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(64), unique=True, nullable=False)

    def __repr__(self):
        return f'<OrderStatus {self.status}>'

    @staticmethod
    def get_all_statuses():
        """獲取所有訂單狀態"""
        return OrderStatus.query.all()

    @staticmethod
    def add_status(status_name):
        """添加新的訂單狀態"""
        if not OrderStatus.query.filter_by(status=status_name).first():
            new_status = OrderStatus(status=status_name)
            db.session.add(new_status)
            db.session.commit()
            return new_status
        return None