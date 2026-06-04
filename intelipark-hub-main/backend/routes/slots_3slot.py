"""
API routes for 3-slot parking management - SmartPark Entry/Exit System
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from ..database_entry_exit import get_db, get_slot_stats, log_system_event
from ..models.parking import ParkingSlot, Reservation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["slots"])

@router.get("/get_slots")
async def get_all_slots(db: Session = Depends(get_db)):
    """Get all 3 parking slots with current status - Frontend endpoint"""
    try:
        # Ensure we have exactly 3 slots
        slots = db.query(ParkingSlot).order_by(ParkingSlot.slot_number).all()
        
        # If no slots exist, create them
        if not slots:
            await initialize_3_slots(db)
            slots = db.query(ParkingSlot).order_by(ParkingSlot.slot_number).all()
        
        # Format for frontend compatibility (exactly 3 slots)
        slot_data = []
        for i, slot in enumerate(slots[:3]):  # Ensure only 3 slots
            slot_data.append({
                "id": slot.id,
                "slot_number": slot.slot_number,
                "status": slot.status.upper(),  # Convert to uppercase for frontend compatibility
                "assigned_at": slot.assigned_at.isoformat() if slot.assigned_at else None,
                "last_updated": slot.last_updated.isoformat() if slot.last_updated else None,
                # Frontend compatibility fields
                "is_occupied": slot.status == "occupied",
                "is_reserved": slot.status == "reserved",
                "is_free": slot.status == "free"
            })
        
        # Calculate summary for exactly 3 slots
        total_slots = 3
        free_count = len([s for s in slot_data if s["status"] == "free"])
        occupied_count = len([s for s in slot_data if s["status"] == "occupied"])
        reserved_count = len([s for s in slot_data if s["status"] == "reserved"])
        occupancy_rate = round((occupied_count / total_slots) * 100, 1)
        
        return {
            "success": True,
            "data": {
                "slots": slot_data,
                "summary": {
                    "total_slots": total_slots,
                    "free_slots": free_count,
                    "occupied_slots": occupied_count,
                    "reserved_slots": reserved_count,
                    "occupancy_rate": occupancy_rate
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting slots: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/parking_overview")
async def get_parking_overview(db: Session = Depends(get_db)):
    """Get parking overview with statistics - Alternative endpoint for frontend"""
    try:
        # Get slot data
        slots_response = await get_all_slots(db)
        slots_data = slots_response["data"]
        
        # Get recent activity (last 10 events)
        from ..models.parking import CarEvent
        recent_events = db.query(CarEvent).order_by(
            CarEvent.timestamp.desc()
        ).limit(10).all()
        
        activity_feed = []
        for event in recent_events:
            activity_feed.append({
                "id": event.id,
                "event_type": event.event_type,
                "timestamp": event.timestamp.isoformat(),
                "assigned_slot_id": event.assigned_slot_id,
                "processing_status": event.processing_status
            })
        
        return {
            "success": True,
            "data": {
                "total_slots": 3,
                "free_slots": slots_data["summary"]["free_slots"],
                "occupied_slots": slots_data["summary"]["occupied_slots"],
                "reserved_slots": slots_data["summary"]["reserved_slots"],
                "occupancy_rate": slots_data["summary"]["occupancy_rate"],
                "slots": slots_data["slots"],
                "recent_activity": activity_feed
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting parking overview: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/reserve_slot")
async def reserve_slot(reservation_data: Dict[str, Any], db: Session = Depends(get_db)):
    """Reserve a specific parking slot"""
    try:
        slot_id = reservation_data.get("slot_id")
        user_name = reservation_data.get("user_name", "Anonymous")
        user_email = reservation_data.get("user_email", "")
        user_phone = reservation_data.get("user_phone", "")
        vehicle_number = reservation_data.get("vehicle_number", "")
        duration_hours = reservation_data.get("duration_hours", 2)
        
        if not slot_id:
            raise HTTPException(status_code=400, detail="Slot ID is required")
        
        # Check if slot exists and is available
        slot = db.query(ParkingSlot).filter(ParkingSlot.id == slot_id).first()
        if not slot:
            raise HTTPException(status_code=404, detail="Slot not found")
        
        if slot.status != "free":
            raise HTTPException(status_code=409, detail=f"Slot {slot.slot_number} is not available")
        
        # Check for existing active reservations for this slot
        existing_reservation = db.query(Reservation).filter(
            Reservation.slot_id == slot_id,
            Reservation.status == "active"
        ).first()
        
        if existing_reservation:
            raise HTTPException(status_code=409, detail="Slot already has an active reservation")
        
        # Create reservation
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(hours=duration_hours)
        
        reservation = Reservation(
            slot_id=slot_id,
            user_name=user_name,
            user_email=user_email,
            user_phone=user_phone,
            vehicle_number=vehicle_number,
            start_time=start_time,
            end_time=end_time,
            status="active",
            amount=duration_hours * 5.0  # $5 per hour
        )
        
        # Update slot status
        slot.status = "reserved"
        slot.last_updated = datetime.utcnow()
        
        db.add(reservation)
        db.commit()
        db.refresh(reservation)
        
        logger.info(f"🅿️ Reserved {slot.slot_number} for {user_name}")
        
        # Log system event
        log_system_event(db, "INFO", "reservations", f"Slot {slot.slot_number} reserved by {user_name}")
        
        return {
            "success": True,
            "message": "Slot reserved successfully",
            "data": {
                "reservation_id": reservation.id,
                "slot_id": slot_id,
                "slot_number": slot.slot_number,
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
        logger.error(f"❌ Error creating reservation: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create reservation")

@router.post("/release_slot")
async def release_slot(release_data: Dict[str, Any], db: Session = Depends(get_db)):
    """Release a parking slot reservation"""
    try:
        slot_id = release_data.get("slot_id")
        reservation_id = release_data.get("reservation_id")
        
        if not slot_id and not reservation_id:
            raise HTTPException(status_code=400, detail="Either slot_id or reservation_id is required")
        
        # Find reservation
        if reservation_id:
            reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
        else:
            reservation = db.query(Reservation).filter(
                Reservation.slot_id == slot_id,
                Reservation.status == "active"
            ).first()
        
        if not reservation:
            raise HTTPException(status_code=404, detail="Active reservation not found")
        
        # Find slot
        slot = db.query(ParkingSlot).filter(ParkingSlot.id == reservation.slot_id).first()
        if not slot:
            raise HTTPException(status_code=404, detail="Slot not found")
        
        # Update reservation status
        reservation.status = "completed"
        reservation.end_time = datetime.utcnow()
        
        # Update slot status
        slot.status = "free"
        slot.assigned_at = None
        slot.last_updated = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"🚗 Released {slot.slot_number} (reservation {reservation.id})")
        
        # Log system event
        log_system_event(db, "INFO", "reservations", f"Slot {slot.slot_number} released")
        
        return {
            "success": True,
            "message": "Slot released successfully",
            "data": {
                "reservation_id": reservation.id,
                "slot_id": slot.id,
                "slot_number": slot.slot_number,
                "completed_at": reservation.end_time.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error releasing slot: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to release slot")

@router.get("/reservations")
async def get_reservations(
    user_email: str = None,
    slot_id: int = None,
    status: str = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get reservations with optional filters"""
    try:
        query = db.query(Reservation)
        
        if user_email:
            query = query.filter(Reservation.user_email == user_email)
        if slot_id:
            query = query.filter(Reservation.slot_id == slot_id)
        if status:
            query = query.filter(Reservation.status == status)
        
        reservations = query.order_by(Reservation.created_at.desc()).limit(limit).all()
        
        reservation_data = []
        for res in reservations:
            # Get slot info
            slot = db.query(ParkingSlot).filter(ParkingSlot.id == res.slot_id).first()
            
            reservation_data.append({
                "id": res.id,
                "slot_id": res.slot_id,
                "slot_number": slot.slot_number if slot else f"SLOT_{res.slot_id}",
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
        logger.error(f"❌ Error getting reservations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get reservations")

@router.get("/slots/{slot_id}")
async def get_specific_slot(slot_id: int, db: Session = Depends(get_db)):
    """Get specific slot details"""
    try:
        slot = db.query(ParkingSlot).filter(ParkingSlot.id == slot_id).first()
        
        if not slot:
            raise HTTPException(status_code=404, detail="Slot not found")
        
        # Get active reservation if any
        active_reservation = db.query(Reservation).filter(
            Reservation.slot_id == slot_id,
            Reservation.status == "active"
        ).first()
        
        slot_data = {
            "id": slot.id,
            "slot_number": slot.slot_number,
            "status": slot.status.upper(),  # Convert to uppercase for frontend compatibility
            "assigned_at": slot.assigned_at.isoformat() if slot.assigned_at else None,
            "last_updated": slot.last_updated.isoformat() if slot.last_updated else None,
            "created_at": slot.created_at.isoformat() if slot.created_at else None,
            "active_reservation": None
        }
        
        if active_reservation:
            slot_data["active_reservation"] = {
                "id": active_reservation.id,
                "user_name": active_reservation.user_name,
                "start_time": active_reservation.start_time.isoformat(),
                "end_time": active_reservation.end_time.isoformat(),
                "vehicle_number": active_reservation.vehicle_number
            }
        
        return {
            "success": True,
            "data": slot_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting slot {slot_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def initialize_3_slots(db: Session):
    """Initialize exactly 3 parking slots if they don't exist"""
    try:
        for i in range(1, 4):  # Create slots 1, 2, 3
            existing_slot = db.query(ParkingSlot).filter(
                ParkingSlot.slot_number == f"SLOT_{i}"
            ).first()
            
            if not existing_slot:
                slot = ParkingSlot(
                    slot_number=f"SLOT_{i}",
                    status="free"
                )
                db.add(slot)
        
        db.commit()
        logger.info("✅ Initialized 3 parking slots")
        
    except Exception as e:
        logger.error(f"❌ Error initializing slots: {e}")
        db.rollback()

@router.post("/initialize_slots")
async def initialize_slots_endpoint(db: Session = Depends(get_db)):
    """Manually initialize 3 parking slots (admin endpoint)"""
    try:
        await initialize_3_slots(db)
        
        return {
            "success": True,
            "message": "3 parking slots initialized successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error in initialize endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize slots")
