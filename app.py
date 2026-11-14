from datetime import datetime
from flask import Flask, render_template, redirect, url_for, flash, request, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, inspect, text
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from models import db, User, Service, ExchangeRequest, Transaction

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
    featured_services = (
        Service.query.filter_by(is_active=True)
        .order_by(Service.created_at.desc()).limit(6).all()
    )
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
            if next_page and next_page.startswith("/") and not next_page.startswith("//"):
                return redirect(next_page)
            return redirect(url_for("dashboard"))

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
    my_services = Service.query.filter_by(
        owner_id=current_user.id,
        is_active=True
            ).order_by(Service.created_at.desc()).all()
    incoming_count = ExchangeRequest.query.filter_by(
        provider_id=current_user.id, status="pending"
    ).count()
    outgoing_count = ExchangeRequest.query.filter_by(
        requester_id=current_user.id, status="pending"
    ).count()
    return render_template(
        "dashboard.html",
        my_services=my_services,
        incoming_count=incoming_count,
        outgoing_count=outgoing_count
    )


@app.route("/wallet")
@login_required
def wallet():
    transactions = Transaction.query.filter(
        or_(Transaction.from_user_id == current_user.id,
            Transaction.to_user_id == current_user.id)
    ).order_by(Transaction.created_at.desc()).all()
    return render_template("wallet.html", transactions=transactions)


@app.route("/explore")
def explore():
    category = request.args.get("category", "").strip()
    search = request.args.get("q", "").strip()
    query = Service.query.filter_by(is_active=True)

    if category:
        query = query.filter_by(category=category)
    if search:
        term = f"%{search}%"
        query = query.filter(or_(
            Service.title.ilike(term),
            Service.description.ilike(term),
            Service.category.ilike(term)
        ))

    services = query.order_by(Service.created_at.desc()).all()
    categories = ["Technology", "Creative", "Academic", "Lifestyle", "Music", "Other"]
    return render_template(
        "explore.html",
        services=services,
        categories=categories,
        selected_category=category,
        search=search
    )


@app.route("/service/<int:service_id>")
def service_detail(service_id):
    service = db.get_or_404(Service, service_id)
    if not service.is_active:
        abort(404)

    existing_request = None
    if current_user.is_authenticated:
        existing_request = ExchangeRequest.query.filter(
            ExchangeRequest.service_id == service.id,
            ExchangeRequest.requester_id == current_user.id,
            ExchangeRequest.status.in_(["pending", "accepted"])
        ).first()

    return render_template(
        "service_detail.html",
        service=service,
        existing_request=existing_request
    )


@app.route("/service/<int:service_id>/request", methods=["POST"])
@login_required
def request_service(service_id):
    service = db.get_or_404(Service, service_id)

    if not service.is_active:
        flash("This service is no longer available.", "error")
        return redirect(url_for("explore"))

    if service.owner_id == current_user.id:
        flash("You can't request your own service.", "error")
        return redirect(url_for("service_detail", service_id=service.id))

    existing = ExchangeRequest.query.filter(
        ExchangeRequest.service_id == service.id,
        ExchangeRequest.requester_id == current_user.id,
        ExchangeRequest.status.in_(["pending", "accepted"])
    ).first()

    if existing:
        flash("You already have an active request for this service.", "info")
        return redirect(url_for("exchanges"))

    if current_user.credits < service.duration_hours:
        flash(
            f"You need {service.duration_hours} credits for this service, but your wallet has {current_user.credits}.",
            "error"
        )
        return redirect(url_for("service_detail", service_id=service.id))

    message = request.form.get("message", "").strip()
    if not message:
        flash("Please add a short message with your request.", "error")
        return redirect(url_for("service_detail", service_id=service.id))

    exchange = ExchangeRequest(
        service_id=service.id,
        requester_id=current_user.id,
        provider_id=service.owner_id,
        message=message
    )
    db.session.add(exchange)
    db.session.commit()

    flash("Your request has been sent. You'll see updates in My Exchanges.", "success")
    return redirect(url_for("exchanges"))


@app.route("/exchanges")
@login_required
def exchanges():
    incoming = (
        ExchangeRequest.query.filter_by(provider_id=current_user.id)
        .order_by(ExchangeRequest.created_at.desc()).all()
    )
    outgoing = (
        ExchangeRequest.query.filter_by(requester_id=current_user.id)
        .order_by(ExchangeRequest.created_at.desc()).all()
    )
    return render_template("exchanges.html", incoming=incoming, outgoing=outgoing)


