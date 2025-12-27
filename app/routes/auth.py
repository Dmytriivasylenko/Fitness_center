# app/routes/auth.py

from flask import Blueprint, render_template, request, redirect, session, flash
from flask_login import login_user, logout_user, login_required
from app import database
from app.models import User, UserRegistrationLog
from app.utils import check_credentials
from app.tasks import send_welcome_email, send_admin_new_user_email
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        form = request.form

        hashed_password = generate_password_hash(form["password"])

        new_user = User(
            login=form["login"],
            password=hashed_password,
            birth_date=form["birth_date"],
            phone=form["phone"],
            email=form["email"],
        )

        database.db_session.add(new_user)
        database.db_session.commit()

        log = UserRegistrationLog(
            login=new_user.login,
            email=new_user.email,
            phone=new_user.phone,
        )
        database.db_session.add(log)
        database.db_session.commit()

        send_welcome_email(
            new_user.email,
            new_user.login,
            "http://localhost:5000/login",
        )

        send_admin_new_user_email(
            new_user.login,
            new_user.email,
            new_user.phone,
        )

        return redirect("/registration_success")

    return render_template("auth/register.html")


@auth_bp.route("/registration_success")
def registration_success():
    return render_template("auth/registration_success.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = check_credentials(
            request.form["login"],
            request.form["password"]
        )

        if user:
            # 🔹 Save user_id for our custom decorator
            session["user_id"] = user.id
            # 🔹 Flask-Login
            login_user(user)
            return redirect("/user")

        flash("Invalid credentials", "error")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    # 🔹 Clear session and Flask-Login
    session.pop("user_id", None)
    logout_user()
    return redirect("/")
