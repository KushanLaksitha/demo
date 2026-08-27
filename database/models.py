"""
SQLAlchemy ORM models mirroring database/schema.sql
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DECIMAL, Date, DateTime, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

UserRoleEnum = SQLEnum('farmer', 'trader', 'policymaker', 'admin', name='user_role_enum')


class Region(Base):
    __tablename__ = "region"
    region_id = Column(Integer, primary_key=True, autoincrement=True)
    region_name = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False)


class User(Base):
    __tablename__ = "user"
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(150), nullable=False, unique=True)
    password = Column(String(255), nullable=False)   # bcrypt hash
    user_type = Column(UserRoleEnum, nullable=False)    # farmer/trader/policymaker/admin
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    region_id = Column(Integer, ForeignKey("region.region_id"))
    is_active = Column(Boolean, default=False, nullable=False)
    confirmation_token = Column(String(255), nullable=True)
    token_created_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    region = relationship("Region")
    preferences = relationship("UserPreferences", uselist=False, back_populates="user")


class UserPreferences(Base):
    __tablename__ = "user_preferences"
    user_id = Column(Integer, ForeignKey("user.user_id"), primary_key=True)
    notification_settings = Column(Text, default="enabled")
    preferred_crops = Column(Text)   # comma separated crop_ids, e.g. "1,3,5"

    user = relationship("User", back_populates="preferences")


class Crop(Base):
    __tablename__ = "crop"
    crop_id = Column(Integer, primary_key=True, autoincrement=True)
    crop_name = Column(String(100), nullable=False, unique=True)
    category = Column(String(100), nullable=False)


class Production(Base):
    __tablename__ = "production"
    production_id = Column(Integer, primary_key=True, autoincrement=True)
    season = Column(String(50), nullable=False)
    quantity = Column(DECIMAL(12, 2), nullable=False)
    unit = Column(String(20), default="kg")
    record_date = Column(Date, nullable=False)
    crop_id = Column(Integer, ForeignKey("crop.crop_id"), nullable=False)
    region_id = Column(Integer, ForeignKey("region.region_id"), nullable=False)

    crop = relationship("Crop")
    region = relationship("Region")


class Price(Base):
    __tablename__ = "price"
    price_id = Column(Integer, primary_key=True, autoincrement=True)
    price = Column(DECIMAL(10, 2), nullable=False)   # LKR / kg
    date = Column(Date, nullable=False)
    crop_id = Column(Integer, ForeignKey("crop.crop_id"), nullable=False)
    region_id = Column(Integer, ForeignKey("region.region_id"), nullable=False)

    crop = relationship("Crop")
    region = relationship("Region")


class Climate(Base):
    __tablename__ = "climate"
    climate_id = Column(Integer, primary_key=True, autoincrement=True)
    record_date = Column(Date, nullable=False)
    region_id = Column(Integer, ForeignKey("region.region_id"), nullable=False)
    rainfall_mm = Column(DECIMAL(8, 2))
    avg_temp_c = Column(DECIMAL(5, 2))
    humidity_pct = Column(DECIMAL(5, 2))

    region = relationship("Region")


class Prediction(Base):
    __tablename__ = "prediction"
    prediction_id = Column(Integer, primary_key=True, autoincrement=True)
    prediction_type = Column(String(50), nullable=False)  # price | production
    prediction_value = Column(DECIMAL(12, 2), nullable=False)
    prediction_date = Column(Date, nullable=False)
    crop_id = Column(Integer, ForeignKey("crop.crop_id"), nullable=False)
    region_id = Column(Integer, ForeignKey("region.region_id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    crop = relationship("Crop")
    region = relationship("Region")


class Alert(Base):
    __tablename__ = "alert"
    alert_id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    prediction_id = Column(Integer, ForeignKey("prediction.prediction_id"), nullable=True)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Recommendation(Base):
    __tablename__ = "recommendation"
    recommendation_id = Column(Integer, primary_key=True, autoincrement=True)
    message = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False)
    prediction_id = Column(Integer, ForeignKey("prediction.prediction_id"), nullable=True)
    region_id = Column(Integer, ForeignKey("region.region_id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Feedback(Base):
    __tablename__ = "feedback"
    feedback_id = Column(Integer, primary_key=True, autoincrement=True)
    message = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)   # 1-5 stars
    user_id = Column(Integer, ForeignKey("user.user_id"), nullable=False)
    status = Column(String(20), default="new")
    submitted_at = Column(DateTime, default=datetime.utcnow)
