"""
Reservations API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
import logging

from database import get_db
from models import Reservation, Slot
from schemas import Reservation as ReservationSchema, ReservationCreate, ReservationUpdate
import utils

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/reservations", response_model=ReservationSchema)
async def create_reservation(
    reservation: ReservationCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a new parking reservation"""
    try:
        # Validate reservation times
        is_valid, message = utils.validate_reservation_time(reservation.start_time, reservation.end_time)
        if not is_valid:
            raise HTTPException(status_code=400, detail=message)
        
        # Check if slot exists
        slot = db.query(Slot).filter(Slot.id == reservation.slot_id).first()
        if not slot:
            raise HTTPException(status_code=404, detail="Slot not found")
        
        # Check if slot is available for the requested time
        if not utils.is_slot_available(db, reservation.slot_id, reservation.start_time, reservation.end_time):
            raise HTTPException(status_code=409, detail="Slot is not available for the requested time period")
        
        # Create reservation
        db_reservation = Reservation(
            slot_id=reservation.slot_id,
            user_id=reservation.user_id,
            user_name=reservation.user_name,
            user_email=reservation.user_email,
            start_time=reservation.start_time,
            end_time=reservation.end_time,
            status="active",
            created_at=utils.get_current_time()
        )
        
        db.add(db_reservation)
        
        # Update slot status if reservation starts now
        current_time = utils.get_current_time()
        if reservation.start_time <= current_time:
            slot.status = "RESERVED"
            slot.last_updated = current_time
            
            # Send servo command to open gate
            if hasattr(request.app.state, 'send_servo_command'):
                success = request.app.state.send_servo_command("SERVO_OPEN")
                if success:
                    logger.info(f"Gate opened for reservation {db_reservation.id}")
        
        db.commit()
        db.refresh(db_reservation)
        
        # Log the reservation
        utils.log_system_event(db, "INFO", f"New reservation created: slot {slot.slot_label}, user {reservation.user_id}", "reservations")
        
        logger.info(f"Created reservation {db_reservation.id} for slot {slot.slot_label}")
        
        return db_reservation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating reservation: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/reservations", response_model=List[ReservationSchema])
async def get_reservations(
    user_id: int = None,
    status: str = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get reservations with optional filtering"""
    try:
        query = db.query(Reservation)
        
        if user_id:
            query = query.filter(Reservation.user_id == user_id)
        
        if status:
            valid_statuses = ["active", "completed", "canceled"]
            if status not in valid_statuses:
                raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
            query = query.filter(Reservation.status == status)
        
        reservations = query.order_by(Reservation.created_at.desc()).limit(limit).all()
        
        return reservations
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching reservations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/reservations/{reservation_id}", response_model=ReservationSchema)
async def get_reservation(reservation_id: int, db: Session = Depends(get_db)):
    """Get specific reservation details"""
    try:
        reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
        if not reservation:
            raise HTTPException(status_code=404, detail="Reservation not found")
        
        return reservation
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching reservation {reservation_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/reservations/{reservation_id}/cancel")
async def cancel_reservation(
    reservation_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Cancel a reservation"""
    try:
        reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
        if not reservation:
            raise HTTPException(status_code=404, detail="Reservation not found")
        
        if reservation.status != "active":
            raise HTTPException(status_code=400, detail="Only active reservations can be canceled")
        
        # Update reservation status
        reservation.status = "canceled"
        
        # Update slot status if it was reserved
        slot = db.query(Slot).filter(Slot.id == reservation.slot_id).first()
        if slot and slot.status == "RESERVED":
            slot.status = "FREE"
            slot.last_updated = utils.get_current_time()
            
            # Send servo command to close gate if needed
            if hasattr(request.app.state, 'send_servo_command'):
                success = request.app.state.send_servo_command("SERVO_CLOSE")
                if success:
                    logger.info(f"Gate closed after reservation {reservation_id} cancellation")
        
        db.commit()
        
        # Log the cancellation
        utils.log_system_event(db, "INFO", f"Reservation canceled: {reservation_id}", "reservations")
        
        logger.info(f"Canceled reservation {reservation_id}")
        
        return {
            "message": "Reservation canceled successfully",
            "reservation_id": reservation_id,
            "slot_label": slot.slot_label if slot else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error canceling reservation {reservation_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/reservations/{reservation_id}/extend")
async def extend_reservation(
    reservation_id: int,
    minutes: int,
    db: Session = Depends(get_db)
):
    """Extend a reservation by specified minutes"""
    try:
        if minutes <= 0 or minutes > 240:  # Max 4 hours extension
            raise HTTPException(status_code=400, detail="Extension must be between 1 and 240 minutes")
        
        reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
        if not reservation:
            raise HTTPException(status_code=404, detail="Reservation not found")
        
        if reservation.status != "active":
            raise HTTPException(status_code=400, detail="Only active reservations can be extended")
        
        # Calculate new end time
        new_end_time = reservation.end_time + timedelta(minutes=minutes)
        
        # Check if extension is valid (no conflicts)
        if not utils.is_slot_available(db, reservation.slot_id, reservation.end_time, new_end_time):
            raise HTTPException(status_code=409, detail="Cannot extend reservation due to conflicting bookings")
        
        # Update reservation
        old_end_time = reservation.end_time
        reservation.end_time = new_end_time
        
        db.commit()
        
        # Log the extension
        utils.log_system_event(db, "INFO", f"Reservation extended: {reservation_id} by {minutes} minutes", "reservations")
        
        logger.info(f"Extended reservation {reservation_id} by {minutes} minutes")
        
        return {
            "message": "Reservation extended successfully",
            "reservation_id": reservation_id,
            "old_end_time": old_end_time.isoformat(),
            "new_end_time": new_end_time.isoformat(),
            "extension_minutes": minutes
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extending reservation {reservation_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/reservations/check-expired")
async def check_expired_reservations(db: Session = Depends(get_db)):
    """Check and process expired reservations (admin function)"""
    try:
        expired_count = utils.check_expired_reservations(db)
        
        return {
            "message": f"Processed {expired_count} expired reservations",
            "expired_count": expired_count
        }
        
    except Exception as e:
        logger.error(f"Error checking expired reservations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/reservations/active/count")
async def get_active_reservations_count(db: Session = Depends(get_db)):
    """Get count of currently active reservations"""
    try:
        count = db.query(Reservation).filter(Reservation.status == "active").count()
        
        return {
            "active_reservations": count,
            "timestamp": utils.get_current_time().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error counting active reservations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
