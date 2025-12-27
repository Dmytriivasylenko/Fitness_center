# app/decorators.py

from functools import wraps
from flask import session, redirect, abort
from flask_login import current_user

from app import database
from app.models import User


def login_required(func):
    """
    Verifies that the user is authenticated.
    Works with session and Flask-Login.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect("/login")
        return func(*args, **kwargs)
    return wrapper


def admin_required(func):
    """
    Access restricted to administrators only.
    We check the user.is_admin field.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect("/login")

        # MAIN CHECK
        if not getattr(current_user, "is_admin", False):
            return abort(403)

        return func(*args, **kwargs)

    return wrapper
