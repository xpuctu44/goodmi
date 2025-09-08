from datetime import datetime, date, time, timezone, timedelta

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import relationship

from app.database import Base


def _get_moscow_time():
    """Получает текущее время в московском часовом поясе (UTC+3)"""
    moscow_tz = timezone(timedelta(hours=3))
    return datetime.now(moscow_tz)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(320), unique=True, index=True, nullable=False)
    full_name = Column(String(200), nullable=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    role = Column(String(20), nullable=False, default="employee")
    date_of_birth = Column(Date, nullable=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="SET NULL"), nullable=True)

    # Telegram integration
    telegram_id = Column(Integer, unique=True, nullable=True)

    # Web credentials for Telegram-registered users
    web_username = Column(String(100), unique=True, nullable=True)
    web_password_plain = Column(String(100), nullable=True)

    store = relationship("Store", back_populates="employees")


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    work_date = Column(Date, nullable=False)
    hours = Column(Float, nullable=True)
    
    user = relationship("User")

class ScheduleEntry(Base):
    __tablename__ = "schedule_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    work_date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="SET NULL"), nullable=True)
    notes = Column(Text, nullable=True)
    shift_type = Column(String(20), nullable=False, default="work")  # work, off, vacation, sick, weekend
    published = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=_get_moscow_time, nullable=False)

    user = relationship("User")
    store = relationship("Store")


class Store(Base):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    address = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    employees = relationship("User", back_populates="store")


class AllowedIP(Base):
    __tablename__ = "allowed_ips"

    id = Column(Integer, primary_key=True, index=True)
    ip_address = Column(String(45), unique=True, nullable=False, index=True)  # IPv4 and IPv6 support
    description = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=_get_moscow_time, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    creator = relationship("User")

