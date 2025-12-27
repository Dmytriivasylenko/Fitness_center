import stripe
from flask import Blueprint, render_template, request, redirect, flash
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
import os
from flask_login import current_user, login_required

from app import database
from app.models import User, Reservation, Transaction

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile")
@login_required
def profile_page():
    user = current_user

    reservations = (
        database.db_session.query(Reservation)
        .filter_by(user_id=user.id)
        .all()
    )

    total_reservations = len(reservations)

    return render_template(
        "profile/view.html",
        user=user,
        total_reservations=total_reservations,
        active="profile"
    )


@profile_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    user = current_user

    if request.method == "POST":
        user.login = request.form["login"]
        user.email = request.form["email"]
        user.phone = request.form["phone"]
        user.birth_date = request.form["birth_date"]

        database.db_session.commit()
        return redirect("/profile")

    return render_template(
        "profile/edit.html",
        user=user,
        active="profile"
    )


@profile_bp.route("/profile/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    user = current_user

    if request.method == "POST":
        old_password = request.form["old_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        # 🔐 verify old password hash
        if not check_password_hash(user.password, old_password):
            return render_template(
                "profile/change_password.html",
                error="Old password is incorrect.",
                user=user,
                active="profile"
            )

        if new_password != confirm_password:
            return render_template(
                "profile/change_password.html",
                error="Passwords do not match.",
                user=user,
                active="profile"
            )

        # 🔐 save NEW password as hash
        user.password = generate_password_hash(new_password)
        database.db_session.commit()

        flash("Password successfully updated!", "success")
        return redirect("/profile")

    return render_template(
        "profile/change_password.html",
        user=user,
        active="profile"
    )


@profile_bp.route("/profile/upload_photo", methods=["POST"])
@login_required
def upload_photo():
    user = current_user

    if "avatar" not in request.files:
        return redirect("/profile/edit")

    file = request.files["avatar"]
    if file.filename == "":
        return redirect("/profile/edit")

    upload_folder = "app/static/uploads"
    os.makedirs(upload_folder, exist_ok=True)

    filename = secure_filename(file.filename)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)

    user.avatar = f"/static/uploads/{filename}"
    database.db_session.commit()

    return redirect("/profile/edit")


from flask import flash, request, redirect, render_template, url_for

@profile_bp.route("/profile/add_funds", methods=["GET"])
@login_required
def add_funds_page():
    return render_template(
        "profile/add_funds.html",
        user=current_user,
        active="profile",
        stripe_key=os.getenv("STRIPE_PUBLISHABLE_KEY")
    )


@profile_bp.route("/create_checkout_session", methods=["POST"])
@login_required
def create_checkout_session():
    amount = int(request.form["amount"]) * 100   # $ → cents

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": "Account Top-Up"},
                "unit_amount": amount,
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url="http://localhost:5000/profile/payment_success?amount=" + request.form["amount"],
        cancel_url="http://localhost:5000/profile/add_funds",
    )

    return redirect(session.url, code=303)


@profile_bp.route("/profile/payment_success")
@login_required
def payment_success():
    amount = float(request.args.get("amount", 0))

    current_user.funds += amount
    database.db_session.commit()

    flash(f"Balance topped-up by ${amount}", "success")
    return redirect("/profile")


@profile_bp.route("/profile/payment")
@login_required
def payment_page():
    amount = request.args.get("amount")

    return render_template(
        "profile/payment.html",
        amount=amount,
        active="profile"
    )


@profile_bp.route("/profile/transactions")
@login_required
def transactions_page():
    transactions = (
        database.db_session.query(Transaction)
        .filter_by(user_id=current_user.id)
        .order_by(Transaction.created_at.desc())
        .all()
    )

    return render_template(
        "profile/transactions.html",
        transactions=transactions,
        active="profile",
        user=current_user
    )


@profile_bp.route("/profile/payment/process", methods=["POST"])
@login_required
def process_payment():
    amount = int(request.form["amount"])

    # here we simulate a call to a payment system
    print("PAYMENT SUCCESS:", amount)

    # update balance
    current_user.funds += amount

    tx = Transaction(
        user_id=current_user.id,
        amount=amount,
        type="topup"
    )

    database.db_session.add(tx)
    database.db_session.commit()

    flash("Payment successful! Balance updated.", "success")

    return redirect("/profile")
