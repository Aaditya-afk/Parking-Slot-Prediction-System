"""
Database models for parking reservations
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .slots import Base

class Reservation(Base):
    """Parking reservation model"""
    __tablename__ = "reservations"
    
    id = Column(Integer, primary_key=True, index=True)
    slot_number = Column(String(10), index=True)  # slot1, slot2, slot3
    user_name = Column(String(100))
    user_email = Column(String(100))
    user_phone = Column(String(20))
    
    # Timing
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Status
    status = Column(String(20), default="active")  # active, completed, cancelled, expired
    
    # Payment (optional)
    amount = Column(Float, default=0.0)
    payment_status = Column(String(20), default="pending")  # pending, paid, failed
    
    # Additional info
    vehicle_number = Column(String(20))
    notes = Column(Text)
    
    def __repr__(self):
        return f"<Reservation(id={self.id}, slot='{self.slot_number}', user='{self.user_name}', status='{self.status}')>"

class GateLog(Base):
    """Log of gate operations"""
    __tablename__ = "gate_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(20))  # OPEN, CLOSE
    triggered_by = Column(String(50))  # reservation_id, manual, system
    timestamp = Column(DateTime, default=datetime.utcnow)
    success = Column(String(20), default="pending")  # pending, success, failed
    response_time_ms = Column(Integer)  # Time taken for servo to respond
    error_message = Column(Text)
    
    def __repr__(self):
        return f"<GateLog(action='{self.action}', triggered_by='{self.triggered_by}', success='{self.success}')>"
