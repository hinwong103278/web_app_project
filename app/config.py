import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SECRET_KEY = os.environ.get("SECRET_KEY") or "you-will-never-guess"
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI") or \
        'postgresql://postgres:postgres@postgresdb:5432/postgres'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or "mailhog"
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 1025)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    PAYMENT_GATEWAY_API_KEY = os.environ.get('PAYMENT_GATEWAY_API_KEY')
    PAYMENT_GATEWAY_SECRET = os.environ.get('PAYMENT_GATEWAY_SECRET')
    ADMINS = ['peter@example.com']
    POSTS_PER_PAGE = 3
    LANGUAGES = ['en', 'es', 'zh']

    # File Uploads (for Product Images, Brand Logos, etc.)
    UPLOAD_FOLDER = os.path.join(basedir, 'app/static/images')
    ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'avif'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB

    # Pagination (for Products, Brands, Categories, Orders, etc.)
    PRODUCTS_PER_PAGE = 12
    BRANDS_PER_PAGE = 10
    CATEGORIES_PER_PAGE = 10
    ORDERS_PER_PAGE = 10
    REVIEWS_PER_PAGE = 5