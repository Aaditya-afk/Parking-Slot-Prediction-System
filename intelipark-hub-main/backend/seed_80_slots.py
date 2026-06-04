"""
Script to seed 80 parking slots in the database
Run this to populate your Supabase database with 80 slots
"""
import os
os.environ["TOTAL_PARKING_SLOTS"] = "80"

from database_entry_exit import SessionLocal, Base, engine
from models.parking import ParkingSlot

def seed_slots():
    """Create 80 parking slots"""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Delete existing slots
        existing_count = db.query(ParkingSlot).count()
        if existing_count > 0:
            print(f"🗑️  Deleting {existing_count} existing slots...")
            db.query(ParkingSlot).delete()
            db.commit()
        
        # Create 80 new slots
        print("✨ Creating 80 new parking slots...")
        for i in range(1, 81):
            slot = ParkingSlot(
                slot_number=f"SLOT_{i}",
                status="free"
            )
            db.add(slot)
        
        db.commit()
        print("✅ Successfully created 80 parking slots (SLOT_1 to SLOT_80)")
        
        # Verify
        total = db.query(ParkingSlot).count()
        free = db.query(ParkingSlot).filter(ParkingSlot.status == "free").count()
        print(f"📊 Database now has {total} total slots, {free} free")
        
    except Exception as e:
        print(f"❌ Error seeding slots: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_slots()
