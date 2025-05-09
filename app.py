from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import requests
import logging

# -----------------------------------------------------------------
#کانفیگ

app = Flask(__name__)
app.config['SECRET_KEY'] = 'e9b1c4f3d8c44f719b6b8f4e7a8a2e6a84e5e6e8f2f3c5a9d3e6d4b7e8c2a1f3'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# مقداردهی کلید API
API_KEY = "کلید API خود را وارد کنید"
BASE_URL = "https://api.spoonacular.com/recipes"

# -----------------------------------------------------------------
# سرچ و نمایش غذا

# مسیر اصلی
@app.route("/")
def home():
    return render_template("index.html", recipes=[])

# جستجوی غذا بر اساس نام
@app.route("/search")
def search_recipe():
    query = request.args.get("query")
    diet = request.args.get("diet")

    if not query:
        return render_template("search_results.html", recipes=[], error="لطفاً نام غذا را وارد کنید.")

    params = {
        "query": query,
        "number": 10,
        "apiKey": API_KEY
    }

    if diet:
        params["diet"] = diet

    response = requests.get(f"{BASE_URL}/complexSearch", params=params)

    if response.status_code == 200:
        data = response.json()
        recipes = data.get("results", [])
        return render_template("search_results.html", recipes=recipes)
    else:
        return render_template("search_results.html", recipes=[], error="مشکلی در ارتباط با API رخ داده است.")

# دریافت جزئیات یک دستور پخت
@app.route("/recipe/<int:recipe_id>")
@login_required
def get_recipe_details(recipe_id):
    response = requests.get(f"{BASE_URL}/{recipe_id}/information", params={"apiKey": API_KEY})

    if response.status_code == 200:
        recipe = response.json()

        existing_history = History.query.filter_by(
            user_id=current_user.id,
            recipe_id=recipe_id
        ).first()

        if existing_history:
            existing_history.timestamp = db.func.current_timestamp()
        else:
            new_history = History(
                recipe_id=recipe_id,
                recipe_name=recipe.get("title", "نامشخص"),
                recipe_image=recipe.get("image", ""),
                user_id=current_user.id
            )
            db.session.add(new_history)

        db.session.commit()
        is_favorite = Favorite.query.filter_by(recipe_id=recipe_id, user_id=current_user.id).first() is not None
        return render_template('recipe_details.html', recipe=recipe, is_favorite=is_favorite)
    else:
        return "<p class='error'>مشکلی در دریافت جزئیات غذا رخ داده است.</p>"

# -----------------------------------------------------------------
#علاقه مندی کاربر

# مدل علاقه‌مندی‌ها
class Favorite(db.Model):
    __tablename__ = 'favorites'
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    image = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # ارتباط با مدل کاربر
    user = db.relationship('User', backref=db.backref('favorites', lazy=True))

# اضافه کردن از علاقه مندی
@app.route('/add_favorite/<int:recipe_id>', methods=['POST'])
@login_required
def add_favorite(recipe_id):
    recipe_title = request.form.get('title')
    recipe_image = request.form.get('image')

    existing_favorite = Favorite.query.filter_by(recipe_id=recipe_id, user_id=current_user.id).first()
    if existing_favorite:
        return jsonify({'success': False, 'message': 'این دستور پخت قبلاً به علاقه‌مندی‌های شما اضافه شده است!'})

    new_favorite = Favorite(recipe_id=recipe_id, title=recipe_title, image=recipe_image, user_id=current_user.id)
    db.session.add(new_favorite)
    db.session.commit()

    return jsonify({'success': True, 'message': '✅ دستور پخت با موفقیت به علاقه‌مندی‌ها اضافه شد!'})

# حذف کردن از علاقه مندی
@app.route('/remove_favorite/<int:recipe_id>', methods=['POST'])
@login_required
def remove_favorite(recipe_id):
    favorite = Favorite.query.filter_by(recipe_id=recipe_id, user_id=current_user.id).first()
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({'success': True, 'message': 'دستور پخت با موفقیت از علاقه‌مندی‌ها حذف شد.'})
    else:
        return jsonify({'success': False, 'message': 'این دستور پخت در علاقه‌مندی‌های شما نیست.'})

# مسیر علاقه مندی ها
@app.route('/favorites')
@login_required
def favorites():
    favorite_recipes = Favorite.query.filter_by(user_id=current_user.id).all()
    return render_template('favorites.html', favorites=favorite_recipes)

# -----------------------------------------------------------------
#مدیریت حساب های کاربری

# مدل کاربر
class User(db.Model, UserMixin):
    __tablename__ = 'user'  # نام جدول
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

# بررسی ورود کاربر
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ثبت‌نام
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')

        existing_user = User.query.filter_by(username=username).first()
        existing_email = User.query.filter_by(email=email).first()

        if existing_user:
            return jsonify({"error": "این نام کاربری قبلاً انتخاب شده است."}), 400
        if existing_email:
            return jsonify({"error": "این ایمیل قبلاً ثبت شده است."}), 400

        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        return jsonify({"redirect": url_for('login')})

    return render_template('register.html')

# ورود
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return jsonify({"redirect": url_for('home')})

        return jsonify({"error": "نام کاربری یا رمز عبور اشتباه است!"}), 400

    return render_template('login.html')


# خروج
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))



# -----------------------------------------------------------------
# تاریخچه جستجوی کاربران


# مدل تاریخچه
class History(db.Model):
    __tablename__ = 'history'
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, nullable=False)
    recipe_name = db.Column(db.String(200), nullable=False)
    recipe_image = db.Column(db.String(300))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    # ارتباط با مدل کاربر
    user = db.relationship('User', backref=db.backref('histories', lazy=True))

# مسیر تاریخچه
@app.route("/history")
@login_required
def view_history():
    user_history = History.query.filter_by(user_id=current_user.id).order_by(History.timestamp.desc()).all()
    return render_template("history.html", history=user_history)


# -----------------------------------------------------------------

# ایجاد جدول‌ها با SQLAlchemy
with app.app_context():
    db.create_all()

# فعال‌سازی لاگ‌های SQLAlchemy
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
