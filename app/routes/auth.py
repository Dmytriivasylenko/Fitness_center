import re

from flask import Blueprint, render_template, request, redirect, session, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash

from app import database
from app.models import User, UserRegistrationLog
from app.utils import check_credentials
from app.tasks import send_welcome_email, send_admin_new_user_email

auth_bp = Blueprint("auth", __name__)

#Validaation new function

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

#Returns a list of errors or an empty list if everything is ok
def _validate_register_form(form):
    errors = []

    login    = form.get("login", "").strip()
    email    = form.get("email", "").strip()
    password = form.get("password", "")
    phone    = form.get("phone", "").strip()

    if len(login) < 3:
        errors.append("Login must be at least 3 characters.")

    if not EMAIL_RE.match(email):
        errors.append("Invalid email address.")

    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")

    if not phone:
        errors.append("Phone number is required.")

    return errors


#Register
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        form = request.form

        # validation
        errors = _validate_register_form(form)
        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("auth/register.html")

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


#Login
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = check_credentials(
            request.form["login"],
            request.form["password"],
        )

        if user:
            if user.is_banned:
                flash("Your account has been banned.", "error")
                return render_template("auth/login.html")

            session["user_id"] = user.id
            login_user(user)
            return redirect("/user")

        flash("Invalid credentials", "error")

    return render_template("auth/login.html")


#Logout
@auth_bp.route("/logout")
@login_required
def logout():
    session.pop("user_id", None)
    logout_user()
    return redirect("/")
