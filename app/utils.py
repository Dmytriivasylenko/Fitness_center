from datetime import datetime

from werkzeug.security import check_password_hash

from app.database import db_session
from app import database
from app.models import (
    User,
    Trainer,
    Service,
    Reservation,
    Transaction,
)

from app.tasks import (
    send_booking_confirmation_email,
    send_booking_updated_email,
    send_booking_canceled_email,
)


# -------------------------- AUTH CHECK -----------------------------
def check_credentials(login, password):
    user = (
        database.db_session.query(User)
        .filter_by(login=login)
        .first()
    )

    if user and check_password_hash(user.password, password):
        return user

    return None


# ----------------------- SAFE GET ---------------------------------
def _get_entity(model, pk):
    if pk is None:
        return None

    try:
        return db_session.get(model, pk)
    except AttributeError:
        return db_session.query(model).get(pk)


# ----------------------- PAYMENTS ---------------------------------
def charge_user(user, service):
    """ deduct funds when booking """
    user.funds -= service.price

    tx = Transaction(
        user_id=user.id,
        amount=-service.price,
        type="payment",
        created_at=datetime.utcnow()
    )

    db_session.add(tx)


def refund_user(user, service):
    """ return funds on cancellation """
    user.funds += service.price

    tx = Transaction(
        user_id=user.id,
        amount=service.price,
        type="refund",
        created_at=datetime.utcnow()
    )

    db_session.add(tx)


# ----------------------- CREATE RESERVATION ------------------------
def create_reservation(user_id, service_id, trainer_id, date, time):
    user = _get_entity(User, user_id)
    trainer = _get_entity(Trainer, trainer_id)
    service = _get_entity(Service, service_id)

    if not user or not trainer or not service:
        return None

    reservation = Reservation(
        trainer_id=trainer_id,
        service_id=service_id,
        user_id=user_id,
        date=date,
        time=time,
    )

    db_session.add(reservation)

    # 💳 deduct funds
    charge_user(user, service)

    db_session.commit()

    send_booking_confirmation_email(
        user.email,
        user.login,
        service.name,
        trainer.name,
        date,
        time,
    )

    return reservation


# ----------------------- UPDATE RESERVATION ------------------------
def update_reservation(reservation_id, user_id, new_date, new_time):
    reservation = (
        db_session.query(Reservation)
        .filter_by(id=reservation_id, user_id=user_id)
        .first()
    )

    if not reservation:
        return None

    reservation.date = new_date
    reservation.time = new_time

    db_session.commit()

    user = reservation.user

    send_booking_updated_email(
        user.email,
        user.login,
        new_date,
        new_time,
    )

    return reservation


# ----------------------- CANCEL RESERVATION ------------------------
def cancel_reservation(reservation_id, user_id):
    reservation = (
        db_session.query(Reservation)
        .filter_by(id=reservation_id, user_id=user_id)
        .first()
    )

    if not reservation:
        return False

    user = reservation.user
    service = reservation.service

    # ♻️ refund funds
    refund_user(user, service)

    db_session.delete(reservation)
    db_session.commit()

    send_booking_canceled_email(
        user.email,
        user.login,
    )

    return True
