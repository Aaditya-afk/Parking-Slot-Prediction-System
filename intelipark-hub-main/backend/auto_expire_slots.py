"""
Background task to auto-expire slots when their booking time ends
"""
import asyncio
from datetime import datetime
from database_entry_exit import SessionLocal
from models.parking import ParkingSlot, Reservation

async def auto_expire_slots():
    """Check and free expired slots every 5 seconds"""
    while True:
        try:
            db = SessionLocal()
            now = datetime.utcnow()
            
            # Find all active reservations that have ended
            expired_reservations = db.query(Reservation).filter(
                Reservation.status == "active",
                Reservation.end_time <= now
            ).all()
            
            for res in expired_reservations:
                # Mark reservation as completed
                res.status = "completed"
                
                # Free the slot
                slot = db.query(ParkingSlot).filter(ParkingSlot.id == res.slot_id).first()
                if slot:
                    slot.status = "free"
                    slot.assigned_at = None
                    slot.last_updated = now
                    print(f"✅ Auto-freed {slot.slot_number} - booking expired")
            
            if expired_reservations:
                db.commit()
                
            db.close()
        except Exception as e:
            print(f"❌ Error in auto_expire_slots: {e}")
            try:
                db.close()
            except:
                pass
        
        await asyncio.sleep(5)  # Check every 5 seconds
