from datetime import datetime
from flask import render_template, flash, redirect, url_for, request, g, session, make_response, abort
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from flask_babel import _, get_locale
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PostForm, \
    ResetPasswordRequestForm, ResetPasswordForm, PaymentForm, ShippingAddressesForm, \
    UserAddressForm, ProductForm, BrandForm, CategoryForm, ProductReviewForm, \
    OrderDetailsForm, OrderStatusForm, CartForm, CouponForm, CustomerOrderForm
from app.models import User, Post, Payment, ShippingAddresses, Product, Brand, Category, ProductReview, OrderDetails, OrderStatus, CustomerOrder, Coupon, Cart, Wishlist
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
    products = Product.query.all()  # 查詢所有產品
    page = request.args.get('page', 1, type=int)
    posts = current_user.followed_posts().paginate(
        page=page, per_page=app.config["POSTS_PER_PAGE"], error_out=False)
    next_url = url_for(
        'index', page=posts.next_num) if posts.next_num else None
    prev_url = url_for(
        'index', page=posts.prev_num) if posts.prev_num else None
    payment = Payment.query.all()
    address = ShippingAddresses.query.all()
    return render_template('index.html.j2', title=_('Home'),
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url, payment=payment, address=address, products=products)


@app.route('/explore', methods=['GET', 'POST'])
@login_required
def explore():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash(_('Your post is now live!'))
        return redirect(url_for('explore'))
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page=page, per_page=app.config["POSTS_PER_PAGE"], error_out=False)
    next_url = url_for(
        'explore', page=posts.next_num) if posts.next_num else None
    prev_url = url_for(
        'explore', page=posts.prev_num) if posts.prev_num else None
    return render_template('explore.html.j2', title=_('Explore'),
                           posts=posts.items, next_url=next_url,
                           prev_url=prev_url, form=form)


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
    form.category.choices = [(c.id, c.name) for c in Category.query.all()]
    form.brand.choices = [(b.id, b.name) for b in Brand.query.all()]  # 填充品牌選項

    products = Product.query.all()
    if form.validate_on_submit():
        # 處理類別
        category_id = None
        if form.new_category.data:
            new_category = Category(name=form.new_category.data)
            db.session.add(new_category)
            db.session.commit()
            category_id = new_category.id
        elif form.category.data:
            category_id = form.category.data

        # 處理品牌
        brand_id = None
        if form.new_brand.data:
            new_brand = Brand(name=form.new_brand.data, description=None)
            db.session.add(new_brand)
            db.session.commit()
            brand_id = new_brand.id
        elif form.brand.data:
            brand_id = form.brand.data

        # 創建產品
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            image=form.image.data,
            category_id=category_id,
            brand_id=brand_id  # 分配品牌
        )
        db.session.add(product)
        db.session.commit()
        flash(_('Product has been added successfully.'))
        return redirect(url_for('set_product'))
    
    return render_template('set_product.html.j2', title=_('Add Product'), form=form, products=products)




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

##@app.route('/set_cart', methods=['GET', 'POST'])
##@login_required
##def set_cart():
##    form = CartForm()
##    if form.validate_on_submit():
##        cart_item = Cart(user_id=form.user_id.data, product_id=form.product_id.data, quantity=form.quantity.data)
##        db.session.add(cart_item)
##        db.session.commit()
##        flash(_('Your changes have been saved.'))
##        return redirect(url_for('index'))
##    return render_template('set_cart.html.j2', title=_('Set Cart'), form=form)

@app.route('/set_coupon', methods=['GET', 'POST'])
@login_required
def set_coupon():
    if current_user.username != "Admin":
        abort(403)  # 只有 Admin 可以設置優惠券
    
    form = CouponForm()
    if form.validate_on_submit():
        coupon = Coupon(code=form.code.data,
                        discount_percentage=form.discount_percentage.data,
                        expiration_date=form.expiration_date.data)
        db.session.add(coupon)
        db.session.commit()
        flash(_('Coupon has been created.'))
        return redirect(url_for('index'))
    
    return render_template('set_coupon.html.j2', title=_('Set Coupon'), form=form)


