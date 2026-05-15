"""
tests/test_utils.py

Тести для:
  - create_reservation  (конфлікт часу, баланс, неактивний тренер)
  - cancel_reservation  (soft-delete, повернення коштів)
  - update_reservation  (reschedule без конфлікту)
  - check_credentials   (логін / неправильний пароль)
  - _validate_register_form (валідація email, пароль, логін)
"""
import pytest
from unittest.mock import patch, MagicMock

from app.utils import (
    create_reservation,
    cancel_reservation,
    update_reservation,
    check_credentials,
    has_time_conflict,
)
from app.routes.auth import _validate_register_form
from app.models import Reservation, User


# ══════════════════════════════════════════════════════
# CREATE RESERVATION
# ══════════════════════════════════════════════════════

class TestCreateReservation:

    @patch("app.utils.send_booking_confirmation_email")
    def test_creates_successfully(
        self, mock_email, db_session, user, trainer, service, monkeypatch
    ):
        """Успішне бронювання списує кошти і повертає об'єкт."""
        monkeypatch.setattr("app.utils.db_session", db_session)

        initial_funds = user.funds

        result = create_reservation(
            user_id=user.id,
            service_id=service.id,
            trainer_id=trainer.id,
            date="2025-12-10",
            time="09:00",
        )

        assert result is not None
        assert result.status == "active"
        assert user.funds == initial_funds - service.price
        mock_email.assert_called_once()

    @patch("app.utils.send_booking_confirmation_email")
    def test_conflict_returns_none(
        self, mock_email, db_session, user, trainer, service,
        reservation, monkeypatch
    ):
        """
        Якщо тренер вже зайнятий — повертає None, не надсилає email.
        reservation fixture вже займає trainer на 2025-12-01 10:00.
        """
        monkeypatch.setattr("app.utils.db_session", db_session)

        result = create_reservation(
            user_id=user.id,
            service_id=service.id,
            trainer_id=trainer.id,
            date="2025-12-01",   # та сама дата
            time="10:00",        # той самий час
        )

        assert result is None
        mock_email.assert_not_called()

    @patch("app.utils.send_booking_confirmation_email")
    def test_insufficient_funds_returns_none(
        self, mock_email, db_session, poor_user, trainer, service, monkeypatch
    ):
        """Якщо коштів не вистачає — повертає None."""
        monkeypatch.setattr("app.utils.db_session", db_session)

        result = create_reservation(
            user_id=poor_user.id,
            service_id=service.id,
            trainer_id=trainer.id,
            date="2025-12-15",
            time="11:00",
        )

        assert result is None
        mock_email.assert_not_called()

    @patch("app.utils.send_booking_confirmation_email")
    def test_inactive_trainer_returns_none(
        self, mock_email, db_session, user, inactive_trainer, service, monkeypatch
    ):
        """Якщо тренер неактивний — бронювання неможливе."""
        monkeypatch.setattr("app.utils.db_session", db_session)

        result = create_reservation(
            user_id=user.id,
            service_id=service.id,
            trainer_id=inactive_trainer.id,
            date="2025-12-20",
            time="14:00",
        )

        assert result is None
        mock_email.assert_not_called()

    @patch("app.utils.send_booking_confirmation_email")
    def test_different_time_no_conflict(
        self, mock_email, db_session, user, trainer, service,
        reservation, monkeypatch
    ):
        """Той самий тренер і день, але інший час — дозволено."""
        monkeypatch.setattr("app.utils.db_session", db_session)

        result = create_reservation(
            user_id=user.id,
            service_id=service.id,
            trainer_id=trainer.id,
            date="2025-12-01",
            time="12:00",   # інший час
        )

        assert result is not None


# ══════════════════════════════════════════════════════
# CANCEL RESERVATION
# ══════════════════════════════════════════════════════

