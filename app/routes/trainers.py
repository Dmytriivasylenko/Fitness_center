from flask import Blueprint, render_template
from app import database
from app.models import Trainer, Service
from app.decorators import login_required

trainers_bp = Blueprint("trainers", __name__)

@trainers_bp.route("/trainers")
@login_required
def trainers_page():
    trainers = database.db_session.query(Trainer).all()

    return render_template(
        "trainers/list.html",
        trainers=trainers,
        active="trainers"
    )

@trainers_bp.route("/trainers/<int:trainer_id>")
@login_required
def trainer_profile(trainer_id):
    trainer = database.db_session.get(Trainer, trainer_id)
    if not trainer:
        return "Trainer not found", 404

    services = (
        database.db_session.query(Service)
        .filter_by(fitness_center_id=trainer.gym_id)
        .all()
    )

    return render_template(
        "trainers/profile.html",
        trainer=trainer,
        services=services,
        active="trainers"
    )
