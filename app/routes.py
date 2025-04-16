from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from flask_babel import _, get_locale
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm, \
    ResetPasswordRequestForm, ResetPasswordForm, PaymentForm, ShippingAddressesForm, \
    UserAddressForm, ProductForm, BrandForm, CategoryForm, ProductReviewForm, \
    OrderDetailsForm, OrderStatusForm, CartForm, CouponForm, CustomerOrderForm
from app.models import User, Post, Payment, ShippingAddresses, Product, Brand, Category, ProductReview, OrderDetails, OrderStatus, CustomerOrder, Coupon, Cart
from app.email import send_password_reset_email


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.locale = str(get_locale())


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash(_('Your post is now live!'))
        return redirect(url_for('index'))
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page=page, per_page=app.config["POSTS_PER_PAGE"], error_out=False)
    next_url = url_for(
        'index', page=posts.next_num) if posts.next_num else None
    prev_url = url_for(
        'index', page=posts.prev_num) if posts.prev_num else None
    return render_template('index.html.j2', title=_('Home'), form=form,
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=app.config["POSTS_PER_PAGE"], error_out=False)
    next_url = url_for(
        'explore', page=posts.next_num) if posts.next_num else None
    prev_url = url_for(
        'explore', page=posts.prev_num) if posts.prev_num else None
    return render_template('index.html.j2', title=_('Explore'),
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(_('Invalid username or password'))
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html.j2', title=_('Sign In'), form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(_('Congratulations, you are now a registered user!'))
        return redirect(url_for('login'))
    return render_template('register.html.j2', title=_('Register'), form=form)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash(
            _('Check your email for the instructions to reset your password'))
        return redirect(url_for('login'))
    return render_template('reset_password_request.html.j2',
                           title=_('Reset Password'), form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if user is None:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash(_('Your password has been reset.'))
        return redirect(url_for('login'))
    return render_template('reset_password.html.j2', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.followed_posts().paginate(
        page=page, per_page=app.config["POSTS_PER_PAGE"], error_out=False)
    next_url = url_for(
        'index', page=posts.next_num) if posts.next_num else None
    prev_url = url_for(
        'index', page=posts.prev_num) if posts.prev_num else None
    return render_template('user.html.j2', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html.j2', title=_('Edit Profile'),
                           form=form)


@app.route('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found.', username=username))
        return redirect(url_for('index'))
    if user == current_user:
        flash(_('You cannot follow yourself!'))
        return redirect(url_for('user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash(_('You are following %(username)s!', username=username))
    return redirect(url_for('user', username=username))


@app.route('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(_('User %(username)s not found.', username=username))
        return redirect(url_for('index'))
    if user == current_user:
        flash(_('You cannot unfollow yourself!'))
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(_('You are not following %(username)s.', username=username))
    return redirect(url_for('user', username=username))


@app.route('/set Payment', methods=['GET', 'POST'])
@login_required
def payment():
    form = PaymentForm()
    if form.validate_on_submit():
        payments = Payment(payment=form.payment.data, logo=form.logo.data)
        db.session.add(payments)
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('index'))
    return render_template('setpayment.html.j2', title=_('payment'),
                           form=form, user=user)

@app.route('/set shippingAddress', methods=['GET', 'POST'])
@login_required
def shippingAddress():
    form = ShippingAddressesForm()
    if form.validate_on_submit():
        SAddress = ShippingAddresses(SAddress=form.SAddress.data)
        db.session.add(SAddress)
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('index'))
    return render_template('setshippingAddress.html.j2', title=_('shippingAddress'),
                           form=form)

@app.route('/set userAddress', methods=['GET', 'POST'])
@login_required
def userAddress():
    form = UserAddressForm()
    if form.validate_on_submit():
        UAddress = ShippingAddresses(UAddress=form.UAddress.data, author=current_user)
        db.session.add(UAddress)
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('index'))
    return render_template('setuserAddress.html.j2', title=_('userAddress'),
                           form=form, user=user)

@app.route('/set_product', methods=['GET', 'POST'])
@login_required
def set_product():
    form = ProductForm()
    if form.validate_on_submit():
        product = Product(name=form.name.data)
        db.session.add(product)
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('index'))
    return render_template('set_product.html.j2', title=_('product'),
                           form=form, user=user)

@app.route('/set_brand', methods=['GET', 'POST'])
@login_required
def set_brand():
    form = BrandForm()
    if form.validate_on_submit():
        brand = Brand(name=form.name.data)
        db.session.add(brand)
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('index'))
    return render_template('set_brand.html.j2', title=_('brand'),
                           form=form, user=user)

@app.route('/set_category', methods=['GET', 'POST'])
@login_required
def set_category():
    form = CategoryForm()
    if form.validate_on_submit():
        category = Category(name=form.name.data)
        db.session.add(category)
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('index'))
    return render_template('set_category.html.j2', title=_('category'),
                           form=form, user=user)

@app.route('/set_productReview', methods=['GET', 'POST'])
@login_required
def set_productReview():
    form = ProductReviewForm()
    if form.validate_on_submit():
        productReview = ProductReview(name=form.name.data)
        db.session.add(productReview)
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('index'))
    return render_template('set_producteview.html.j2', title=_('productReview'),
                           form=form, user=user)

@app.route('/set_orderdetails', methods=['GET', 'POST'])
@login_required
def set_orderdetails():
    form = OrderDetailsForm()
    if form.validate_on_submit():
        orderdetails = OrderDetails(name=form.name.data)
        db.session.add(orderdetails)
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('index'))
    return render_template('set_orderdetails.html.j2', title=_('orderdetails'),
                           form=form, user=user)

@app.route('/set_orderstatus', methods=['GET', 'POST'])
@login_required
def set_orderstatus():
    form = OrderStatusForm()
    if form.validate_on_submit():
        orderstatus = OrderStatus(name=form.name.data)
        db.session.add(orderstatus)
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('index'))
    return render_template('set_orderstatus.html.j2', title=_('orderstatus'),
                           form=form, user=user)

@app.route('/set_cart', methods=['GET', 'POST'])
@login_required
def set_cart():
    form = CartForm()
    if form.validate_on_submit():
        cart_item = Cart(user_id=form.user_id.data, product_id=form.product_id.data, quantity=form.quantity.data)
        db.session.add(cart_item)
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('index'))
    return render_template('set_cart.html.j2', title=_('Set Cart'), form=form)

@app.route('/set_coupon', methods=['GET', 'POST'])
@login_required
def set_coupon():
    form = CouponForm()
    if form.validate_on_submit():
        coupon = Coupon(code=form.code.data, discount_percentage=form.discount_percentage.data, expiration_date=form.expiration_date.data)
        db.session.add(coupon)
        db.session.commit()
        flash(_('Your coupon has been created.'))
        return redirect(url_for('index'))
    return render_template('set_coupon.html.j2', title=_('Set Coupon'), form=form)

@app.route('/set_customer_order', methods=['GET', 'POST'])
@login_required
def set_customer_order():
    form = CustomerOrderForm()
    if form.validate_on_submit():
        order = CustomerOrder(date=form.date.data, user_id=form.user_id.data, cost=form.cost.data)
        db.session.add(order)
        db.session.commit()
        flash(_('Your order has been created.'))
        return redirect(url_for('index'))
    return render_template('set_customer_order.html.j2', title=_('Set Customer Order'), form=form)