class TestCancelReservation:

    @patch("app.utils.send_booking_canceled_email")
    def test_soft_delete_sets_cancelled_status(
        self, mock_email, db_session, reservation, user, monkeypatch
    ):
        """
        Скасування НЕ видаляє запис — змінює статус на 'cancelled'.
        """
        monkeypatch.setattr("app.utils.db_session", db_session)

        result = cancel_reservation(reservation.id, user.id)

        assert result is True

        # Запис ще є в БД
        still_exists = db_session.get(Reservation, reservation.id)
        assert still_exists is not None
        assert still_exists.status == "cancelled"

    @patch("app.utils.send_booking_canceled_email")
    def test_refund_on_cancellation(
        self, mock_email, db_session, reservation, user, service, monkeypatch
    ):
        """Кошти повертаються після скасування."""
        monkeypatch.setattr("app.utils.db_session", db_session)

        funds_before = user.funds

        cancel_reservation(reservation.id, user.id)

        assert user.funds == funds_before + service.price

    @patch("app.utils.send_booking_canceled_email")
    def test_email_sent_on_cancel(
        self, mock_email, db_session, reservation, user, monkeypatch
    ):
        """Email надсилається після скасування."""
        monkeypatch.setattr("app.utils.db_session", db_session)

        cancel_reservation(reservation.id, user.id)

        mock_email.assert_called_once_with(user.email, user.login)

    @patch("app.utils.send_booking_canceled_email")
    def test_wrong_user_cannot_cancel(
        self, mock_email, db_session, reservation, monkeypatch
    ):
        """Інший користувач не може скасувати чуже бронювання."""
        monkeypatch.setattr("app.utils.db_session", db_session)

        result = cancel_reservation(reservation.id, user_id=99999)

        assert result is False
        assert reservation.status == "active"
        mock_email.assert_not_called()

    @patch("app.utils.send_booking_canceled_email")
    def test_nonexistent_reservation_returns_false(
        self, mock_email, db_session, user, monkeypatch
    ):
        """Повертає False для неіснуючого id."""
        monkeypatch.setattr("app.utils.db_session", db_session)

        result = cancel_reservation(99999, user.id)

        assert result is False


# ══════════════════════════════════════════════════════
# UPDATE RESERVATION
# ══════════════════════════════════════════════════════

class TestUpdateReservation:

    @patch("app.utils.send_booking_updated_email")
    def test_reschedule_success(
        self, mock_email, db_session, reservation, user, monkeypatch
    ):
        """Успішний перенос на вільний час."""
        monkeypatch.setattr("app.utils.db_session", db_session)

        result = update_reservation(
            reservation_id=reservation.id,
            user_id=user.id,
            new_date="2025-12-02",
            new_time="15:00",
        )

        assert result is not None
        assert result.date == "2025-12-02"
        assert result.time == "15:00"
        mock_email.assert_called_once()

    @patch("app.utils.send_booking_updated_email")
    def test_reschedule_to_same_slot_allowed(
        self, mock_email, db_session, reservation, user, monkeypatch
    ):
        """
        Перенос на той самий час — дозволений
        (exclude_reservation_id виключає власний запис).
        """
        monkeypatch.setattr("app.utils.db_session", db_session)

        result = update_reservation(
            reservation_id=reservation.id,
            user_id=user.id,
            new_date=reservation.date,
            new_time=reservation.time,
        )

        assert result is not None

    @patch("app.utils.send_booking_updated_email")
    def test_reschedule_conflict_returns_none(
        self, mock_email, db_session, user, trainer, service,
        reservation, monkeypatch
    ):
        """Перенос на зайнятий час — неможливий."""
        monkeypatch.setattr("app.utils.db_session", db_session)

        # Створюємо другу бронь на той час куди хочемо перенести
        r2 = Reservation(
            trainer_id=trainer.id,
            service_id=service.id,
            user_id=user.id,
            date="2025-12-05",
            time="16:00",
            status="active",
        )
        db_session.add(r2)
        db_session.commit()

        result = update_reservation(
            reservation_id=reservation.id,
            user_id=user.id,
            new_date="2025-12-05",
            new_time="16:00",   # зайнято r2
        )

        assert result is None
        mock_email.assert_not_called()


