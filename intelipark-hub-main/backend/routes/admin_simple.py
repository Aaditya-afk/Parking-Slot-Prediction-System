from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database_entry_exit import get_db
from models.parking import ParkingSlot, Reservation, Feedback
from database_entry_exit import get_slot_stats

router = APIRouter(prefix="/api/admin", tags=["admin"])

IST = timezone(timedelta(hours=5, minutes=30))

def to_ist_iso(dt: datetime) -> str:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IST).isoformat()

@router.get("/summary")
async def get_summary(db: Session = Depends(get_db)):
    """Return real-time admin dashboard summary using current schema."""
    # Slot stats (free/occupied/reserved counts)
    slot_stats = get_slot_stats(db)

    # Active bookings = active + reserved reservations
    active_bookings = db.query(Reservation).filter(
        Reservation.status.in_(["active", "reserved"])  # statuses used in current code
    ).count()

    # Feedback stats (if table exists)
    try:
        total_feedback = db.query(func.count(Feedback.id)).scalar() or 0
        avg_rating = db.query(func.avg(Feedback.rating)).scalar()
        average_rating = float(avg_rating) if avg_rating is not None else 0.0
    except Exception:
        total_feedback = 0
        average_rating = 0.0

    # System health: percentage of non-maintenance slots
    total_slots = slot_stats.get("total_slots", 0)
    maintenance_slots = db.query(ParkingSlot).filter(ParkingSlot.status == "maintenance").count()
    working = max(0, total_slots - maintenance_slots)
    system_health = round((working / total_slots * 100), 1) if total_slots else 0.0

    return {
        "success": True,
        "data": {
            "active_bookings": active_bookings,
            "total_feedback": total_feedback,
            "average_rating": round(average_rating, 1),
            "system_health": system_health,
            "slot_status": slot_stats,
            "timestamp": to_ist_iso(datetime.utcnow()),
        }
    }

@router.get("/recent-reservations")
async def recent_reservations(limit: int = 20, db: Session = Depends(get_db)):
    """Return the most recent reservations for admin view."""
    limit = max(1, min(100, limit))
    # Fetch latest reservations with slot number
    rows = (
        db.query(Reservation, ParkingSlot.slot_number)
        .join(ParkingSlot, ParkingSlot.id == Reservation.slot_id)
        .order_by(Reservation.created_at.desc())
        .limit(limit)
        .all()
    )
    data = []
    for res, slot_number in rows:
        data.append({
            "id": res.id,
            "slot_number": slot_number,
            "status": res.status,
            "start_time": to_ist_iso(res.start_time),
            "end_time": to_ist_iso(res.end_time),
            "created_at": to_ist_iso(res.created_at),
            "user_name": res.user_name,
            "user_email": res.user_email,
        })
    return {"success": True, "data": data}
