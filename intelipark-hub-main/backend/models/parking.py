"""
Database models for SmartPark Entry/Exit System
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ParkingSlot(Base):
    """Parking slot model for entry/exit system"""
    __tablename__ = "parking_slots"
    
    id = Column(Integer, primary_key=True, index=True)
    slot_number = Column(String(10), unique=True, index=True)  # SLOT_1, SLOT_2, etc.
    status = Column(String(20), default="free")  # free, occupied, reserved, maintenance
    assigned_at = Column(DateTime, nullable=True)  # When slot was assigned
    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ParkingSlot(slot_number='{self.slot_number}', status='{self.status}')>"

class CarEvent(Base):
    """Log of all car entry/exit events"""
    __tablename__ = "car_events"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(20), index=True)  # car_entered, car_exited
    timestamp = Column(DateTime, default=datetime.utcnow)
    arduino_timestamp = Column(Integer)  # Arduino millis() timestamp
    entry_sensor_state = Column(Boolean, default=False)
    exit_sensor_state = Column(Boolean, default=False)
    assigned_slot_id = Column(Integer, nullable=True)  # Which slot was assigned/freed
    processing_status = Column(String(20), default="processed")  # processed, failed, pending
    error_message = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<CarEvent(event_type='{self.event_type}', timestamp='{self.timestamp}')>"

class Reservation(Base):
    """Parking reservation model"""
    __tablename__ = "reservations"
    
    id = Column(Integer, primary_key=True, index=True)
    slot_id = Column(Integer, index=True)  # Reference to parking slot
    user_name = Column(String(100))
    user_email = Column(String(100))
    user_phone = Column(String(20))
    vehicle_number = Column(String(20))
    
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
    notes = Column(Text)
    
    def __repr__(self):
        return f"<Reservation(id={self.id}, slot_id={self.slot_id}, user='{self.user_name}', status='{self.status}')>"

class GateLog(Base):
    """Log of gate operations"""
    __tablename__ = "gate_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(20))  # OPEN, CLOSE
    triggered_by = Column(String(50))  # car_entry, car_exit, manual, reservation
    event_id = Column(Integer, nullable=True)  # Reference to car event
    timestamp = Column(DateTime, default=datetime.utcnow)
    success = Column(String(20), default="pending")  # pending, success, failed
    response_time_ms = Column(Integer)  # Time taken for gate to respond
    error_message = Column(Text)
    arduino_response = Column(Text)  # Raw Arduino response
    
    def __repr__(self):
        return f"<GateLog(action='{self.action}', triggered_by='{self.triggered_by}', success='{self.success}')>"

class SystemLog(Base):
    """General system logs and events"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(10), index=True)  # INFO, WARNING, ERROR, DEBUG
    component = Column(String(50), index=True)  # arduino, bridge, backend, frontend
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    additional_data = Column(Text)  # JSON string for extra data
    
    def __repr__(self):
        return f"<SystemLog(level='{self.level}', component='{self.component}', timestamp='{self.timestamp}')>"

class OccupancyStats(Base):
    """Occupancy statistics for AI/ML predictions"""
    __tablename__ = "occupancy_stats"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    hour = Column(Integer)  # 0-23
    day_of_week = Column(Integer)  # 0=Monday, 6=Sunday
    total_slots = Column(Integer)
    occupied_slots = Column(Integer)
    free_slots = Column(Integer)
    reserved_slots = Column(Integer)
    occupancy_rate = Column(Float)  # Percentage
    entry_events_hour = Column(Integer, default=0)  # Cars entered this hour
    exit_events_hour = Column(Integer, default=0)   # Cars exited this hour
    
    def __repr__(self):
        return f"<OccupancyStats(timestamp='{self.timestamp}', occupancy_rate={self.occupancy_rate})>"

class Feedback(Base):
    """User feedback model"""
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True)
    user_name = Column(String(100))
    user_email = Column(String(100))
    
    # Feedback content
    rating = Column(Integer)  # 1-5 stars
    category = Column(String(50))  # 'complaint', 'suggestion', 'praise', 'bug_report'
    message = Column(Text)
    
    # Status tracking
    status = Column(String(20), default="pending")  # pending, reviewed, resolved, dismissed
    priority = Column(String(20), default="normal")  # low, normal, high, critical
    
    # Admin response
    admin_response = Column(Text, nullable=True)
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Feedback(id={self.id}, rating={self.rating}, category='{self.category}', status='{self.status}')>"
