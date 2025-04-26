from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, session, make_response
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


@app.route('/')
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    products = Product.query.all()  # 查詢所有產品
    posts = current_user.followed_posts().paginate(
        page=request.args.get('page', 1, type=int),
        per_page=app.config['POSTS_PER_PAGE'],
        error_out=False
    )
    next_url = url_for('index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) if posts.has_prev else None
    payment = Payment.query.all()
    address = ShippingAddresses.query.all()
    brands = Brand.query.all()
    categories = Category.query.all()
    return render_template('index.html.j2',title=_('Home'),form=form,posts=posts.items,
                            next_url=next_url,prev_url=prev_url,payment=payment,
                            address=address,products=products,brands=brands,
                            categories=categories )


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
        # 保存用戶信息到Session
        session['username'] = user.username
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html.j2', title=_('Sign In'), form=form)


@app.route('/logout')
def logout():
    session.pop('username', None)  # 清除Session中的用戶數據
    logout_user() # 清除Flask-Login的用戶認證
    flash(_('You have been logged out.'))  # 顯示登出提示消息
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, useraddress=form.UAddress.data)
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
    payment = Payment.query.all()
    page = request.args.get('page', 1, type=int)
    posts = user.followed_posts().paginate(
        page=page, per_page=app.config["POSTS_PER_PAGE"], error_out=False)
    next_url = url_for(
        'index', page=posts.next_num) if posts.next_num else None
    prev_url = url_for(
        'index', page=posts.prev_num) if posts.prev_num else None
    return render_template('user.html.j2', user=user, posts=posts.items,
                           next_url=next_url, prev_url=prev_url, payment=payment)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        current_user.useraddress = form.useraddress.data 
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
        form.useraddress.data = current_user.useraddress
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
def set_payment():
    form = PaymentForm()
    payment = Payment.query.all()
    if form.validate_on_submit():
        payments = Payment(payment=form.payment.data, logo=form.logo.data)
        db.session.add(payments)
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('index'))
    return render_template('setpayment.html.j2', title=_('set_payment'),
                           form=form, user=user, payment=payment)

@app.route('/set_shipping_Address', methods=['GET', 'POST'])
@login_required
def shippingAddress():
    form = ShippingAddressesForm()
    address = ShippingAddresses.query.all()
    if form.validate_on_submit():
        address = ShippingAddresses(address=form.address.data)
        db.session.add(address)
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('index'))
    return render_template('setshippingAddress.html.j2', title=_('shippingAddress'),
                           form=form, address=address)


@app.route('/set_product', methods=['GET', 'POST'])
@login_required
def set_product():
    form = ProductForm()
    products = Product.query.all()
    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            image=form.image.data,
        )
        db.session.add(product)
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('set_product'))
    return render_template('set_product.html.j2', title=_('Product'), 
                           form=form, product=products)

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

@app.route('/set_productReview', methods=['GET', 'POST'], endpoint='set_productReview_general')
@login_required
def set_productReview_general():
    form = ProductReviewForm()
    if form.validate_on_submit():
        productReview = ProductReview(name=form.name.data)
        db.session.add(productReview)
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('index'))
    return render_template('set_productreview.html.j2', title=_('Product Review'),
                           form=form, user=current_user)

@app.route('/set_cart/<int:product_id>', methods=['POST'], endpoint='set_cart_add')
@login_required
def set_cart_add(product_id):
    product = Product.query.get_or_404(product_id)
    cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product.id).first()
    if cart_item:
        cart_item.quantity += 1  
    else:
        cart_item = Cart(user_id=current_user.id, product_id=product.id, quantity=1)
        db.session.add(cart_item)
    db.session.commit()
    flash(_('Product added to cart!'))
    return redirect(url_for('set_product'))

@app.route('/set_productReview/<int:product_id>', methods=['GET', 'POST'], endpoint='set_productReview_specific')
@login_required
def set_productReview_specific(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductReviewForm()
    if form.validate_on_submit():
        review = ProductReview(
            content=form.content.data,
            product_id=product.id,
            user_id=current_user.id
        )
        db.session.add(review)
        db.session.commit()
        flash(_('Your review has been submitted.'))
        return redirect(url_for('index'))
    return render_template('set_productreview.html.j2', title=_('Review Product'),
                           form=form, product=product)

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

@app.route('/set_cart', methods=['GET', 'POST'], endpoint='set_cart_manage')
@login_required
def set_cart_manage():
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

@app.route('/set_cookie')
def set_cookie():
    resp = make_response("Cookie is set!")
    resp.set_cookie('username', 'example_user', max_age=60*60*24, secure=True)  # 保存一天
    return resp

@app.route('/get_cookie')
def get_cookie():
    username = request.cookies.get('username')  # 獲取名為 'username' 的Cookie
    if username:
        return f'Hello, {username}!'
    return 'No cookie found!'

@app.route('/delete_cookie')
def delete_cookie():
    resp = make_response("Cookie has been deleted!")
    resp.set_cookie('username', '', max_age=0)  # 刪除Cookie
    return resp


@app.route('/remove_payment/<int:payment_id>', methods=['GET','POST'])
@login_required
def remove_payment(payment_id):
    payment = Payment.query.filter_by(id=payment_id).first_or_404()
    db.session.delete(payment)
    db.session.commit()
    flash('Payment has been removed.')
    return redirect(('index'))

@app.route('/remove_address/<int:address_id>',methods=['GET',"POST"])
@login_required
def remove_address(address_id):
    address = ShippingAddresses.query.filter_by(id=address_id).first_or_404()
    db.session.delete(address)
    db.session.commit()
    flash('address has been removed.')
    return redirect(('index')) 