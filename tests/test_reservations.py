from app.models import Reservation, User, Trainer, Service
from app import database

def test_create_reservation(client):
    session = database.db_session

    # підготуємо дані
    user = User(login="testuser", password="123", birth_date="2000-01-01", phone="000", email="a@a.com")
    trainer = Trainer(name="Test Trainer", gym_id=1)
    service = Service(name="Yoga", duration=60, price=100, description="x")

    session.add_all([user, trainer, service])
    session.commit()

    r = Reservation(
        user_id=user.id,
        trainer_id=trainer.id,
        service_id=service.id,
        date="2026-01-01",
        time="10:00",
        status="active"
    )

    session.add(r)
    session.commit()

    assert r.id is not None
