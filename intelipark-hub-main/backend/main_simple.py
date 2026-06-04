"""
Simple SmartPark Backend - Just for testing booking
"""
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn

app = FastAPI(title="SmartPark API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data for 80 slots
slots_data = []
for i in range(1, 81):
    slots_data.append({
        "id": i,
        "slot_number": f"SLOT_{i}",
        "status": "free" if i % 3 != 0 else "occupied",
        "assigned_at": None,
        "last_updated": "2025-10-05T23:40:00"
    })

reservations_data = []

class BookingRequest(BaseModel):
    slot_number: str
    booking_type: str
    duration_minutes: int = 60
    user_name: str = "Guest"
    user_email: str = "guest@example.com"
    start_time: str = None
    end_time: str = None

@app.get("/api/health")
async def health():
    return {"status": "ok", "message": "SmartPark API is running"}

@app.get("/api/get_slots")
async def get_slots():
    """Get all 80 parking slots"""
    stats = {
        "total_slots": 80,
        "free_slots": len([s for s in slots_data if s["status"] == "free"]),
        "occupied_slots": len([s for s in slots_data if s["status"] == "occupied"]),
        "reserved_slots": len([s for s in slots_data if s["status"] == "reserved"]),
        "occupancy_rate": len([s for s in slots_data if s["status"] != "free"]) / 80 * 100
    }
    
    return {
        "success": True,
        "data": {
            "slots": slots_data,
            "summary": stats
        }
    }

@app.post("/api/booking/availability")
async def check_availability(request: Dict[str, Any]):
    """Check slot availability"""
    slot_number = request.get("slot_number")
    slot = next((s for s in slots_data if s["slot_number"] == slot_number), None)
    
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    
    available = slot["status"] == "free"
    return {
        "available": available,
        "ml": {"prediction": "free" if available else "occupied", "confidence": 0.85},
        "reason": "Available" if available else "Currently occupied"
    }

@app.post("/api/booking/create")
async def create_booking(booking: BookingRequest):
    """Create a new booking"""
    slot = next((s for s in slots_data if s["slot_number"] == booking.slot_number), None)
    
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    
    if slot["status"] != "free":
        raise HTTPException(status_code=400, detail="Slot not available")
    
    # Update slot status
    slot["status"] = "reserved"
    
    # Create reservation
    reservation = {
        "id": len(reservations_data) + 1,
        "slot_number": booking.slot_number,
        "start_time": booking.start_time or "2025-10-05T23:45:00",
        "end_time": booking.end_time or "2025-10-06T00:45:00",
        "status": "active",
        "user_name": booking.user_name,
        "user_email": booking.user_email
    }
    reservations_data.append(reservation)
    
    return {
        "success": True,
        "data": reservation,
        "message": f"Slot {booking.slot_number} booked successfully"
    }

@app.get("/api/booking/reservations")
async def get_reservations(limit: int = 100):
    """Get all reservations"""
    return {
        "success": True,
        "data": reservations_data[:limit]
    }

@app.put("/api/booking/{reservation_id}/modify")
async def modify_reservation(reservation_id: int, request: Dict[str, Any]):
    """Modify a reservation"""
    reservation = next((r for r in reservations_data if r["id"] == reservation_id), None)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    if "end_time" in request:
        reservation["end_time"] = request["end_time"]
    
    return {"success": True, "message": "Reservation modified"}

@app.put("/api/booking/{reservation_id}/cancel")
async def cancel_reservation(reservation_id: int):
    """Cancel a reservation"""
    reservation = next((r for r in reservations_data if r["id"] == reservation_id), None)
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    # Free up the slot
    slot = next((s for s in slots_data if s["slot_number"] == reservation["slot_number"]), None)
    if slot:
        slot["status"] = "free"
    
    reservation["status"] = "cancelled"
    return {"success": True, "message": "Reservation cancelled"}

if __name__ == "__main__":
    print("🚀 Starting SmartPark Simple Backend...")
    print("📍 API will be available at: http://localhost:8000")
    print("📖 API docs at: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
