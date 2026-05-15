from __future__ import annotations

from datetime import datetime
from typing import Optional

from flask_login import UserMixin
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship


class Base(DeclarativeBase):
    pass


class FitnessCenter(Base):
    __tablename__ = "fitness_center"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = Column(String(100), nullable=False)
    address: Mapped[str] = Column(String(255), nullable=False)
    contacts: Mapped[str] = Column(String(100), nullable=False)

    trainers: Mapped[list[Trainer]] = relationship("Trainer", back_populates="fitness_center")
    services: Mapped[list[Service]] = relationship("Service", back_populates="fitness_center_rel")

    def __repr__(self) -> str:
        return f"<FitnessCenter {self.name}>"


class Trainer(Base):
    __tablename__ = "trainer"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = Column(String, nullable=False)
    gym_id: Mapped[int] = Column(Integer, ForeignKey("fitness_center.id"), nullable=False)
    is_active: Mapped[bool] = Column(Boolean, default=True, nullable=False)

    fitness_center: Mapped[FitnessCenter] = relationship("FitnessCenter", back_populates="trainers")
    reservations: Mapped[list[Reservation]] = relationship("Reservation", back_populates="trainer")

    def __repr__(self) -> str:
        return f"<Trainer {self.name}>"



class User(UserMixin, Base):
    __tablename__ = "user"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    login: Mapped[str] = Column(String(50), unique=True, nullable=False)
    password: Mapped[str] = Column(String(255), nullable=False)
    birth_date: Mapped[str] = Column(String, nullable=False)
    phone: Mapped[str] = Column(String(50), nullable=False)
    email: Mapped[str] = Column(String(150), nullable=False)
    funds: Mapped[int] = Column(Integer, default=0)
    is_admin: Mapped[bool] = Column(Boolean, default=False)
    is_banned: Mapped[bool] = Column(Boolean, default=False)
    telegram_id: Mapped[Optional[str]] = Column(String, nullable=True)

    reservations: Mapped[list[Reservation]] = relationship("Reservation", back_populates="user")
    transactions: Mapped[list[Transaction]] = relationship("Transaction", back_populates="user")

    def __repr__(self) -> str:
        return f"<User {self.login}>"



class Service(Base):
    __tablename__ = "service"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = Column(String(50), nullable=False)
    duration: Mapped[int] = Column(Integer, nullable=False)
    price: Mapped[int] = Column(Integer, nullable=False)
    description: Mapped[str] = Column(String(255), nullable=False)
    category: Mapped[str] = Column(String, default="other")
    fitness_center_id: Mapped[int] = Column(Integer, ForeignKey("fitness_center.id"))
    is_active: Mapped[bool] = Column(Boolean, default=True, nullable=False)

    fitness_center_rel: Mapped[FitnessCenter] = relationship("FitnessCenter", back_populates="services")
    reservations: Mapped[list[Reservation]] = relationship("Reservation", back_populates="service")

    def __repr__(self) -> str:
        return f"<Service {self.name}>"



class Reservation(Base):
    __tablename__ = "reservation"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    trainer_id: Mapped[int] = Column(Integer, ForeignKey("trainer.id"), nullable=False)
    service_id: Mapped[int] = Column(Integer, ForeignKey("service.id"), nullable=False)
    user_id: Mapped[int] = Column(Integer, ForeignKey("user.id"), nullable=False)
    date: Mapped[str] = Column(String, nullable=False)   # YYYY-MM-DD
    time: Mapped[str] = Column(String, nullable=False)   # HH:MM
    status: Mapped[str] = Column(String(20), nullable=False, default="active")
    # active | canceled | completed

    trainer: Mapped[Trainer] = relationship("Trainer", back_populates="reservations")
    service: Mapped[Service] = relationship("Service", back_populates="reservations")
    user: Mapped[User] = relationship("User", back_populates="reservations")

    def __repr__(self) -> str:
        return f"<Reservation {self.id}>"



class Review(Base):
    __tablename__ = "review"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    trainer_id: Mapped[int] = Column(Integer, ForeignKey("trainer.id"), nullable=False)
    gym_id: Mapped[int] = Column(Integer, ForeignKey("fitness_center.id"), nullable=False)
    user_id: Mapped[int] = Column(Integer, ForeignKey("user.id"), nullable=False)
    rating: Mapped[int] = Column(Integer, nullable=False)
    review: Mapped[Optional[str]] = Column(String(500), nullable=True)

    def __repr__(self) -> str:
        return f"<Review {self.id}>"




class UserRegistrationLog(Base):
    __tablename__ = "user_registration_logs"

    id: Mapped[int] = Column(Integer, primary_key=True)
    login: Mapped[str] = Column(String, nullable=False)
    email: Mapped[str] = Column(String, nullable=False)
    phone: Mapped[Optional[str]] = Column(String, nullable=True)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.now)

    def __repr__(self) -> str:
        return f"<UserRegistrationLog {self.login}>"



class Transaction(Base):
    __tablename__ = "transaction"

    id: Mapped[int] = Column(Integer, primary_key=True)
    user_id: Mapped[int] = Column(Integer, ForeignKey("user.id"), nullable=False)
    amount: Mapped[int] = Column(Integer, nullable=False)   # + top-up / - deduction
    type: Mapped[str] = Column(String(20), nullable=False)  # payment / refund / topup
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)

    user: Mapped[User] = relationship("User", back_populates="transactions")




class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = Column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = Column(Integer, ForeignKey("user.id"))
    action: Mapped[str] = Column(String, nullable=False)
    entity: Mapped[str] = Column(String, nullable=False)
    entity_id: Mapped[Optional[int]] = Column(Integer)
    timestamp: Mapped[datetime] = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} {self.entity}:{self.entity_id}>"
