from flask import Blueprint, render_template, redirect, request, abort
from datetime import datetime
from flask_login import login_required, current_user

from app import database
from app.models import Reservation
from app.utils import update_reservation, cancel_reservation

reservations_bp = Blueprint("reservations", __name__)

@reservations_bp.route("/reservations")
@login_required
def reservations_page():
    today = datetime.now().date()

    reservations = (
        database.db_session.query(Reservation)
        .filter_by(user_id=current_user.id)
        .order_by(Reservation.date, Reservation.time)
        .all()
    )

    upcoming = []
    today_list = []
    past = []
    canceled = []

    for r in reservations:
        r_dt = datetime.strptime(f"{r.date} {r.time}", "%Y-%m-%d %H:%M")
        r.is_canceled = getattr(r, "canceled", False)
        r.is_today = r_dt.date() == today
        r.is_past = r_dt.date() < today

        if r.is_canceled:
            canceled.append(r)
        elif r.is_today:
            today_list.append(r)
        elif r.is_past:
            past.append(r)
        else:
            upcoming.append(r)

    return render_template(
        "reservations/index.html",
        upcoming=upcoming,
        today=today_list,
        past=past,
        canceled=canceled,
        active="reservations",
        user=current_user
    )

@reservations_bp.route("/reservation/<int:reservation_id>/cancel", methods=["POST"])
@login_required
def cancel_reservation_route(reservation_id):
    cancel_reservation(reservation_id, current_user.id)
    return redirect("/reservations")

@reservations_bp.route("/reservation/<int:reservation_id>/edit", methods=["GET", "POST"])
@login_required
def edit_reservation_route(reservation_id):
    reservation = (
        database.db_session.query(Reservation)
        .filter_by(id=reservation_id, user_id=current_user.id)
        .first()
    )

    if not reservation:
        return abort(404)

    if request.method == "POST":
        new_date = request.form["date"]
        new_time = request.form["time"]
        update_reservation(reservation_id, current_user.id, new_date, new_time)
        return redirect("/reservations")

    return render_template(
        "reservations/edit.html",
        reservation=reservation,
        active="reservations",
        user=current_user
    )
