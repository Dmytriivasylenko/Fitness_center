from __future__ import annotations

import os
import stripe

from flask import Blueprint, render_template, request, redirect, flash
from flask_login import current_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from app import database
from app.config import settings
from app.models import Reservation, Transaction

profile_bp = Blueprint("profile", __name__)


# ──────────────────────────────────────────────────────
# PROFILE VIEW
# ──────────────────────────────────────────────────────

@profile_bp.route("/profile")
@login_required
def profile_page():
    reservations = (
        database.db_session.query(Reservation)
        .filter_by(user_id=current_user.id)
        .all()
    )
    return render_template(
        "profile/view.html",
        user=current_user,
        total_reservations=len(reservations),
        active="profile",
    )


# ──────────────────────────────────────────────────────
# EDIT PROFILE
# ──────────────────────────────────────────────────────

@profile_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        current_user.login      = request.form["login"]
        current_user.email      = request.form["email"]
        current_user.phone      = request.form["phone"]
        current_user.birth_date = request.form["birth_date"]
        database.db_session.commit()
        return redirect("/profile")

    return render_template("profile/edit.html", user=current_user, active="profile")


# ──────────────────────────────────────────────────────
# CHANGE PASSWORD
# ──────────────────────────────────────────────────────

@profile_bp.route("/profile/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        old_password     = request.form["old_password"]
        new_password     = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if not check_password_hash(current_user.password, old_password):
            return render_template(
                "profile/change_password.html",
                error="Old password is incorrect.",
                user=current_user,
                active="profile",
            )

        if new_password != confirm_password:
            return render_template(
                "profile/change_password.html",
                error="Passwords do not match.",
                user=current_user,
                active="profile",
            )

        if len(new_password) < 8:
            return render_template(
                "profile/change_password.html",
                error="New password must be at least 8 characters.",
                user=current_user,
                active="profile",
            )

        current_user.password = generate_password_hash(new_password)
        database.db_session.commit()

        flash("Password successfully updated!", "success")
        return redirect("/profile")

    return render_template(
        "profile/change_password.html",
        user=current_user,
        active="profile",
    )


# ──────────────────────────────────────────────────────
# UPLOAD AVATAR
# ──────────────────────────────────────────────────────

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@profile_bp.route("/profile/upload_photo", methods=["POST"])
@login_required
def upload_photo():
    if "avatar" not in request.files:
        return redirect("/profile/edit")

    file = request.files["avatar"]
    if file.filename == "":
        return redirect("/profile/edit")

    if not _allowed_file(file.filename):
        flash("Invalid file type. Allowed: png, jpg, jpeg, gif, webp.", "error")
        return redirect("/profile/edit")

    upload_folder = settings.upload_folder
    os.makedirs(upload_folder, exist_ok=True)

    filename = secure_filename(file.filename)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)

    current_user.avatar = f"/static/uploads/{filename}"
    database.db_session.commit()

    return redirect("/profile/edit")


# ──────────────────────────────────────────────────────
# ADD FUNDS PAGE
# ──────────────────────────────────────────────────────

@profile_bp.route("/profile/add_funds", methods=["GET"])
@login_required
def add_funds_page():
    return render_template(
        "profile/add_funds.html",
        user=current_user,
        active="profile",
        stripe_key=settings.stripe_public_key,   # ← was os.getenv() before
    )


# ──────────────────────────────────────────────────────
# STRIPE CHECKOUT SESSION
# ──────────────────────────────────────────────────────

@profile_bp.route("/create_checkout_session", methods=["POST"])
@login_required
def create_checkout_session():
    try:
        amount = int(request.form["amount"])
        if amount <= 0:
            flash("Amount must be greater than 0.", "error")
            return redirect("/profile/add_funds")
    except (ValueError, KeyError):
        flash("Invalid amount.", "error")
        return redirect("/profile/add_funds")

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": "Account Top-Up"},
                "unit_amount": amount * 100,   # dollars → cents
            },
            "quantity": 1,
        }],
        mode="payment",
        # Pass user_id in metadata so webhook can identify who paid
        metadata={"user_id": current_user.id, "amount": amount},
        success_url="http://localhost:5000/profile/payment_success?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="http://localhost:5000/profile/add_funds",
    )

    return redirect(checkout_session.url, code=303)


# ──────────────────────────────────────────────────────
# PAYMENT SUCCESS  ← FIXED: now verifies Stripe session
# ──────────────────────────────────────────────────────

@profile_bp.route("/profile/payment_success")
@login_required
def payment_success():
    session_id = request.args.get("session_id")

    if not session_id:
        flash("Invalid payment session.", "error")
        return redirect("/profile")

    try:
        # Verify payment with Stripe — cannot be faked
        checkout_session = stripe.checkout.Session.retrieve(session_id)

        if checkout_session.payment_status != "paid":
            flash("Payment not completed.", "error")
            return redirect("/profile/add_funds")

        # Prevent double top-up: check if this session was already processed
        existing = (
            database.db_session.query(Transaction)
            .filter_by(stripe_session_id=session_id)
            .first()
        )
        if existing:
            flash("This payment was already processed.", "warning")
            return redirect("/profile")

        amount = int(checkout_session.metadata.get("amount", 0))
        if amount <= 0:
            flash("Invalid payment amount.", "error")
            return redirect("/profile")

        # Top up balance
        current_user.funds += amount

        tx = Transaction(
            user_id=current_user.id,
            amount=amount,
            type="topup",
            stripe_session_id=session_id,
        )
        database.db_session.add(tx)
        database.db_session.commit()

        flash(f"Balance topped up by ${amount}!", "success")
        return redirect("/profile")

    except stripe.error.StripeError as e:
        flash(f"Payment verification failed: {str(e)}", "error")
        return redirect("/profile/add_funds")


# ──────────────────────────────────────────────────────
# TRANSACTIONS HISTORY
# ──────────────────────────────────────────────────────

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
        user=current_user,
    )


# ──────────────────────────────────────────────────────
# MANUAL PAYMENT (dev/test only)
# ──────────────────────────────────────────────────────

@profile_bp.route("/profile/payment/process", methods=["POST"])
@login_required
def process_payment():
    try:
        amount = int(request.form["amount"])
        if amount <= 0:
            raise ValueError
    except (ValueError, KeyError):
        flash("Invalid amount.", "error")
        return redirect("/profile")

    current_user.funds += amount

    tx = Transaction(
        user_id=current_user.id,
        amount=amount,
        type="topup",
    )
    database.db_session.add(tx)
    database.db_session.commit()

    flash(f"Payment successful! Balance updated by ${amount}.", "success")
    return redirect("/profile")