# ══════════════════════════════════════════════════════
# HAS TIME CONFLICT
# ══════════════════════════════════════════════════════

class TestHasTimeConflict:

    def test_detects_conflict(self, db_session, reservation, monkeypatch):
        monkeypatch.setattr("app.utils.db_session", db_session)

        conflict = has_time_conflict(
            trainer_id=reservation.trainer_id,
            date=reservation.date,
            time=reservation.time,
        )

        assert conflict is True

    def test_no_conflict_different_time(self, db_session, reservation, monkeypatch):
        monkeypatch.setattr("app.utils.db_session", db_session)

        conflict = has_time_conflict(
            trainer_id=reservation.trainer_id,
            date=reservation.date,
            time="23:00",
        )

        assert conflict is False

    def test_cancelled_reservation_not_a_conflict(
        self, db_session, reservation, monkeypatch
    ):
        """Скасоване бронювання не вважається конфліктом."""
        monkeypatch.setattr("app.utils.db_session", db_session)

        reservation.status = "cancelled"
        db_session.commit()

        conflict = has_time_conflict(
            trainer_id=reservation.trainer_id,
            date=reservation.date,
            time=reservation.time,
        )

        assert conflict is False


# ══════════════════════════════════════════════════════
# CHECK CREDENTIALS
# ══════════════════════════════════════════════════════

class TestCheckCredentials:

    def test_valid_credentials(self, db_session, user, monkeypatch):
        monkeypatch.setattr("app.utils.db_session", db_session)

        result = check_credentials("testuser", "password123")

        assert result is not None
        assert result.id == user.id

    def test_wrong_password(self, db_session, user, monkeypatch):
        monkeypatch.setattr("app.utils.db_session", db_session)

        result = check_credentials("testuser", "wrongpassword")

        assert result is None

    def test_nonexistent_user(self, db_session, monkeypatch):
        monkeypatch.setattr("app.utils.db_session", db_session)

        result = check_credentials("ghost", "anypassword")

        assert result is None


# ══════════════════════════════════════════════════════
# REGISTER FORM VALIDATION
# ══════════════════════════════════════════════════════

class TestValidateRegisterForm:

    def test_valid_form_no_errors(self):
        form = {
            "login": "dmytro",
            "email": "dmytro@example.com",
            "password": "securepass",
            "phone": "0501234567",
        }
        errors = _validate_register_form(form)
        assert errors == []

    def test_short_login(self):
        form = {
            "login": "ab",          # < 3 символи
            "email": "a@b.com",
            "password": "securepass",
            "phone": "0501234567",
        }
        errors = _validate_register_form(form)
        assert any("Login" in e for e in errors)

    def test_invalid_email(self):
        form = {
            "login": "dmytro",
            "email": "not-an-email",
            "password": "securepass",
            "phone": "0501234567",
        }
        errors = _validate_register_form(form)
        assert any("email" in e.lower() for e in errors)

    def test_short_password(self):
        form = {
            "login": "dmytro",
            "email": "d@example.com",
            "password": "short",    # < 8 символів
            "phone": "0501234567",
        }
        errors = _validate_register_form(form)
        assert any("Password" in e for e in errors)

    def test_missing_phone(self):
        form = {
            "login": "dmytro",
            "email": "d@example.com",
            "password": "securepass",
            "phone": "",
        }
        errors = _validate_register_form(form)
        assert any("Phone" in e for e in errors)

    def test_multiple_errors(self):
        form = {
            "login": "x",
            "email": "bad",
            "password": "123",
            "phone": "",
        }
        errors = _validate_register_form(form)
        assert len(errors) == 4