@app.route("/exchanges/<int:exchange_id>/<action>", methods=["POST"])
@login_required
def update_exchange(exchange_id, action):
    exchange = db.get_or_404(ExchangeRequest, exchange_id)

    if action in ("accept", "reject"):
        if exchange.provider_id != current_user.id:
            abort(403)
        if exchange.status != "pending":
            flash("This request has already been updated.", "info")
        else:
            exchange.status = "accepted" if action == "accept" else "rejected"
            db.session.commit()
            flash(
                "Request accepted. Once the service is complete, both of you can confirm it here."
                if action == "accept" else "Request declined.",
                "success" if action == "accept" else "info"
            )

    elif action == "cancel":
        if exchange.requester_id != current_user.id:
            abort(403)
        if exchange.status != "pending":
            flash("Only pending requests can be cancelled.", "info")
        else:
            exchange.status = "cancelled"
            db.session.commit()
            flash("Your request has been cancelled.", "info")

    elif action == "confirm":
        if current_user.id not in (exchange.requester_id, exchange.provider_id):
            abort(403)
        if exchange.status != "accepted":
            flash("Only accepted exchanges can be confirmed.", "info")
            return redirect(url_for("exchanges"))

        # If the other person has already confirmed, check the requester's
        # balance before recording the final confirmation and transferring credits.
        other_has_confirmed = (
            exchange.provider_confirmed if current_user.id == exchange.requester_id
            else exchange.requester_confirmed
        )
        cost = exchange.service.duration_hours
        if other_has_confirmed and exchange.requester.credits < cost:
            flash(
                f"This exchange cannot be completed yet: the requester needs {cost} credits but currently has {exchange.requester.credits}.",
                "error"
            )
            return redirect(url_for("exchanges"))

        if current_user.id == exchange.requester_id:
            exchange.requester_confirmed = True
        else:
            exchange.provider_confirmed = True

        if exchange.requester_confirmed and exchange.provider_confirmed:
            # The unique exchange_id on Transaction prevents a second transfer.
            existing_transaction = Transaction.query.filter_by(exchange_id=exchange.id).first()
            if not existing_transaction:
                exchange.requester.credits -= cost
                exchange.provider.credits += cost
                transaction = Transaction(
                    exchange_id=exchange.id,
                    from_user_id=exchange.requester_id,
                    to_user_id=exchange.provider_id,
                    credits=cost,
                    description=f"{exchange.service.title} ({cost} credit{'s' if cost != 1 else ''})"
                )
                db.session.add(transaction)
            exchange.status = "completed"
            exchange.completed_at = datetime.utcnow()
            db.session.commit()
            flash(f"Exchange completed! {cost} credit{'s' if cost != 1 else ''} transferred to {exchange.provider.name}.", "success")
        else:
            db.session.commit()
            flash("Your confirmation has been recorded. The exchange will complete once the other person confirms.", "success")

    else:
        abort(404)

    return redirect(url_for("exchanges"))


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


@app.route("/services/<int:service_id>/delete", methods=["POST"])
@login_required
def delete_service(service_id):
    service = db.get_or_404(Service, service_id)

    # Only the person who created the service can delete it.
    if service.owner_id != current_user.id:
        abort(403)

    if not service.is_active:
        flash("This service has already been removed.", "info")
        return redirect(url_for("dashboard"))

    # Cancel pending requests for this service.
    for exchange in service.exchange_requests:
        if exchange.status == "pending":
            exchange.status = "cancelled"

    # Archive the service instead of permanently deleting it.
    service.is_active = False

    db.session.commit()

    flash("Your service has been removed successfully.", "success")
    return redirect(url_for("dashboard"))


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


def migrate_day3_columns():
    """Add Day 3 confirmation fields to existing SQLite databases safely."""
    inspector = inspect(db.engine)
    if "exchange_request" not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("exchange_request")}
    migrations = {
        "requester_confirmed": "ALTER TABLE exchange_request ADD COLUMN requester_confirmed BOOLEAN NOT NULL DEFAULT 0",
        "provider_confirmed": "ALTER TABLE exchange_request ADD COLUMN provider_confirmed BOOLEAN NOT NULL DEFAULT 0",
        "completed_at": "ALTER TABLE exchange_request ADD COLUMN completed_at DATETIME",
    }
    with db.engine.begin() as connection:
        for column_name, statement in migrations.items():
            if column_name not in existing_columns:
                connection.execute(text(statement))


with app.app_context():
    db.create_all()
    migrate_day3_columns()


if __name__ == "__main__":
    app.run(debug=True)

