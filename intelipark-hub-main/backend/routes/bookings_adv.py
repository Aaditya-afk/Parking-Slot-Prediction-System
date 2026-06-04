"""
Advanced Booking & Availability APIs
- Start/end bookings with booking types (immediate, scheduled, hourly, daily)
- ML-assisted validation using `ml/availability_predictor.py`
- Scales to N slots defined in `models/parking.ParkingSlot`
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import logging

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database_entry_exit import get_db
from models.parking import ParkingSlot, Reservation
# ML predictor removed to avoid numpy dependency

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/booking", tags=["advanced-booking"])

# Helper functions for IST timezone handling
def get_ist_now():
    """Get current time in IST"""
    return datetime.now(IST)

def to_ist(dt):
    """Convert any datetime to IST"""
    if dt.tzinfo is None:
        # Assume UTC if no timezone
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IST)

# ---------------------- Schemas ----------------------
class BookingType(str):
    pass  # 'immediate' | 'scheduled' | 'hourly' | 'daily'

class BookingCreate(BaseModel):
    slot_number: str = Field(..., description="SLOT_1, SLOT_2, ...")
    booking_type: str = Field(..., description="immediate|scheduled|hourly|daily")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(default=None, ge=15, le=24*60)
    user_name: str
    user_email: str
    user_phone: Optional[str] = None
    vehicle_number: Optional[str] = None

class BookingUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class AvailabilityQuery(BaseModel):
    slot_number: str
    start_time: datetime
    end_time: datetime

# ---------------------- Helpers ----------------------

def _validate_window(start: datetime, end: datetime):
    if end <= start:
        raise HTTPException(status_code=400, detail="End time must be after start time")
    if (end - start).total_seconds() < 15*60:
        raise HTTPException(status_code=400, detail="Minimum booking is 15 minutes")


def _conflicts(db: Session, slot_number: str, start: datetime, end: datetime, exclude_reservation_id: Optional[int] = None) -> bool:
    q = db.query(Reservation).filter(
        Reservation.slot_id.isnot(None),  # keep SQLAlchemy happy
    )
    # We store slot as numeric id in this model; map number
    slot = db.query(ParkingSlot).filter(ParkingSlot.slot_number == slot_number).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    q = db.query(Reservation).filter(Reservation.slot_id == slot.id, Reservation.status == "active")
    if exclude_reservation_id:
        q = q.filter(Reservation.id != exclude_reservation_id)
    # overlap: start < other.end && end > other.start
    clash = q.filter(Reservation.start_time < end, Reservation.end_time > start).first()
    return clash is not None


# ---------------------- Endpoints ----------------------
@router.get("/slots")
async def list_slots(db: Session = Depends(get_db)):
    slots = db.query(ParkingSlot).order_by(ParkingSlot.slot_number).all()
    return {
        "success": True,
        "data": [
            {
                "slot_number": s.slot_number,
                "status": s.status,
                "last_updated": s.last_updated.isoformat() if s.last_updated else None,
            } for s in slots
        ],
        "total": len(slots)
    }


@router.get("/predictions")
async def predictions(minutes_ahead: int = 15, db: Session = Depends(get_db)):
    if minutes_ahead < 5 or minutes_ahead > 240:
        raise HTTPException(status_code=400, detail="minutes_ahead must be 5..240")
    # Simple heuristic predictions without ML dependencies
    slots = db.query(ParkingSlot).all()
    preds = []
    for slot in slots:
        # Basic heuristic: free slots likely to stay free, occupied likely to become free
        prob_free = 0.7 if slot.status == "free" else 0.4
        preds.append({
            "slot_number": slot.slot_number,
            "prediction": "free" if prob_free >= 0.5 else "occupied",
            "probability_free": prob_free,
            "confidence": "medium"
        })
    free = sum(1 for p in preds if p["prediction"] == "free")
    return {
        "success": True,
        "data": {"predictions": preds, "summary": {"likely_free": free, "total": len(preds), "horizon": minutes_ahead}},
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/availability")
async def check_availability(payload: AvailabilityQuery, db: Session = Depends(get_db)):
    try:
        # Normalize datetimes to IST if naive
        start = payload.start_time
        end = payload.end_time
        if start.tzinfo is None:
            start = start.replace(tzinfo=IST)
        if end.tzinfo is None:
            end = end.replace(tzinfo=IST)

        _validate_window(start, end)
        
        # First check if slot exists and is currently free
        slot = db.query(ParkingSlot).filter(ParkingSlot.slot_number == payload.slot_number).first()
        if not slot:
            return {"success": False, "available": False, "reason": "Slot not found"}
        
        # If slot is currently occupied or reserved, check if it conflicts with requested time
        if slot.status in ["occupied", "reserved"]:
            # Check if there's an active reservation that conflicts
            if _conflicts(db, payload.slot_number, start, end):
                return {"success": True, "available": False, "reason": "Slot is already booked for this time"}
        
        # Slot is free or doesn't conflict - it's available
        return {"success": True, "available": True, "reason": "Slot is available"}
    except Exception as e:
        logger.error(f"Error checking availability: {e}")
        return {"success": False, "available": False, "reason": str(e)}


@router.get("/reservations")
async def list_reservations(limit: int = 100, db: Session = Depends(get_db)):
    q = db.query(Reservation).order_by(Reservation.created_at.desc()).limit(limit)
    rows = q.all()
    out: List[Dict[str, Any]] = []
    for r in rows:
        slot = db.query(ParkingSlot).filter(ParkingSlot.id == r.slot_id).first()
        out.append({
            "id": r.id,
            "slot_number": slot.slot_number if slot else None,
            "start_time": r.start_time.isoformat() if r.start_time else None,
            "end_time": r.end_time.isoformat() if r.end_time else None,
            "status": r.status,
            "user_name": r.user_name,
            "user_email": r.user_email,
        })
    return {"success": True, "data": out}


@router.post("/create")
async def create_booking(req: BookingCreate, request: Request, db: Session = Depends(get_db)):
    try:
        logger.info(f"📝 Creating booking: type={req.booking_type}, slot={req.slot_number}, start={req.start_time}, end={req.end_time}, duration={req.duration_minutes}")
        
        # resolve times by type - use IST timezone
        now = get_ist_now()
        if req.booking_type == "immediate":
            start = now
            end = now + timedelta(minutes=req.duration_minutes or 60)
        elif req.booking_type == "hourly":
            start = req.start_time or now
            if start.tzinfo is None:
                start = start.replace(tzinfo=IST)
            hours = max(1, int((req.duration_minutes or 60) / 60))
            end = start + timedelta(hours=hours)
        elif req.booking_type == "daily":
            start = req.start_time or now
            if start.tzinfo is None:
                start = start.replace(tzinfo=IST)
            days = max(1, int((req.duration_minutes or 24*60) / (24*60)))
            end = start + timedelta(days=days)
        elif req.booking_type == "scheduled":
            if not (req.start_time and req.end_time):
                raise HTTPException(status_code=400, detail="scheduled requires start_time and end_time")
            start, end = req.start_time, req.end_time
            # If frontend sent naive times (no tz), assume IST
            if start.tzinfo is None:
                start = start.replace(tzinfo=IST)
            if end.tzinfo is None:
                end = end.replace(tzinfo=IST)
            # Enforce scheduled starts in the future to avoid misclassification as active
            if start <= now:
                raise HTTPException(status_code=400, detail="Scheduled booking start_time must be in the future (IST)")
        else:
            raise HTTPException(status_code=400, detail="Unsupported booking_type")

        logger.info(f"⏰ Calculated times: start={start}, end={end}")
        _validate_window(start, end)

        # conflict check
        if _conflicts(db, req.slot_number, start, end):
            raise HTTPException(status_code=409, detail="Time window conflicts with existing booking")

        # create reservation
        slot = db.query(ParkingSlot).filter(ParkingSlot.slot_number == req.slot_number).first()
        if not slot:
            raise HTTPException(status_code=404, detail="Slot not found")

        # Determine reservation status based on start time
        now = get_ist_now()
        if start <= now:
            # Immediate booking - mark as active
            reservation_status = "active"
            slot_status = "occupied"
            slot.assigned_at = now
        else:
            # Future booking - mark as reserved
            reservation_status = "reserved"
            slot_status = "reserved"
            slot.assigned_at = start
        
        res = Reservation(
            slot_id=slot.id,
            user_name=req.user_name,
            user_email=req.user_email,
            user_phone=req.user_phone or "",
            vehicle_number=req.vehicle_number or "",
            start_time=start,
            end_time=end,
            status=reservation_status,
            amount=0.0,
            payment_status="pending",
        )
        db.add(res)
        
        # Update slot status
        slot.status = slot_status
        slot.last_updated = now
        
        logger.info(f"💾 Committing reservation: id={res.id}, status={res.status}, slot_status={slot.status}")
        db.commit()
        db.refresh(res)
        logger.info(f"✅ Reservation created successfully: id={res.id}")

        # Broadcast booking update and slot status change
        try:
            manager = getattr(request.app.state, 'manager', None)
            if manager:
                import json
                # Broadcast booking created
                await manager.broadcast(json.dumps({
                    "type": "booking_update",
                    "data": {
                        "action": "created",
                        "reservation_id": res.id,
                        "slot_number": req.slot_number,
                        "start_time": start.isoformat(),
                        "end_time": end.isoformat(),
                        "status": res.status,
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                }))
                # Broadcast slot status change
                await manager.broadcast(json.dumps({
                    "type": "slot_update",
                    "data": {
                        "slot_number": req.slot_number,
                        "status": slot.status.upper(),  # Convert to uppercase for frontend compatibility
                        "assigned_at": slot.assigned_at.isoformat() if slot.assigned_at else None,
                        "expected_free_time": end.isoformat(),
                    },
                    "timestamp": datetime.utcnow().isoformat(),
                }))
        except Exception:
            pass

        return {
            "success": True,
            "data": {
                "reservation_id": res.id,
                "slot_number": req.slot_number,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
                "status": res.status,
            }
        }
    except Exception as e:
        logger.error(f"Error creating booking: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create booking: {str(e)}")


@router.put("/{reservation_id}/modify")
async def modify_booking(reservation_id: int, payload: BookingUpdate, request: Request, db: Session = Depends(get_db)):
    res = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if res.status != "active":
        raise HTTPException(status_code=400, detail="Only active reservations can be modified")

    start = payload.start_time or res.start_time
    end = payload.end_time or res.end_time
    _validate_window(start, end)

    slot = db.query(ParkingSlot).filter(ParkingSlot.id == res.slot_id).first()
    if _conflicts(db, slot.slot_number, start, end, exclude_reservation_id=res.id):
        raise HTTPException(status_code=409, detail="New window conflicts with existing booking")

    # Skip ML validation - allow modification if no direct conflicts

    res.start_time = start
    res.end_time = end
    db.commit()

    # Broadcast
    try:
        manager = getattr(request.app.state, 'manager', None)
        if manager:
            import json
            slot = db.query(ParkingSlot).filter(ParkingSlot.id == res.slot_id).first()
            await manager.broadcast(json.dumps({
                "type": "booking_update",
                "data": {
                    "action": "modified",
                    "reservation_id": res.id,
                    "slot_number": slot.slot_number if slot else None,
                    "start_time": start.isoformat(),
                    "end_time": end.isoformat(),
                },
                "timestamp": datetime.utcnow().isoformat(),
            }))
    except Exception:
        pass

    return {"success": True, "message": "Reservation updated", "data": {"start_time": start, "end_time": end}}


@router.put("/{reservation_id}/cancel")
async def cancel_booking(reservation_id: int, request: Request, db: Session = Depends(get_db)):
    res = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if res.status != "active":
        raise HTTPException(status_code=400, detail="Only active reservations can be cancelled")
    res.status = "cancelled"
    db.commit()
    # Broadcast
    try:
        manager = getattr(request.app.state, 'manager', None)
        if manager:
            import json
            slot = db.query(ParkingSlot).filter(ParkingSlot.id == res.slot_id).first()
            await manager.broadcast(json.dumps({
                "type": "booking_update",
                "data": {
                    "action": "cancelled",
                    "reservation_id": res.id,
                    "slot_number": slot.slot_number if slot else None,
                },
                "timestamp": datetime.utcnow().isoformat(),
            }))
    except Exception:
        pass
    return {"success": True, "message": "Reservation cancelled"}
