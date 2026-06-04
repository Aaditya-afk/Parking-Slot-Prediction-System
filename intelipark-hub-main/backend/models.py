"""
SQLAlchemy ORM Models for SmartPark Database
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime, timezone

class Slot(Base):
    """Parking slot model"""
    __tablename__ = "slots"
    
    id = Column(Integer, primary_key=True, index=True)
    slot_label = Column(String(50), unique=True, index=True, nullable=False)
    status = Column(String(20), default="FREE")  # FREE, OCCUPIED, RESERVED
    last_updated = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    
    # Relationships
    reservations = relationship("Reservation", back_populates="slot")
    sensor_logs = relationship("SensorLog", back_populates="slot")
    forecasts = relationship("Forecast", back_populates="slot")

class Reservation(Base):
    """Parking reservation model"""
    __tablename__ = "reservations"
    
    id = Column(Integer, primary_key=True, index=True)
    slot_id = Column(Integer, ForeignKey("slots.id"), nullable=False)
    user_id = Column(Integer, nullable=False)  # User identifier
    user_name = Column(String(100))  # Optional user name
    user_email = Column(String(100))  # Optional user email
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), default="active")  # active, completed, canceled
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    
    # Relationships
    slot = relationship("Slot", back_populates="reservations")

class SensorLog(Base):
    """Sensor event logging model"""
    __tablename__ = "sensor_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    slot_id = Column(Integer, ForeignKey("slots.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    occupied = Column(Boolean, nullable=False)
    
    # Relationships
    slot = relationship("Slot", back_populates="sensor_logs")

class Forecast(Base):
    """ML prediction model results"""
    __tablename__ = "forecasts"
    
    id = Column(Integer, primary_key=True, index=True)
    slot_id = Column(Integer, ForeignKey("slots.id"), nullable=False)
    generated_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    horizon_minutes = Column(Integer, nullable=False)  # Prediction horizon
    prediction = Column(Float, nullable=False)  # Probability of being free (0-1)
    
    # Relationships
    slot = relationship("Slot", back_populates="forecasts")

class SystemLog(Base):
    """System events and errors logging"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    level = Column(String(20), nullable=False)  # INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    component = Column(String(50))  # serial_bridge, ml_model, api, etc.
