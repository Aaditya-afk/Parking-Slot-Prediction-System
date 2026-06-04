"""
API routes for parking reservations - 3 Slots System
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging

from database import get_db
from models.reservations import Reservation, GateLog
from models.slots import ParkingSlot

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["reservations"])

@router.post("/reserve_slot")
async def reserve_slot(reservation_data: Dict[str, Any], db: Session = Depends(get_db)):
    """Reserve a parking slot"""
    try:
        slot_number = reservation_data.get("slot_number")  # slot1, slot2, slot3
        user_name = reservation_data.get("user_name", "Anonymous")
        user_email = reservation_data.get("user_email", "")
        user_phone = reservation_data.get("user_phone", "")
        vehicle_number = reservation_data.get("vehicle_number", "")
        duration_hours = reservation_data.get("duration_hours", 2)  # Default 2 hours
        
        if not slot_number or slot_number not in ["slot1", "slot2", "slot3"]:
            raise HTTPException(status_code=400, detail="Invalid slot number")
        
        # Check if slot exists and is available
        slot = db.query(ParkingSlot).filter(ParkingSlot.slot_number == slot_number).first()
        if not slot:
            raise HTTPException(status_code=404, detail="Slot not found")
        
        if slot.is_occupied:
            raise HTTPException(status_code=409, detail="Slot is currently occupied")
        
        # Check for existing active reservations
        existing_reservation = db.query(Reservation).filter(
            Reservation.slot_number == slot_number,
            Reservation.status == "active"
        ).first()
        
        if existing_reservation:
            raise HTTPException(status_code=409, detail="Slot is already reserved")
        
        # Create reservation
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=duration_hours)
        
        reservation = Reservation(
            slot_number=slot_number,
            user_name=user_name,
            user_email=user_email,
            user_phone=user_phone,
            vehicle_number=vehicle_number,
            start_time=start_time,
            end_time=end_time,
            status="active",
            amount=duration_hours * 5.0,  # $5 per hour
            payment_status="pending"
        )
        
        db.add(reservation)
        db.commit()
        db.refresh(reservation)
        
        logger.info(f"Created reservation {reservation.id} for {slot_number} by {user_name}")
        
        return {
            "success": True,
            "message": "Slot reserved successfully",
            "data": {
                "reservation_id": reservation.id,
                "slot_number": slot_number,
                "user_name": user_name,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "amount": reservation.amount,
                "status": reservation.status
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating reservation: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create reservation")

@router.post("/release_slot")
async def release_slot(release_data: Dict[str, Any], db: Session = Depends(get_db)):
    """Release a parking slot reservation"""
    try:
        reservation_id = release_data.get("reservation_id")
        slot_number = release_data.get("slot_number")
        
        if reservation_id:
            # Find by reservation ID
            reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
        elif slot_number:
            # Find active reservation by slot number
            reservation = db.query(Reservation).filter(
                Reservation.slot_number == slot_number,
                Reservation.status == "active"
            ).first()
        else:
            raise HTTPException(status_code=400, detail="Provide either reservation_id or slot_number")
        
        if not reservation:
            raise HTTPException(status_code=404, detail="Reservation not found")
        
        if reservation.status != "active":
            raise HTTPException(status_code=400, detail="Can only release active reservations")
        
        # Update reservation status
        reservation.status = "completed"
        reservation.end_time = datetime.utcnow()  # Update actual end time
        
        db.commit()
        
        logger.info(f"Released reservation {reservation.id} for {reservation.slot_number}")
        
        return {
            "success": True,
            "message": "Slot released successfully",
            "data": {
                "reservation_id": reservation.id,
                "slot_number": reservation.slot_number,
                "completed_at": reservation.end_time.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error releasing slot: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to release slot")

@router.get("/reservations")
async def get_reservations(
    user_email: str = None,
    slot_number: str = None,
    status: str = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get reservations with optional filters"""
    try:
        query = db.query(Reservation)
        
        if user_email:
            query = query.filter(Reservation.user_email == user_email)
        if slot_number:
            query = query.filter(Reservation.slot_number == slot_number)
        if status:
            query = query.filter(Reservation.status == status)
        
        reservations = query.order_by(Reservation.created_at.desc()).limit(limit).all()
        
        reservation_data = []
        for res in reservations:
            reservation_data.append({
                "id": res.id,
                "slot_number": res.slot_number,
                "user_name": res.user_name,
                "user_email": res.user_email,
                "user_phone": res.user_phone,
                "vehicle_number": res.vehicle_number,
                "start_time": res.start_time.isoformat() if res.start_time else None,
                "end_time": res.end_time.isoformat() if res.end_time else None,
                "created_at": res.created_at.isoformat() if res.created_at else None,
                "status": res.status,
                "amount": res.amount,
                "payment_status": res.payment_status
            })
        
        return {
            "success": True,
            "data": reservation_data,
            "total": len(reservation_data)
        }
        
    except Exception as e:
        logger.error(f"Error getting reservations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get reservations")
