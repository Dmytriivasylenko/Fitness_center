from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Boolean
)
from sqlalchemy.orm import relationship, declarative_base
from flask_login import UserMixin

Base = declarative_base()

# ----------------- FITNESS CENTER ----------------- #
class FitnessCenter(Base):
    __tablename__ = "fitness_center"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=False)
    contacts = Column(String(100), nullable=False)

    trainers = relationship("Trainer", back_populates="fitness_center")
    services = relationship("Service", back_populates="fitness_center_rel")

    def __repr__(self):
        return f"<FitnessCenter {self.name}>"


# ----------------- TRAINER ----------------- #
from sqlalchemy import Boolean

class Trainer(Base):
    __tablename__ = "trainer"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)

    gym_id = Column(Integer, ForeignKey("fitness_center.id"), nullable=False)
    fitness_center = relationship("FitnessCenter", back_populates="trainers")

    is_active = Column(Boolean, default=True, nullable=False)

    reservations = relationship("Reservation", back_populates="trainer")

    def __repr__(self):
        return f"<Trainer {self.name}>"


# ----------------- USER ----------------- #
class User(UserMixin, Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    login = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    birth_date = Column(String, nullable=False)
    phone = Column(String(50), nullable=False)
    funds = Column(Integer, default=0)
    email = Column(String(150), nullable=False)
    transactions = relationship("Transaction", back_populates="user")

    # ROLE / STATUS
    is_admin = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)

    reservations = relationship("Reservation", back_populates="user")

    # Telegram
    telegram_id = Column(String, nullable=True)

    def __repr__(self):
        return f"<User {self.login}>"


# ----------------- SERVICE ----------------- #
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship


class Service(Base):
    __tablename__ = "service"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    duration = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)
    description = Column(String(255), nullable=False)
    category = Column(String, default="other")
    fitness_center_id = Column(Integer, ForeignKey("fitness_center.id"))
    fitness_center_rel = relationship("FitnessCenter", back_populates="services")

    # 👇 SOFT-DELETE FLAG (important!)
    is_active = Column(Boolean, default=True, nullable=False)

    reservations = relationship("Reservation", back_populates="service")

    def __repr__(self):
        return f"<Service {self.name}>"


# ----------------- RESERVATION ----------------- #
class Reservation(Base):
    __tablename__ = "reservation"

    id = Column(Integer, primary_key=True, autoincrement=True)

    trainer_id = Column(Integer, ForeignKey("trainer.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("service.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)

    date = Column(String, nullable=False)   # YYYY-MM-DD
    time = Column(String, nullable=False)   # HH:MM

    status = Column(String(20), nullable=False, default="active")
    # active | canceled | completed

    trainer = relationship("Trainer", back_populates="reservations")
    service = relationship("Service", back_populates="reservations")
    user = relationship("User", back_populates="reservations")

    def __repr__(self):
        return f"<Reservation {self.id}>"


# ----------------- REVIEW ----------------- #
class Review(Base):
    __tablename__ = "review"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trainer_id = Column(Integer, ForeignKey("trainer.id"), nullable=False)
    gym_id = Column(Integer, ForeignKey("fitness_center.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    review = Column(String(500), nullable=True)

    def __repr__(self):
        return f"<Review {self.id}>"


# ----------------- USER REGISTRATION LOG ----------------- #
class UserRegistrationLog(Base):
    __tablename__ = "user_registration_logs"

    id = Column(Integer, primary_key=True)
    login = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<UserRegistrationLog {self.login}>"


class Transaction(Base):
    __tablename__ = "transaction"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    amount = Column(Integer, nullable=False)   # + top-up / - deduction
    type = Column(String(20), nullable=False)  # payment / refund / topup
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="transactions")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    action = Column(String, nullable=False)
    entity = Column(String, nullable=False)
    entity_id = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<AuditLog {self.action} {self.entity}:{self.entity_id}>"
