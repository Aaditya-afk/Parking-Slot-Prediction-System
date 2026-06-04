"""
Slots API endpoints (Entry/Exit unified model)
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
import logging
from datetime import datetime

from database_entry_exit import get_db
from models.parking import ParkingSlot as Slot, Reservation
from schemas import SlotStatus, ParkingOverview, SlotUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["slots"])

@router.get("/slots", response_model=List[SlotStatus])
async def get_all_slots(db: Session = Depends(get_db)):
    """Get all parking slots with their current status"""
    try:
        slots = db.query(Slot).order_by(Slot.slot_number).all()
        out: List[SlotStatus] = []

        for slot in slots:
            # Prefer an active reservation; otherwise take the most relevant reserved one
            active_res = db.query(Reservation).filter(
                Reservation.slot_id == slot.id,
                Reservation.status == "active",
            ).order_by(Reservation.end_time.desc()).first()

            reserved_res = None
            if active_res is None:
                reserved_res = db.query(Reservation).filter(
                    Reservation.slot_id == slot.id,
                    Reservation.status == "reserved",
                ).order_by(Reservation.end_time.desc()).first()

            chosen = active_res or reserved_res

            out.append(
                SlotStatus(
                    id=slot.id,
                    slot_label=slot.slot_number,  # map to schema field
                    status=slot.status.upper(),  # Convert to uppercase for frontend compatibility
                    last_updated=slot.last_updated,
                    has_active_reservation=active_res is not None,
                    reservation_end_time=chosen.end_time if chosen else None,
                )
            )

        return out
        
    except Exception as e:
        logger.error(f"Error fetching slots: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/slots/{slot_id}", response_model=SlotStatus)
async def get_slot(slot_id: int, db: Session = Depends(get_db)):
    """Get specific slot details"""
    try:
        slot = db.query(Slot).filter(Slot.id == slot_id).first()
        if not slot:
            raise HTTPException(status_code=404, detail="Slot not found")
        
        # Check for active reservations
        active_res = db.query(Reservation).filter(
            Reservation.slot_id == slot.id,
            Reservation.status == "active",
        ).first()

        return SlotStatus(
            id=slot.id,
            slot_label=slot.slot_number,
            status=slot.status.upper(),  # Convert to uppercase for frontend compatibility
            last_updated=slot.last_updated,
            has_active_reservation=active_res is not None,
            reservation_end_time=active_res.end_time if active_res else None,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching slot {slot_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/slots/update")
async def update_slot_status(
    slot_label: str,
    status: str,
    request: Request,
    db: Session = Depends(get_db),
):
    """Update slot status from hardware"""
    try:
        # Accept both SLOT_X and legacy labels
        slot = db.query(Slot).filter(Slot.slot_number == slot_label).first()
        if not slot:
            raise HTTPException(status_code=404, detail="Slot not found")
        
        # Normalize status to lower-case per entry/exit model
        new_status = status.lower()
        valid = {"free", "occupied", "reserved", "maintenance"}
        if new_status not in valid:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {sorted(list(valid))}")

        slot.status = new_status
        slot.last_updated = datetime.utcnow()
        db.commit()
        
        return {"success": True, "message": f"Slot {slot_label} updated to {new_status}"}
        
    except Exception as e:
        logger.error(f"Error updating slot {slot_label}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/slots/{slot_id}", response_model=SlotStatus)
async def update_slot(
    slot_id: int,
    slot_update: SlotUpdate,
    db: Session = Depends(get_db),
):
    """Update slot status manually (admin function)"""
    try:
        slot = db.query(Slot).filter(Slot.id == slot_id).first()
        if not slot:
            raise HTTPException(status_code=404, detail="Slot not found")
        
        if slot_update.status:
            valid_statuses = ["free", "occupied", "reserved", "maintenance"]
            normalized = slot_update.status.lower()
            if normalized not in valid_statuses:
                raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

            slot.status = normalized
            slot.last_updated = datetime.utcnow()
        
        db.commit()
        
        # Get updated slot info
        active_reservation = db.query(Reservation).filter(
            Reservation.slot_id == slot.id, Reservation.status == "active"
        ).first()
        
        return SlotStatus(
            id=slot.id,
            slot_label=slot.slot_number,
            status=slot.status.upper(),  # Convert to uppercase for frontend compatibility
            last_updated=slot.last_updated,
            has_active_reservation=active_reservation is not None,
            reservation_end_time=active_reservation.end_time if active_reservation else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating slot {slot_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/slots/{slot_id}/statistics")
async def get_slot_statistics(
    slot_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
):
    """Get usage statistics for a specific slot"""
    try:
        slot = db.query(Slot).filter(Slot.id == slot_id).first()
        if not slot:
            raise HTTPException(status_code=404, detail="Slot not found")
        
        # Placeholder: integrate with proper stats once SensorLog is implemented for entry/exit model
        stats = {
            "total_events": 0,
            "occupancy_rate": 0.0,
            "avg_duration": 0,
            "usage_count": 0,
        }
        
        return {
            "slot_id": slot_id,
            "slot_label": slot.slot_number,
            "period_days": days,
            "statistics": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching slot statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
