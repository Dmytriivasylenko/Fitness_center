from flask import Blueprint, render_template, request, redirect
from flask_login import login_required, current_user
from app import database
from app.models import Service, Trainer
from app.utils import create_reservation

services_bp = Blueprint("services", __name__)

@services_bp.route("/services")
@login_required
def services_page():
    category = request.args.get("category", "all")
    sort_by = request.args.get("sort", "name")  # new sorting parameter

    query = database.db_session.query(Service)

    # Filter by category
    if category != "all":
        query = query.filter(Service.category == category)

    # Sorting
    if sort_by == "price":
        query = query.order_by(Service.price)
    elif sort_by == "duration":
        query = query.order_by(Service.duration)
    else:
        query = query.order_by(Service.name)

    services_list = query.all()
    categories = ["all", "strength", "cardio", "wellness", "other"]

    return render_template(
        "services/list.html",
        services=services_list,
        category=category,
        categories=categories,
        sort_by=sort_by,
        active="services",
        user=current_user
    )

@services_bp.route("/services/<int:service_id>")
@login_required
def service_details(service_id):
    service = database.db_session.get(Service, service_id)
    if not service:
        return "Service not found", 404

    trainers = database.db_session.query(Trainer).filter_by(gym_id=service.fitness_center_id).all()

    return render_template(
        "services/detail.html",
        service=service,
        trainers=trainers,
        active="services",
        user=current_user
    )

@services_bp.route("/book/<int:service_id>", methods=["GET", "POST"])
@login_required
def book_service(service_id):
    service = database.db_session.get(Service, service_id)
    if not service:
        return "Service not found", 404

    trainers = (
        database.db_session.query(Trainer)
        .filter_by(gym_id=service.fitness_center_id)
        .all()
    )

    if request.method == "POST":
        user = current_user

        # Check funds
        if user.funds < service.price:
            return render_template(
                "services/book.html",
                service=service,
                trainers=trainers,
                user=user,
                error="❗ Insufficient funds. Please top up your balance."
            )

        # deduct funds
        user.funds -= service.price

        create_reservation(
            user_id=user.id,
            service_id=service.id,
            trainer_id=int(request.form["trainer_id"]),
            date=request.form["date"],
            time=request.form["time"],
        )

        database.db_session.commit()

        return redirect("/reservations")

    return render_template(
        "services/book.html",
        service=service,
        trainers=trainers,
        user=current_user
    )
