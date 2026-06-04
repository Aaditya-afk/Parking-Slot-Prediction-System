"""
Utility functions for SmartPark backend
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from models import SensorLog, SystemLog, Reservation, Slot
import logging

logger = logging.getLogger(__name__)

def get_current_time() -> datetime:
    """Get current UTC time with timezone info"""
    return datetime.now(timezone.utc)

def log_sensor_event(db: Session, slot_id: int, occupied: bool):
    """Log a sensor event to the database"""
    try:
        sensor_log = SensorLog(
            slot_id=slot_id,
            occupied=occupied,
            timestamp=get_current_time()
        )
        db.add(sensor_log)
        db.commit()
        logger.debug(f"Logged sensor event: slot_id={slot_id}, occupied={occupied}")
    except Exception as e:
        logger.error(f"Error logging sensor event: {e}")
        db.rollback()

def log_system_event(db: Session, level: str, message: str, component: str = "system"):
    """Log a system event"""
    try:
        system_log = SystemLog(
            level=level,
            message=message,
            component=component,
            timestamp=get_current_time()
        )
        db.add(system_log)
        db.commit()
    except Exception as e:
        logger.error(f"Error logging system event: {e}")
        db.rollback()

def check_expired_reservations(db: Session):
    """Check and handle expired reservations"""
    current_time = get_current_time()
    
    # Find expired active reservations
    expired_reservations = db.query(Reservation).filter(
        Reservation.status == "active",
        Reservation.end_time < current_time
    ).all()
    
    for reservation in expired_reservations:
        # Check if slot is actually free (sensor confirms)
        slot = db.query(Slot).filter(Slot.id == reservation.slot_id).first()
        
        if slot and slot.status == "FREE":
            # Mark reservation as completed
            reservation.status = "completed"
            logger.info(f"Auto-completed expired reservation {reservation.id}")
        elif slot and slot.status == "OCCUPIED":
            # Extend reservation by 15 minutes (grace period)
            reservation.end_time = current_time + timedelta(minutes=15)
            logger.info(f"Extended reservation {reservation.id} by 15 minutes")
    
    db.commit()
    return len(expired_reservations)

def calculate_occupancy_rate(db: Session, hours: int = 24) -> float:
    """Calculate occupancy rate for the last N hours"""
    end_time = get_current_time()
    start_time = end_time - timedelta(hours=hours)
    
    # Get all sensor logs in the time period
    logs = db.query(SensorLog).filter(
        SensorLog.timestamp >= start_time,
        SensorLog.timestamp <= end_time
    ).all()
    
    if not logs:
        return 0.0
    
    occupied_count = sum(1 for log in logs if log.occupied)
    return (occupied_count / len(logs)) * 100

def get_peak_hours(db: Session, days: int = 7) -> list:
    """Get peak usage hours based on historical data"""
    end_time = get_current_time()
    start_time = end_time - timedelta(days=days)
    
    # Count occupancy events by hour
    hour_counts = {}
    
    logs = db.query(SensorLog).filter(
        SensorLog.timestamp >= start_time,
        SensorLog.timestamp <= end_time,
        SensorLog.occupied == True
    ).all()
    
    for log in logs:
        hour = log.timestamp.hour
        hour_counts[hour] = hour_counts.get(hour, 0) + 1
    
    # Sort by count and return top 3 hours
    sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
    return [hour for hour, count in sorted_hours[:3]]

def validate_reservation_time(start_time: datetime, end_time: datetime) -> tuple[bool, str]:
    """Validate reservation time constraints"""
    current_time = get_current_time()
    
    # Check if start time is in the future
    if start_time < current_time:
        return False, "Start time must be in the future"
    
    # Check if end time is after start time
    if end_time <= start_time:
        return False, "End time must be after start time"
    
    # Check maximum reservation duration (24 hours)
    max_duration = timedelta(hours=24)
    if end_time - start_time > max_duration:
        return False, "Reservation cannot exceed 24 hours"
    
    # Check minimum reservation duration (15 minutes)
    min_duration = timedelta(minutes=15)
    if end_time - start_time < min_duration:
        return False, "Reservation must be at least 15 minutes"
    
    return True, "Valid"

def is_slot_available(db: Session, slot_id: int, start_time: datetime, end_time: datetime) -> bool:
    """Check if a slot is available for the given time period"""
    # Check for overlapping reservations
    overlapping = db.query(Reservation).filter(
        Reservation.slot_id == slot_id,
        Reservation.status == "active",
        Reservation.start_time < end_time,
        Reservation.end_time > start_time
    ).first()
    
    return overlapping is None

def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable string"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

def sanitize_arduino_input(message: str) -> str:
    """Sanitize input from Arduino to prevent injection"""
    # Remove any non-printable characters
    sanitized = ''.join(char for char in message if char.isprintable())
    
    # Limit length
    sanitized = sanitized[:100]
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '&', '"', "'", ';', '|', '`']
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    return sanitized.strip()

def get_slot_statistics(db: Session, slot_id: int, days: int = 30) -> dict:
    """Get usage statistics for a specific slot"""
    end_time = get_current_time()
    start_time = end_time - timedelta(days=days)
    
    # Get sensor logs for this slot
    logs = db.query(SensorLog).filter(
        SensorLog.slot_id == slot_id,
        SensorLog.timestamp >= start_time
    ).all()
    
    if not logs:
        return {
            "total_events": 0,
            "occupancy_rate": 0.0,
            "avg_duration": 0,
            "usage_count": 0
        }
    
    occupied_events = [log for log in logs if log.occupied]
    free_events = [log for log in logs if not log.occupied]
    
    # Calculate average occupancy duration
    durations = []
    for i, occupied_log in enumerate(occupied_events):
        # Find next free event
        next_free = None
        for free_log in free_events:
            if free_log.timestamp > occupied_log.timestamp:
                next_free = free_log
                break
        
        if next_free:
            duration = (next_free.timestamp - occupied_log.timestamp).total_seconds()
            durations.append(duration)
    
    avg_duration = sum(durations) / len(durations) if durations else 0
    
    return {
        "total_events": len(logs),
        "occupancy_rate": (len(occupied_events) / len(logs)) * 100,
        "avg_duration": avg_duration,
        "usage_count": len(occupied_events)
    }
