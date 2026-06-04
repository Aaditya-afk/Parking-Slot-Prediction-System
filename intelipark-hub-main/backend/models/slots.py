"""
Database models for parking slots
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ParkingSlot(Base):
    """Parking slot model"""
    __tablename__ = "parking_slots"
    
    id = Column(Integer, primary_key=True, index=True)
    slot_number = Column(String(10), unique=True, index=True)  # slot1, slot2, slot3
    is_occupied = Column(Boolean, default=False)
    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ParkingSlot(slot_number='{self.slot_number}', is_occupied={self.is_occupied})>"

class SlotLog(Base):
    """Log of all slot state changes"""
    __tablename__ = "slot_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    slot_number = Column(String(10), index=True)
    previous_state = Column(Boolean)
    new_state = Column(Boolean)
    change_timestamp = Column(DateTime, default=datetime.utcnow)
    source = Column(String(50), default="arduino")  # arduino, manual, system
    arduino_timestamp = Column(Integer)  # Arduino millis() timestamp
    
    def __repr__(self):
        return f"<SlotLog(slot='{self.slot_number}', {self.previous_state}->{self.new_state})>"
