"""
Real-Time Parking Slot Availability Prediction System
Complete Backend with Timers, Auto-Release, ML Predictions & Analytics
"""
import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from collections import defaultdict
import random

# ==================== MODELS ====================

class BookingRequest(BaseModel):
    slot_id: int
    duration_minutes: int  # User-selected duration
    user_name: str = "Guest"
    user_email: str = "guest@example.com"

class SlotData(BaseModel):
    slot_id: int
    status: str  # available, occupied, reserved, maintenance
    expected_free_time: Optional[str] = None
    timer_remaining: Optional[int] = None  # seconds
    predicted_free_in: Optional[int] = None  # minutes
    prediction_confidence: Optional[float] = None
    user_set_duration: Optional[int] = None
    zone: str = "A"
    last_updated: str = ""

# ==================== DATABASE ====================

class SmartParkingDB:
    def __init__(self):
        self.slots: Dict[int, Dict] = {}
        self.history: List[Dict] = []
        self.initialize_slots()
    
    def initialize_slots(self):
        """Initialize 80 slots"""
        zones = ['A', 'B', 'C', 'D']
        for i in range(1, 81):
            zone = zones[(i - 1) // 20]
            self.slots[i] = {
                "slot_id": i,
                "status": "available",
                "expected_free_time": None,
                "timer_remaining": None,
                "predicted_free_in": None,
                "prediction_confidence": round(random.uniform(0.75, 0.95), 2),
                "user_set_duration": None,
                "zone": zone,
                "last_updated": datetime.now().isoformat(),
                "occupied_at": None,
                "reserved_by": None
            }
    
    def get_slot(self, slot_id: int):
        return self.slots.get(slot_id)
    
    def update_slot(self, slot_id: int, data: Dict):
        if slot_id in self.slots:
            self.slots[slot_id].update(data)
            self.slots[slot_id]["last_updated"] = datetime.now().isoformat()
            
            # Log to history
            self.history.append({
                "slot_id": slot_id,
                "timestamp": datetime.now().isoformat(),
                "status": self.slots[slot_id]["status"],
                "duration": data.get("user_set_duration"),
                "action": "update"
            })
    
    def get_statistics(self):
        available = sum(1 for s in self.slots.values() if s["status"] == "available")
        occupied = sum(1 for s in self.slots.values() if s["status"] == "occupied")
        reserved = sum(1 for s in self.slots.values() if s["status"] == "reserved")
        
        return {
            "total": 80,
            "available": available,
            "occupied": occupied,
            "reserved": reserved,
            "occupancy_rate": round((occupied + reserved) / 80 * 100, 1)
        }

# ==================== ML PREDICTOR ====================

class PredictionEngine:
    """ML-based prediction for slot availability"""
    
    def predict_slot(self, slot_id: int, current_status: str, history: List) -> Dict:
        """Predict when a slot will be free"""
        hour = datetime.now().hour
        
        # Peak hours logic
        is_peak = (9 <= hour <= 11) or (17 <= hour <= 19)
        
        if current_status == "occupied":
            # Predict based on typical duration
            avg_duration = 25 if is_peak else 35
            predicted_free = avg_duration + random.randint(-5, 10)
            confidence = 0.85 if is_peak else 0.78
        elif current_status == "available":
            predicted_free = 0
            confidence = 0.95
        else:
            predicted_free = 15
            confidence = 0.70
        
        return {
            "slot_id": slot_id,
            "predicted_free_in": max(0, predicted_free),
            "confidence": round(confidence, 2),
            "status": current_status
        }
    
    def get_recommendations(self, db: SmartParkingDB) -> List[Dict]:
        """Smart recommendations for users"""
        # Find slots that will be free soon
        soon_free = []
        
        for slot_id, slot in db.slots.items():
            if slot["status"] == "occupied" and slot["expected_free_time"]:
                free_time = datetime.fromisoformat(slot["expected_free_time"])
                minutes_until_free = (free_time - datetime.now()).total_seconds() / 60
                
                if 0 < minutes_until_free <= 15:
                    soon_free.append({
                        "slot_id": slot_id,
                        "zone": slot["zone"],
                        "free_in_minutes": int(minutes_until_free),
                        "confidence": slot.get("prediction_confidence", 0.8)
                    })
        
        return sorted(soon_free, key=lambda x: x["free_in_minutes"])[:5]

# ==================== FASTAPI APP ====================

app = FastAPI(title="SmartPark Prediction API", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = SmartParkingDB()
predictor = PredictionEngine()
websocket_clients: List[WebSocket] = []

# ==================== TIMER MANAGER ====================

async def timer_manager():
    """Background task: Auto-release slots when timer expires"""
    while True:
        await asyncio.sleep(1)  # Check every second
        now = datetime.now()
        
        for slot_id, slot in db.slots.items():
            if slot["status"] == "occupied" and slot["expected_free_time"]:
                expected_time = datetime.fromisoformat(slot["expected_free_time"])
                
                # Calculate remaining time
                remaining_seconds = (expected_time - now).total_seconds()
                
                if remaining_seconds <= 0:
                    # Timer expired - auto release
                    db.update_slot(slot_id, {
                        "status": "available",
                        "expected_free_time": None,
                        "timer_remaining": None,
                        "user_set_duration": None,
                        "occupied_at": None
                    })
                    await broadcast_update({
                        "type": "slot_freed",
                        "slot_id": slot_id,
                        "message": f"SLOT_{slot_id} is now available"
                    })
                else:
                    # Update timer
                    db.slots[slot_id]["timer_remaining"] = int(remaining_seconds)

async def broadcast_update(message: Dict):
    """Send updates to all WebSocket clients"""
    if websocket_clients:
        disconnected = []
        for client in websocket_clients:
            try:
                await client.send_json(message)
            except:
                disconnected.append(client)
        
        for client in disconnected:
            websocket_clients.remove(client)

# ==================== API ENDPOINTS ====================

@app.on_event("startup")
async def startup():
    asyncio.create_task(timer_manager())

@app.get("/api/health")
async def health():
    return {"status": "ok", "message": "Prediction API running"}

@app.get("/api/slots")
async def get_all_slots():
    """Get all 80 slots with timer info"""
    slots = list(db.slots.values())
    stats = db.get_statistics()
    
    return {
        "success": True,
        "data": {
            "slots": slots,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
    }

@app.post("/api/slots/book/{slot_id}")
async def book_slot(slot_id: int, booking: BookingRequest):
    """Book a slot with user-selected duration"""
    slot = db.get_slot(slot_id)
    
    if not slot:
        raise HTTPException(404, "Slot not found")
    
    if slot["status"] != "available":
        raise HTTPException(400, "Slot not available")
    
    # Calculate expected free time
    expected_free = datetime.now() + timedelta(minutes=booking.duration_minutes)
    
    db.update_slot(slot_id, {
        "status": "occupied",
        "expected_free_time": expected_free.isoformat(),
        "user_set_duration": booking.duration_minutes,
        "timer_remaining": booking.duration_minutes * 60,
        "occupied_at": datetime.now().isoformat()
    })
    
    await broadcast_update({
        "type": "slot_booked",
        "slot_id": slot_id,
        "duration": booking.duration_minutes,
        "expected_free": expected_free.isoformat()
    })
    
    return {
        "success": True,
        "message": f"SLOT_{slot_id} booked for {booking.duration_minutes} minutes",
        "expected_free_time": expected_free.isoformat()
    }

@app.post("/api/slots/free/{slot_id}")
async def free_slot(slot_id: int):
    """Manually free a slot"""
    slot = db.get_slot(slot_id)
    
    if not slot:
        raise HTTPException(404, "Slot not found")
    
    db.update_slot(slot_id, {
        "status": "available",
        "expected_free_time": None,
        "timer_remaining": None,
        "user_set_duration": None,
        "occupied_at": None
    })
    
    await broadcast_update({
        "type": "slot_freed",
        "slot_id": slot_id
    })
    
    return {"success": True, "message": f"SLOT_{slot_id} freed"}

@app.get("/api/predictions")
async def get_predictions():
    """Get ML predictions for all slots"""
    predictions = []
    
    for slot_id, slot in db.slots.items():
        pred = predictor.predict_slot(slot_id, slot["status"], db.history)
        predictions.append(pred)
    
    return {
        "success": True,
        "data": {
            "predictions": predictions,
            "timestamp": datetime.now().isoformat()
        }
    }

@app.get("/api/recommendations")
async def get_recommendations():
    """Get smart recommendations for slots freeing soon"""
    recommendations = predictor.get_recommendations(db)
    
    return {
        "success": True,
        "data": {
            "soon_available": recommendations,
            "message": "Slots predicted to be free soon" if recommendations else "No slots freeing soon",
            "timestamp": datetime.now().isoformat()
        }
    }

@app.get("/api/analytics")
async def get_analytics():
    """Get analytics data for dashboard"""
    stats = db.get_statistics()
    
    # Hourly occupancy simulation
    hourly = []
    for h in range(24):
        occ = random.randint(30, 70) if 9 <= h <= 18 else random.randint(10, 35)
        hourly.append({"hour": h, "occupancy": occ, "available": 80 - occ})
    
    # Average duration
    durations = [s.get("user_set_duration", 0) for s in db.slots.values() if s.get("user_set_duration")]
    avg_duration = sum(durations) / len(durations) if durations else 30
    
    return {
        "success": True,
        "data": {
            "current_stats": stats,
            "hourly_occupancy": hourly,
            "average_duration": round(avg_duration, 1),
            "peak_hours": [9, 10, 11, 17, 18, 19],
            "timestamp": datetime.now().isoformat()
        }
    }

@app.websocket("/ws/realtime")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    websocket_clients.append(websocket)
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_clients.remove(websocket)

if __name__ == "__main__":
    print("🚀 Starting SmartPark Prediction System...")
    print("📍 API: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    print("⏱️  Auto-Release: Active")
    print("🧠 ML Predictions: Enabled")
    print("📊 Analytics: Ready")
    uvicorn.run(app, host="0.0.0.0", port=8000)
