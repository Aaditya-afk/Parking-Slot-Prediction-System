"""
Database configuration and session management
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL from environment variable or default to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./smartpark.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables for both legacy 3-slot and scalable entry/exit models"""
    # Legacy 3-slot model (boolean is_occupied)
    from models.slots import Base as SlotsBase
    # Scalable entry/exit model (string status, SLOT_X)
    from models.parking import Base as ParkingBase, ParkingSlot as ParkingSlotStr

    # Create all tables for both models
    SlotsBase.metadata.create_all(bind=engine)
    ParkingBase.metadata.create_all(bind=engine)

    # Seed scalable SLOT_1..SLOT_N if empty
    db = SessionLocal()
    try:
        total = int(os.getenv("TOTAL_PARKING_SLOTS", "80"))
        existing = db.query(ParkingSlotStr).count()
        if existing == 0:
            for i in range(1, total + 1):
                db.add(ParkingSlotStr(slot_number=f"SLOT_{i}", status="free"))
            db.commit()
            print(f"Seeded {total} slots (SLOT_1..SLOT_{total})")
        else:
            print(f"Entry/Exit slots present: {existing}")
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()
