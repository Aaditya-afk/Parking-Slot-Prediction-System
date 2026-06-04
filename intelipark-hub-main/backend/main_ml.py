"""
SmartPark ML-Driven Backend - 70 Slots with Predictions, Timers & Reservations
Real-Time Parking Availability Prediction Using Spatio-Temporal ML Techniques
"""
import os
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import asyncio
from collections import defaultdict

# ==================== DATA MODELS ====================

class SlotStatus(BaseModel):
    slot_id: int
    status: str  # available, occupied, reserved, maintenance
    expected_free_time: Optional[str] = None
    reserved_until: Optional[str] = None
    prediction_confidence: Optional[float] = None
    zone: str = "A"  # A, B, C for spatial grouping
    occupied_duration: Optional[int] = None  # minutes
    
class ReservationRequest(BaseModel):
    slot_id: int
    duration_minutes: int = 20
    user_name: str = "Guest"
    
class OccupyRequest(BaseModel):
    slot_id: int
    estimated_duration: int = 30  # minutes

# ==================== IN-MEMORY DATABASE ====================

class ParkingDatabase:
    def __init__(self, total_slots=70):
        self.slots: Dict[int, Dict[str, Any]] = {}
        self.history: List[Dict[str, Any]] = []
        self.total_slots = total_slots
        self._initialize_slots()
        
    def _initialize_slots(self):
        """Initialize 70 slots with zones"""
        zones = ['A', 'B', 'C']
        for i in range(1, self.total_slots + 1):
            zone = zones[(i - 1) // 24]  # 24 slots per zone
            self.slots[i] = {
                "slot_id": i,
                "status": "available",
                "expected_free_time": None,
                "reserved_until": None,
                "prediction_confidence": round(random.uniform(0.6, 0.95), 2),
                "zone": zone,
                "occupied_duration": None,
                "last_updated": datetime.now().isoformat()
            }
            
    def get_all_slots(self) -> List[Dict[str, Any]]:
        return list(self.slots.values())
    
    def get_slot(self, slot_id: int) -> Dict[str, Any]:
        if slot_id not in self.slots:
            raise ValueError(f"Slot {slot_id} not found")
        return self.slots[slot_id]
    
    def update_slot(self, slot_id: int, updates: Dict[str, Any]):
        if slot_id not in self.slots:
            raise ValueError(f"Slot {slot_id} not found")
        self.slots[slot_id].update(updates)
        self.slots[slot_id]["last_updated"] = datetime.now().isoformat()
        
        # Log to history
        self.history.append({
            "slot_id": slot_id,
            "timestamp": datetime.now().isoformat(),
            "status": self.slots[slot_id]["status"],
            "action": "update"
        })
    
    def get_statistics(self) -> Dict[str, Any]:
        available = sum(1 for s in self.slots.values() if s["status"] == "available")
        occupied = sum(1 for s in self.slots.values() if s["status"] == "occupied")
        reserved = sum(1 for s in self.slots.values() if s["status"] == "reserved")
        maintenance = sum(1 for s in self.slots.values() if s["status"] == "maintenance")
        
        return {
            "total_slots": self.total_slots,
            "available": available,
            "occupied": occupied,
            "reserved": reserved,
            "maintenance": maintenance,
            "occupancy_rate": round((occupied + reserved) / self.total_slots * 100, 1)
        }

# ==================== ML PREDICTION ENGINE ====================

class MLPredictor:
    """Simulated ML model for slot availability prediction"""
    
    def predict_slot_availability(self, slot_id: int, minutes_ahead: int = 15) -> Dict[str, Any]:
        """Predict if a slot will be available in X minutes"""
        # Simulate ML prediction based on time patterns
        current_hour = datetime.now().hour
        
        # Peak hours (9-11 AM, 5-7 PM) = lower availability
        is_peak = (9 <= current_hour <= 11) or (17 <= current_hour <= 19)
        
        # Base probability
        base_prob = 0.4 if is_peak else 0.7
        
        # Add randomness
        confidence = round(base_prob + random.uniform(-0.2, 0.2), 2)
        confidence = max(0.1, min(0.95, confidence))
        
        return {
            "slot_id": slot_id,
            "minutes_ahead": minutes_ahead,
            "probability_available": confidence,
            "predicted_status": "available" if confidence > 0.6 else "occupied",
            "confidence_level": "high" if confidence > 0.75 else "medium" if confidence > 0.5 else "low"
        }
    
    def get_recommendations(self, db: ParkingDatabase) -> List[Dict[str, Any]]:
        """Recommend best slots based on availability and location"""
        available_slots = [s for s in db.get_all_slots() if s["status"] == "available"]
        
        # Sort by prediction confidence and zone proximity
        recommendations = []
        for slot in available_slots[:5]:  # Top 5
            score = slot["prediction_confidence"] * 100
            if slot["zone"] == "A":  # Closest to entrance
                score += 10
            
            recommendations.append({
                "slot_id": slot["slot_id"],
                "zone": slot["zone"],
                "score": round(score, 1),
                "reason": f"Zone {slot['zone']}, {int(slot['prediction_confidence']*100)}% confidence"
            })
        
        return sorted(recommendations, key=lambda x: x["score"], reverse=True)

# ==================== FASTAPI APP ====================

app = FastAPI(title="SmartPark ML API", version="2.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database and ML predictor
db = ParkingDatabase(total_slots=70)
ml_predictor = MLPredictor()

# WebSocket connections
active_connections: List[WebSocket] = []

# ==================== BACKGROUND TASKS ====================

async def timer_manager():
    """Background task to manage countdowns and auto-release"""
    while True:
        await asyncio.sleep(1)  # Check every second
        now = datetime.now()
        
        for slot_id, slot in db.slots.items():
            updated = False
            
            # Check occupied slots
            if slot["status"] == "occupied" and slot["expected_free_time"]:
                expected_time = datetime.fromisoformat(slot["expected_free_time"])
                if now >= expected_time:
                    db.update_slot(slot_id, {
                        "status": "available",
                        "expected_free_time": None,
                        "occupied_duration": None
                    })
                    updated = True
            
            # Check reserved slots
            if slot["status"] == "reserved" and slot["reserved_until"]:
                reserved_time = datetime.fromisoformat(slot["reserved_until"])
                if now >= reserved_time:
                    db.update_slot(slot_id, {
                        "status": "available",
                        "reserved_until": None
                    })
                    updated = True
            
            # Broadcast update
            if updated:
                await broadcast_slot_update(slot_id)

async def broadcast_slot_update(slot_id: int):
    """Send slot update to all connected WebSocket clients"""
    if active_connections:
        slot = db.get_slot(slot_id)
        message = json.dumps({
            "type": "slot_update",
            "data": slot,
            "timestamp": datetime.now().isoformat()
        })
        
        disconnected = []
        for connection in active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            active_connections.remove(conn)

# ==================== API ENDPOINTS ====================

@app.on_event("startup")
async def startup_event():
    """Start background tasks"""
    asyncio.create_task(timer_manager())

@app.get("/api/health")
async def health():
    return {"status": "ok", "message": "SmartPark ML API is running"}

@app.get("/api/slots")
async def get_all_slots():
    """Get all 70 slots with current status"""
    slots = db.get_all_slots()
    stats = db.get_statistics()
    
    return {
        "success": True,
        "data": {
            "slots": slots,
            "statistics": stats
        }
    }

@app.get("/api/slots/{slot_id}")
async def get_slot(slot_id: int):
    """Get specific slot details"""
    try:
        slot = db.get_slot(slot_id)
        return {"success": True, "data": slot}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/slots/reserve/{slot_id}")
async def reserve_slot(slot_id: int, request: ReservationRequest):
    """Reserve a slot for specified duration"""
    try:
        slot = db.get_slot(slot_id)
        
        if slot["status"] != "available":
            raise HTTPException(status_code=400, detail="Slot not available")
        
        reserved_until = datetime.now() + timedelta(minutes=request.duration_minutes)
        
        db.update_slot(slot_id, {
            "status": "reserved",
            "reserved_until": reserved_until.isoformat()
        })
        
        await broadcast_slot_update(slot_id)
        
        return {
            "success": True,
            "message": f"Slot {slot_id} reserved for {request.duration_minutes} minutes",
            "reserved_until": reserved_until.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/slots/occupy/{slot_id}")
async def occupy_slot(slot_id: int, request: OccupyRequest):
    """Mark slot as occupied with estimated duration"""
    try:
        slot = db.get_slot(slot_id)
        
        if slot["status"] not in ["available", "reserved"]:
            raise HTTPException(status_code=400, detail="Slot cannot be occupied")
        
        expected_free = datetime.now() + timedelta(minutes=request.estimated_duration)
        
        db.update_slot(slot_id, {
            "status": "occupied",
            "expected_free_time": expected_free.isoformat(),
            "occupied_duration": request.estimated_duration,
            "reserved_until": None
        })
        
        await broadcast_slot_update(slot_id)
        
        return {
            "success": True,
            "message": f"Slot {slot_id} occupied, expected free at {expected_free.strftime('%H:%M')}",
            "expected_free_time": expected_free.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/slots/free/{slot_id}")
async def free_slot(slot_id: int):
    """Free up a slot"""
    try:
        db.update_slot(slot_id, {
            "status": "available",
            "expected_free_time": None,
            "reserved_until": None,
            "occupied_duration": None
        })
        
        await broadcast_slot_update(slot_id)
        
        return {"success": True, "message": f"Slot {slot_id} is now available"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/api/predictions")
async def get_predictions(minutes_ahead: int = 15):
    """Get ML predictions for all slots"""
    predictions = []
    for slot_id in range(1, 71):
        pred = ml_predictor.predict_slot_availability(slot_id, minutes_ahead)
        predictions.append(pred)
    
    return {
        "success": True,
        "data": {
            "predictions": predictions,
            "generated_at": datetime.now().isoformat()
        }
    }

@app.get("/api/recommendations")
async def get_recommendations():
    """Get recommended slots based on ML predictions"""
    recommendations = ml_predictor.get_recommendations(db)
    
    return {
        "success": True,
        "data": {
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat()
        }
    }

@app.get("/api/analytics")
async def get_analytics():
    """Get occupancy analytics and trends"""
    stats = db.get_statistics()
    
    # Simulate hourly data
    hourly_data = []
    for hour in range(24):
        occupancy = random.randint(20, 65) if 9 <= hour <= 18 else random.randint(5, 25)
        hourly_data.append({
            "hour": hour,
            "occupancy": occupancy,
            "available": 70 - occupancy
        })
    
    # Zone distribution
    zone_stats = defaultdict(lambda: {"available": 0, "occupied": 0, "reserved": 0})
    for slot in db.get_all_slots():
        zone_stats[slot["zone"]][slot["status"]] += 1
    
    return {
        "success": True,
        "data": {
            "current_stats": stats,
            "hourly_occupancy": hourly_data,
            "zone_distribution": dict(zone_stats),
            "generated_at": datetime.now().isoformat()
        }
    }

@app.websocket("/ws/realtime")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

# ==================== ADMIN ENDPOINTS ====================

@app.post("/api/admin/reset")
async def reset_all_slots():
    """Reset all slots to available (admin)"""
    for slot_id in range(1, 71):
        db.update_slot(slot_id, {
            "status": "available",
            "expected_free_time": None,
            "reserved_until": None,
            "occupied_duration": None
        })
    
    return {"success": True, "message": "All slots reset to available"}

@app.post("/api/admin/simulate")
async def simulate_parking_activity():
    """Simulate random parking activity (admin)"""
    # Randomly occupy/reserve some slots
    for _ in range(random.randint(5, 15)):
        slot_id = random.randint(1, 70)
        action = random.choice(["occupy", "reserve"])
        
        if action == "occupy":
            duration = random.randint(15, 45)
            expected_free = datetime.now() + timedelta(minutes=duration)
            db.update_slot(slot_id, {
                "status": "occupied",
                "expected_free_time": expected_free.isoformat(),
                "occupied_duration": duration
            })
        else:
            duration = random.randint(10, 30)
            reserved_until = datetime.now() + timedelta(minutes=duration)
            db.update_slot(slot_id, {
                "status": "reserved",
                "reserved_until": reserved_until.isoformat()
            })
        
        await broadcast_slot_update(slot_id)
    
    return {"success": True, "message": "Simulated parking activity"}

# ==================== MAIN ====================

if __name__ == "__main__":
    print("🚀 Starting SmartPark ML-Driven Backend...")
    print("📍 API: http://localhost:8000")
    print("📖 Docs: http://localhost:8000/docs")
    print("🧠 ML Predictions: Enabled")
    print("⏱️  Countdown Timers: Active")
    print("🎯 70 Slots: Ready")
    uvicorn.run(app, host="0.0.0.0", port=8000)
