from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from models import db, User, Service

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message_category = "info"
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@app.route("/")
def index():
    featured_services = Service.query.filter_by(is_active=True).order_by(Service.created_at.desc()).limit(6).all()
    return render_template("index.html", featured_services=featured_services)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        location = request.form.get("location", "").strip()

        if not name or not email or not password:
            flash("Please fill in all required fields.", "error")
        elif len(password) < 8:
            flash("Your password must be at least 8 characters.", "error")
        elif User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "error")
        else:
            user = User(
                name=name,
                email=email,
                password_hash=generate_password_hash(password),
                location=location or None,
                credits=3
            )
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Welcome to TimeBank! We've added 3 starter credits to your wallet.", "success")
            return redirect(url_for("dashboard"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f"Welcome back, {user.name.split()[0]}!", "success")
            next_page = request.args.get("next")
            return redirect(next_page if next_page and next_page.startswith("/") else url_for("dashboard"))

        flash("Email or password is incorrect. Please try again.", "error")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You've been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    my_services = Service.query.filter_by(owner_id=current_user.id, is_active=True).order_by(Service.created_at.desc()).limit(4).all()
    return render_template("dashboard.html", my_services=my_services)


@app.route("/explore")
def explore():
    category = request.args.get("category", "").strip()
    search = request.args.get("q", "").strip()
    query = Service.query.filter_by(is_active=True)

    if category:
        query = query.filter_by(category=category)
    if search:
        term = f"%{search}%"
        query = query.filter(db.or_(Service.title.ilike(term), Service.description.ilike(term), Service.category.ilike(term)))

    services = query.order_by(Service.created_at.desc()).all()
    categories = ["Technology", "Creative", "Academic", "Lifestyle", "Music", "Other"]
    return render_template("explore.html", services=services, categories=categories, selected_category=category, search=search)


@app.route("/offer", methods=["GET", "POST"])
@login_required
def offer_service():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        duration = request.form.get("duration", "1").strip()

        if not title or not category or not description:
            flash("Please complete all the required fields.", "error")
        else:
            try:
                duration_hours = max(1, min(8, int(duration)))
            except ValueError:
                duration_hours = 1

            service = Service(
                title=title,
                category=category,
                description=description,
                duration_hours=duration_hours,
                owner_id=current_user.id
            )
            db.session.add(service)
            db.session.commit()
            flash("Your service is now listed on TimeBank!", "success")
            return redirect(url_for("dashboard"))

    categories = ["Technology", "Creative", "Academic", "Lifestyle", "Music", "Other"]
    return render_template("offer_service.html", categories=categories)


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)