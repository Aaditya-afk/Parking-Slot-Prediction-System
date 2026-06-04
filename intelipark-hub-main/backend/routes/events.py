"""
API routes for car entry/exit events - SmartPark Entry/Exit System
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import json

from database_entry_exit import get_db, get_slot_stats, log_system_event
from models.parking import ParkingSlot, CarEvent, GateLog, Reservation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["events"])

@router.get("/get_slots")
async def get_all_slots(db: Session = Depends(get_db)):
    """Get all parking slots with current status and timer fields"""
    try:
        slots = db.query(ParkingSlot).order_by(ParkingSlot.slot_number).all()

        # Default occupied duration in minutes if no explicit reservation duration exists
        DEFAULT_OCCUPIED_DURATION_MIN = 20

        # Format for frontend compatibility
        slot_data = []
        now = datetime.utcnow()
        for slot in slots:
            # Get the actual reservation end time if exists
            expected_free_time_iso = None
            timer_remaining_sec = None
            user_set_duration = None
            
            if slot.status in ["occupied", "reserved"]:
                # Find active reservation for this slot
                reservation = db.query(Reservation).filter(
                    Reservation.slot_id == slot.id,
                    Reservation.status == "active"
                ).first()
                
                if reservation and reservation.end_time:
                    # Use actual reservation end time
                    expected_dt = reservation.end_time
                    expected_free_time_iso = expected_dt.isoformat()
                    timer_remaining_sec = max(0, int((expected_dt - now).total_seconds()))
                    # Calculate duration in minutes
                    if reservation.start_time:
                        user_set_duration = int((reservation.end_time - reservation.start_time).total_seconds() / 60)
                elif slot.assigned_at:
                    # Fallback to default duration if no reservation found
                    expected_dt = slot.assigned_at + timedelta(minutes=DEFAULT_OCCUPIED_DURATION_MIN)
                    if expected_dt < now:
                        expected_dt = now
                    expected_free_time_iso = expected_dt.isoformat()
                    timer_remaining_sec = max(0, int((expected_dt - now).total_seconds()))
                    user_set_duration = DEFAULT_OCCUPIED_DURATION_MIN

            slot_data.append({
                "id": slot.id,
                "slot_number": slot.slot_number,
                "status": slot.status.upper(),  # Convert to uppercase for frontend compatibility
                "assigned_at": slot.assigned_at.isoformat() if slot.assigned_at else None,
                "last_updated": slot.last_updated.isoformat() if slot.last_updated else None,
                # Timer fields from actual reservation
                "expected_free_time": expected_free_time_iso,
                "timer_remaining": timer_remaining_sec,
                "user_set_duration": user_set_duration,
            })
        
        # Get summary statistics
        stats = get_slot_stats(db)
        
        return {
            "success": True,
            "data": {
                "slots": slot_data,
                "summary": stats
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting slots: {e}")
        raise HTTPException(status_code=500, detail="Failed to get slots")

@router.get("/debug_occupied_slots")
async def debug_occupied_slots(db: Session = Depends(get_db)):
    """Debug endpoint to check occupied slots"""
    try:
        slots = db.query(ParkingSlot).order_by(ParkingSlot.slot_number).all()
        
        debug_info = {
            "total_slots": len(slots),
            "occupied_slots_raw": [],
            "occupied_slots_converted": [],
            "all_statuses": {}
        }
        
        for slot in slots:
            # Count all status types
            status = slot.status
            if status not in debug_info["all_statuses"]:
                debug_info["all_statuses"][status] = 0
            debug_info["all_statuses"][status] += 1
            
            # Check if occupied (raw)
            if slot.status == "occupied":
                debug_info["occupied_slots_raw"].append({
                    "slot_number": slot.slot_number,
                    "status_raw": slot.status,
                    "status_converted": slot.status.upper()
                })
            
            # Check if occupied (converted)
            if slot.status.upper() == "OCCUPIED":
                debug_info["occupied_slots_converted"].append({
                    "slot_number": slot.slot_number,
                    "status_raw": slot.status,
                    "status_converted": slot.status.upper()
                })
        
        return debug_info
        
    except Exception as e:
        logger.error(f"❌ Error in debug endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to debug slots")