@app.route('/orders', methods=['GET'])
@login_required
def view_orders():
    user_orders = CustomerOrder.query.filter_by(user_id=current_user.id).order_by(CustomerOrder.date.desc()).all()
    return render_template('orders.html.j2', orders=user_orders)


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

@app.route('/set_cart', methods=['GET'])
@login_required
def view_cart():
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('/cart.html.j2', cart_items=cart_items, total_price=total_price)

@app.route('/set_cart/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    item = Cart.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        abort(403)
    
    form = CartForm()
    if form.validate_on_submit():
        item.quantity = form.quantity.data
        db.session.commit()
        flash(_('Cart updated!'))
    
    return redirect(url_for('view_cart'))

@app.route('/set_cart/remove/<int:item_id>', methods=['GET'])
@login_required
def remove_cart_item(item_id):
    item = Cart.query.get_or_404(item_id)
    if item.user_id != current_user.id:
        abort(403)
    
    db.session.delete(item)
    db.session.commit()
    flash(_('Item removed from cart'))
    return redirect(url_for('view_cart'))

@app.route('/coupons', methods=['GET'])
@login_required
def view_coupons():
    user_coupons = Coupon.query.all()  # 移除 user_id，改為查詢所有優惠券
    return render_template('coupons.html.j2', coupons=user_coupons)

@app.route('/set_cart/add/<int:product_id>', methods=['POST'])
@login_required
def set_cart(product_id):
    product = Product.query.get_or_404(product_id)
    # 檢查該產品是否已存在於購物車
    existing_cart_item = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing_cart_item:
        # 如果產品已在購物車中，增加數量
        existing_cart_item.quantity += 1
    else:
        # 如果是新產品，添加到購物車
        cart_item = Cart(user_id=current_user.id, product_id=product.id, quantity=1)
        db.session.add(cart_item)
    db.session.commit()
    flash(_('Product added to your cart!'))
    return redirect(url_for('view_cart'))

@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    # 獲取當前用戶的購物車項目
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    if not cart_items:
        flash(_('Your cart is empty.'))
        return redirect(url_for('view_cart'))

    # 創建新訂單
    new_order = CustomerOrder(
        user_id=current_user.id,
        cost=total_price,  # 訂單總價
        date=datetime.utcnow(),  # 訂單日期
        status='Completed'  # 訂單狀態設置為已完成
    )
    db.session.add(new_order)

    # 添加訂單中的商品至 `OrderDetails`
    for item in cart_items:
        order_detail = OrderDetails(
            order=new_order,  # 關聯到訂單
            product_id=item.product_id,
            quantity=item.quantity,
            price=item.product.price
        )
        db.session.add(order_detail)

    # 清空購物車
    for item in cart_items:
        db.session.delete(item)
    db.session.commit()

    flash(_('Payment successful! Your order has been created.'))
    return redirect(url_for('view_orders'))  # 跳轉至訂單頁面

@app.route('/categories', methods=['GET'])
@login_required
def view_categories():
    categories = Category.query.all()  # 查詢所有類別
    return render_template('categories.html.j2', categories=categories)

@app.route('/category/<int:category_id>', methods=['GET'])
@login_required
def view_category_products(category_id):
    category = Category.query.get_or_404(category_id)  # 查找類別
    products = Product.query.filter_by(category_id=category_id).all()  # 獲取該類別的產品
    return render_template('category_products.html.j2', category=category, products=products)

@app.route('/admin/categories', methods=['GET'])
@login_required
def admin_categories():
    categories = Category.query.all()
    return render_template('admin_categories.html.j2', categories=categories)



@app.route('/admin/category/delete/<int:category_id>', methods=['POST'])
@login_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash(_('Category has been deleted.'))
    return redirect(url_for('admin_categories'))

@app.route('/product/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)  # 查詢要編輯的產品
    form = ProductForm(obj=product)  # 填充表單初始值為產品信息
    form.category.choices = [(c.id, c.name) for c in Category.query.all()]  # 填充類別選項

    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.image = form.image.data
        product.category_id = form.category.data
        db.session.commit()
        flash(_('Product has been updated successfully.'))
        return redirect(url_for('set_product'))
    
    return render_template('set_product.html.j2', title=_('Edit Product'), form=form)

@app.route('/product/delete/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)  # 直接刪除產品
    db.session.commit()  # 自動刪除與該產品相關聯的 OrderDetails 記錄
    flash(_('Product and related records have been deleted successfully.'))
    return redirect(url_for('set_product'))

@app.route('/brands', methods=['GET'])
def view_brands():
    brands = Brand.query.all()  # 查詢所有品牌
    return render_template('brands.html.j2', brands=brands)

@app.route('/brand/<int:brand_id>', methods=['GET'])
def view_brand_products(brand_id):
    brand = Brand.query.get_or_404(brand_id)  # 查詢品牌
    products = Product.query.filter_by(brand_id=brand_id).all()  # 查詢品牌下的所有產品
    return render_template('brand_products.html.j2', brand=brand, products=products)

@app.route('/category/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)  # 查詢要編輯的類別
    form = CategoryForm(obj=category)  # 填充表單初始值

    if form.validate_on_submit():
        category.name = form.name.data
        category.description = form.description.data
        db.session.commit()  # 保存修改
        flash(_('Category has been updated successfully.'))
        return redirect(url_for('view_categories'))  # 返回類別列表頁面

    return render_template('edit_category.html.j2', title=_('Edit Category'), form=form, category=category)

@app.route('/brand/edit/<int:brand_id>', methods=['GET', 'POST'])
@login_required
def edit_brand(brand_id):
    brand = Brand.query.get_or_404(brand_id)  # 查詢品牌
    form = BrandForm(obj=brand)  # 初始化表單數據
    
    if form.validate_on_submit():  # 確認表單已成功提交
        brand.name = form.name.data
        brand.description = form.description.data
        db.session.commit()  # 保存更新到數據庫
        flash(_('Brand has been updated successfully.'))
        return redirect(url_for('view_brands'))  # 返回品牌列表頁面

    return render_template('edit_brand.html.j2', title=_('Edit Brand'), form=form, brand=brand)

@app.route('/brand/delete/<int:brand_id>', methods=['POST'])
@login_required
def delete_brand(brand_id):
    brand = Brand.query.get_or_404(brand_id)

    # 如果品牌下有關聯的產品，提示無法直接刪除
    if brand.products.count() > 0:
        flash(_('You cannot delete this brand because it is associated with products.'))
        return redirect(url_for('view_brands'))
    
    db.session.delete(brand)
    db.session.commit()
    flash(_('Brand has been deleted successfully.'))
    return redirect(url_for('view_brands'))


@app.route('/wishlist/add/<int:product_id>', methods=['POST'])
@login_required
def add_wishlist(product_id):
    product = Product.query.get_or_404(product_id)
    wishlist_item = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if wishlist_item:
        flash(_('this product is already in your wishlist'))
    else:
        wishlist_item = Wishlist(user_id=current_user.id, product_id=product.id)
        db.session.add(wishlist_item)
    db.session.commit()
    flash(_('Product added to your cart!'))
    return redirect(url_for('view_wishlist'))

@app.route('/view_wishlist', methods=['GET'])
@login_required
def view_wishlist():
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()
    return render_template('/wishlist.html.j2', title=_('view_Wishlist'), wishlist_items=wishlist_items)

@app.route('/wishlist/remove/<int:item_id>', methods=['GET'])
@login_required
def remove_wishlist_item(item_id):
    wishlist_item = Wishlist.query.get_or_404(item_id)
    db.session.delete(wishlist_item)
    db.session.commit()
    flash(_('Item removed from wishlist'))
    return redirect(url_for('view_wishlist'))