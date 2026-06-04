"""
Database configuration for SmartPark Entry/Exit System
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from models.parking import Base, ParkingSlot, CarEvent, Reservation, GateLog, SystemLog, OccupancyStats

# Database URL from environment variable or default to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smartpark_entry_exit.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables and create initial slots"""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create initial parking slots if they don't exist
    db = SessionLocal()
    try:
        # Check if slots already exist
        existing_slots = db.query(ParkingSlot).count()
        if existing_slots == 0:
            # Create default number of parking slots (configurable)
            total_slots = int(os.getenv("TOTAL_PARKING_SLOTS", "80"))
            
            for i in range(1, total_slots + 1):
                slot = ParkingSlot(
                    slot_number=f"SLOT_{i}",
                    status="free"
                )
                db.add(slot)
            
            db.commit()
            print(f"✅ Created {total_slots} initial parking slots")
        else:
            print(f"📊 Database already has {existing_slots} slots")
            
        # Log system initialization
        from datetime import datetime
        system_log = SystemLog(
            level="INFO",
            component="database",
            message=f"Database initialized with {existing_slots or total_slots} slots",
            timestamp=datetime.utcnow()
        )
        db.add(system_log)
        db.commit()
            
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()

def get_slot_stats(db):
    """Get current slot statistics"""
    try:
        total_slots = db.query(ParkingSlot).count()
        free_slots = db.query(ParkingSlot).filter(ParkingSlot.status == "free").count()
        occupied_slots = db.query(ParkingSlot).filter(ParkingSlot.status == "occupied").count()
        reserved_slots = db.query(ParkingSlot).filter(ParkingSlot.status == "reserved").count()
        
        occupancy_rate = (occupied_slots / total_slots * 100) if total_slots > 0 else 0
        
        return {
            "total_slots": total_slots,
            "free_slots": free_slots,
            "occupied_slots": occupied_slots,
            "reserved_slots": reserved_slots,
            "occupancy_rate": round(occupancy_rate, 1)
        }
    except Exception as e:
        print(f"❌ Error getting slot stats: {e}")
        return {
            "total_slots": 0,
            "free_slots": 0,
            "occupied_slots": 0,
            "reserved_slots": 0,
            "occupancy_rate": 0.0
        }

def log_system_event(db, level: str, component: str, message: str, additional_data: str = None):
    """Log a system event to the database"""
    try:
        from datetime import datetime
        log_entry = SystemLog(
            level=level,
            component=component,
            message=message,
            additional_data=additional_data,
            timestamp=datetime.utcnow()
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        print(f"❌ Error logging system event: {e}")
        db.rollback()

def cleanup_old_logs(db, days_to_keep: int = 30):
    """Clean up old log entries"""
    try:
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Clean old system logs
        old_system_logs = db.query(SystemLog).filter(SystemLog.timestamp < cutoff_date).delete()
        
        # Clean old car events (keep more recent ones)
        old_events = db.query(CarEvent).filter(CarEvent.timestamp < cutoff_date).delete()
        
        # Clean old gate logs
        old_gate_logs = db.query(GateLog).filter(GateLog.timestamp < cutoff_date).delete()
        
        db.commit()
        
        total_cleaned = old_system_logs + old_events + old_gate_logs
        if total_cleaned > 0:
            print(f"🧹 Cleaned {total_cleaned} old log entries")
            
        return total_cleaned
        
    except Exception as e:
        print(f"❌ Error cleaning old logs: {e}")
        db.rollback()
        return 0
