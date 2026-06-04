"""
SmartPark FastAPI Backend - 3 Slots System
Main application entry point for IoT parking management
"""
import os
import logging
import json
from contextlib import asynccontextmanager
from datetime import datetime
import asyncio
from typing import Dict, Any, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Routers
from routes.slots import router as slots_router
from routes.events import router as events_router
from routes.gate import router as gate_router
from routes.reservations_3slot import router as reservations_router
from routes.bookings_adv import router as bookings_adv_router
from routes.feedback import router as feedback_router
from routes.admin_simple import router as admin_simple_router

from database import init_db as init_legacy_db, SessionLocal
from database_entry_exit import init_db as init_entry_exit_db
# ML predictor removed to avoid numpy dependency
from auto_expire_slots import auto_expire_slots

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        dead = []
        for ws in self.active_connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


@asynccontextmanager
async def lifecycle(app: FastAPI):
    # Initialize both databases: legacy (3-slot) and scalable entry/exit
    init_legacy_db()
    init_entry_exit_db()
    app.state.manager = manager
    app.state._stop_bg = False

    async def _predictions_task():
        while not app.state._stop_bg:
            try:
                # Simple prediction broadcast without ML dependencies
                msg = json.dumps({
                    "type": "ml_prediction_update", 
                    "data": {"predictions": [], "horizon_minutes": 15},
                    "timestamp": datetime.utcnow().isoformat(),
                })
                await manager.broadcast(msg)
            except Exception:
                pass
            await asyncio.sleep(30)

    app.state._bg_task = asyncio.create_task(_predictions_task())
    app.state._expire_task = asyncio.create_task(auto_expire_slots())
    yield
    app.state._stop_bg = True
    try:
        app.state._bg_task.cancel()
        app.state._expire_task.cancel()
    except Exception:
        pass


app = FastAPI(
    title="SmartPark IoT Backend",
    description="Backend API for SmartPark IoT Parking Management System",
    version="2.1.0",
    lifespan=lifecycle,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(slots_router)
app.include_router(events_router)
app.include_router(gate_router)
app.include_router(reservations_router)
app.include_router(bookings_adv_router)
app.include_router(feedback_router)
app.include_router(admin_simple_router)


@app.get("/")
async def root():
    return {
        "message": "SmartPark IoT Backend API",
        "system": "Parking Management",
        "version": "2.1.0",
        "endpoints": {
            "slots": "/api/slots",
            "reserve": "/api/reserve_slot",
            "booking": "/api/booking/*",
            "websocket": "/ws/realtime",
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/health")
async def health():
    return {
        "status": "healthy",
        "active_websockets": len(manager.active_connections),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.websocket("/ws/realtime")
async def ws_realtime(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await manager.send_personal_message(
            json.dumps({"type": "connection", "status": "connected", "timestamp": datetime.utcnow().isoformat()}),
            websocket,
        )
        while True:
            _ = await websocket.receive_text()
            # For now we keep-alive; real broadcasts originate from routes/services
    except WebSocketDisconnect:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
