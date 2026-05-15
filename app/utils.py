from __future__ import annotations

from datetime import datetime, UTC
from typing import Optional, Type, TypeVar

from werkzeug.security import check_password_hash

from app.database import db_session
from app.models import (
    Reservation,
    Service,
    Trainer,
    Transaction,
    User,
)
from app.tasks import (
    send_booking_canceled_email,
    send_booking_confirmation_email,
    send_booking_updated_email,
)

T = TypeVar("T")


def check_credentials(login: str, password: str) -> Optional[User]:
    user = db_session.query(User).filter_by(login=login).first()
    if user and check_password_hash(user.password, password):
        return user
    return None


def _get_entity(model: Type[T], pk: Optional[int]) -> Optional[T]:
    if pk is None:
        return None
    try:
        return db_session.get(model, pk)
    except AttributeError:
        return db_session.query(model).get(pk)


def charge_user(user: User, service: Service) -> None:
    """Deduct funds when booking."""
    user.funds -= service.price
    tx = Transaction(
        user_id=user.id,
        amount=-service.price,
        type="payment",
        created_at=datetime.now(UTC),
    )
    db_session.add(tx)


def refund_user(user: User, service: Service) -> None:
    """Return funds on cancellation."""
    user.funds += service.price
    tx = Transaction(
        user_id=user.id,
        amount=service.price,
        type="refund",
        created_at=datetime.now(UTC),
    )
    db_session.add(tx)


def has_time_conflict(
    trainer_id: int,
    date: str,
    time: str,
    exclude_reservation_id: Optional[int] = None,
) -> bool:
    """
    Returns True if the trainer already has an active reservation
    on the same date and time.
    exclude_reservation_id excludes the current record when rescheduling.
    """
    query = (
        db_session.query(Reservation)
        .filter(
            Reservation.trainer_id == trainer_id,
            Reservation.date == date,
            Reservation.time == time,
            Reservation.status != "cancelled",
        )
    )
    if exclude_reservation_id is not None:
        query = query.filter(Reservation.id != exclude_reservation_id)
    return query.first() is not None


def create_reservation(
    user_id: int,
    service_id: int,
    trainer_id: int,
    date: str,
    time: str,
) -> Optional[Reservation]:
    user    = _get_entity(User, user_id)
    trainer = _get_entity(Trainer, trainer_id)
    service = _get_entity(Service, service_id)

    if not user or not trainer or not service:
        return None
    if not trainer.is_active:
        return None
    if has_time_conflict(trainer_id, date, time):
        return None
    if user.funds < service.price:
        return None

    reservation = Reservation(
        trainer_id=trainer_id,
        service_id=service_id,
        user_id=user_id,
        date=date,
        time=time,
    )
    db_session.add(reservation)
    charge_user(user, service)
    db_session.commit()

    send_booking_confirmation_email(
        user.email, user.login, service.name, trainer.name, date, time,
    )
    return reservation


def update_reservation(
    reservation_id: int,
    user_id: int,
    new_date: str,
    new_time: str,
) -> Optional[Reservation]:
    reservation = (
        db_session.query(Reservation)
        .filter_by(id=reservation_id, user_id=user_id)
        .first()
    )
    if not reservation:
        return None
    if has_time_conflict(
        reservation.trainer_id, new_date, new_time,
        exclude_reservation_id=reservation_id,
    ):
        return None

    reservation.date = new_date
    reservation.time = new_time
    db_session.commit()

    user: User = reservation.user
    send_booking_updated_email(user.email, user.login, new_date, new_time)
    return reservation


def cancel_reservation(reservation_id: int, user_id: int) -> bool:
    reservation = (
        db_session.query(Reservation)
        .filter_by(id=reservation_id, user_id=user_id)
        .first()
    )
    if not reservation:
        return False

    reservation.status = "cancelled"
    user: User = reservation.user
    service: Service = reservation.service

    refund_user(user, service)
    db_session.commit()

    send_booking_canceled_email(user.email, user.login)
    return True
