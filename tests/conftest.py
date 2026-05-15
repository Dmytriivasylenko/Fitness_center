import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Set env vars BEFORE any app imports
os.environ["SECRET_KEY"] = "test-secret-key-32-chars-minimum!!"
os.environ["DATABASE_URL"] = "sqlite:///test.db"
os.environ["CELERY_BROKER_URL"] = "amqp://guest:guest@localhost:5672//"
os.environ["STRIPE_SECRET_KEY"] = "sk_test_placeholder"
os.environ["STRIPE_PUBLIC_KEY"] = "pk_test_placeholder"
os.environ["EMAIL_PASSWORD"] = "placeholder"
os.environ["MAIL_USERNAME"] = "test@example.com"

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import generate_password_hash

from app.models import Base, User, Trainer, Service, Reservation, FitnessCenter


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    Session = scoped_session(sessionmaker(bind=engine))
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def gym(db_session):
    center = FitnessCenter(name="Test Gym", address="Test St 1", contacts="000")
    db_session.add(center)
    db_session.commit()
    return center


@pytest.fixture
def trainer(db_session, gym):
    t = Trainer(name="Ivan Trainer", gym_id=gym.id, is_active=True)
    db_session.add(t)
    db_session.commit()
    return t


@pytest.fixture
def inactive_trainer(db_session, gym):
    t = Trainer(name="Inactive Trainer", gym_id=gym.id, is_active=False)
    db_session.add(t)
    db_session.commit()
    return t


@pytest.fixture
def service(db_session, gym):
    s = Service(
        name="Yoga",
        duration=60,
        price=200,
        description="Morning yoga",
        fitness_center_id=gym.id,
        is_active=True,
    )
    db_session.add(s)
    db_session.commit()
    return s


@pytest.fixture
def user(db_session):
    u = User(
        login="testuser",
        password=generate_password_hash("password123"),
        phone="0501234567",
        email="test@example.com",
        birth_date="1990-01-01",
        funds=1000,
        is_admin=False,
        is_banned=False,
    )
    db_session.add(u)
    db_session.commit()
    return u


@pytest.fixture
def poor_user(db_session):
    u = User(
        login="pooruser",
        password=generate_password_hash("password123"),
        phone="0507654321",
        email="poor@example.com",
        birth_date="1995-05-05",
        funds=50,
        is_admin=False,
        is_banned=False,
    )
    db_session.add(u)
    db_session.commit()
    return u


@pytest.fixture
def reservation(db_session, user, trainer, service):
    r = Reservation(
        trainer_id=trainer.id,
        service_id=service.id,
        user_id=user.id,
        date="2025-12-01",
        time="10:00",
        status="active",
    )
    db_session.add(r)
    db_session.commit()
    return r

@pytest.fixture
def client(db_session, monkeypatch):
    import app.database as db_module
    monkeypatch.setattr(db_module, "db_session", db_session)

    from app.app import app as flask_app
    flask_app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )
    with flask_app.test_client() as c:
        yield c