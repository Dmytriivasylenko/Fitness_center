from flask import Blueprint, render_template
from datetime import datetime, timedelta
import json

from flask_login import login_required, current_user

from app import database
from app.models import Reservation

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/user")
@login_required
def user_dashboard():
    #Flask-Login user
    user = current_user

    reservations = (
        database.db_session.query(Reservation)
        .filter_by(user_id=user.id)
        .order_by(Reservation.date, Reservation.time)
        .all()
    )

    now = datetime.now()

    for r in reservations:
        r.dt = datetime.strptime(f"{r.date} {r.time}", "%Y-%m-%d %H:%M")
        r.is_past = r.dt < now
        r.is_canceled = (r.status == "canceled")

    upcoming = [r for r in reservations if not r.is_past and not r.is_canceled]
    next_reservation = min(upcoming, key=lambda r: r.dt) if upcoming else None

    recent_reservations = sorted(reservations, key=lambda r: r.dt, reverse=True)[:3]

    total_reservations = len(reservations)
    completed_reservations = len(
        [r for r in reservations if r.is_past and not r.is_canceled]
    )
    canceled_reservations = len(
        [r for r in reservations if r.is_canceled]
    )

    total_spent = sum((r.service.price or 0) for r in reservations)

    # ----------- CHART DATA -----------
    start_date = now.date() - timedelta(days=6)
    counts_by_day = {
        (start_date + timedelta(days=i)).strftime("%Y-%m-%d"): 0
        for i in range(7)
    }

    for r in reservations:
        if r.date in counts_by_day:
            counts_by_day[r.date] += 1

    chart_data = json.dumps({
        "labels": list(counts_by_day.keys()),
        "values": list(counts_by_day.values())
    })

    # ----------- RECOMMENDATIONS -----------
    recommendations = []

    if not upcoming:
        recommendations.append("You have no upcoming sessions. Book a new training.")
    if (user.funds or 0) < 20:
        recommendations.append("Your balance is getting low.")
    if total_reservations >= 5 and completed_reservations == total_reservations:
        recommendations.append("Great consistency!")

    if not recommendations:
        recommendations.append("Keep it up! Explore new services.")

    return render_template(
        "dashboard/index.html",
        user=user,
        total_reservations=total_reservations,
        total_spent=total_spent,
        completed_reservations=completed_reservations,
        canceled_reservations=canceled_reservations,
        next_reservation=next_reservation,
        recent_reservations=recent_reservations,
        chart_data=chart_data,
        recommendations=recommendations,
        active="dashboard",
        breadcrumbs=[
            {"label": "Dashboard"}
        ]
    )
