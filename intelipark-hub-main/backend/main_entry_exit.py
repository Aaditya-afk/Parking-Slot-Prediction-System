"""
SmartPark FastAPI Backend - Entry/Exit Detection System
Main application entry point for 3-slot IoT parking management
"""

import os
import asyncio
import logging
import json
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import routes
from routes.events import router as events_router
from routes.gate_control import router as gate_router
from routes.slots_3slot import router as slots_router

# ML and simulation (software-only mode)
from ml.predictor import predictor as rf_predictor
from ml.simulator import backfill_history, tick_once
from database_entry_exit import SessionLocal

# Import database
from database_entry_exit import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smartpark_entry_exit.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# WebSocket connection manager for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"🔌 WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"🔌 WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"❌ Error sending personal message: {e}")

    async def broadcast(self, message: str):
        """Broadcast message to all connected WebSocket clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"❌ Error broadcasting to WebSocket: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            self.active_connections.remove(conn)

    async def broadcast_slot_update(self, slot_data: Dict[str, Any]):
        """Broadcast slot update to all connected clients"""
        message = json.dumps({
            "type": "slot_update",
            "data": slot_data,
            "timestamp": datetime.utcnow().isoformat()
        })
        await self.broadcast(message)

    async def broadcast_event(self, event_type: str, event_data: Dict[str, Any]):
        """Broadcast car events to all connected clients"""
        message = json.dumps({
            "type": "car_event",
            "event_type": event_type,
            "data": event_data,
            "timestamp": datetime.utcnow().isoformat()
        })
        await self.broadcast(message)

manager = ConnectionManager()

# Application lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting SmartPark Backend (Entry/Exit Detection System)...")
    
    # Initialize database
    try:
        init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise
    
    # Store connection manager in app state
    app.state.websocket_manager = manager

    # Software-only simulation mode (no hardware)
    simulate = os.getenv("SIMULATE_DATA", "false").lower() == "true"
    sim_days = int(os.getenv("SIM_HISTORY_DAYS", "30"))
    sim_interval = int(os.getenv("SIM_LIVE_INTERVAL_SECONDS", "15"))

    app.state.background_tasks = []

    if simulate:
        logger.info("🧪 Simulation mode enabled (software-only)")
        # Backfill + train model once at startup
        try:
            db = SessionLocal()
            written = backfill_history(db, days=sim_days, step_minutes=5)
            logger.info(f"🗂️ Backfilled simulated history samples: {written}")
        except Exception as e:
            logger.error(f"❌ Simulator backfill failed: {e}")
        finally:
            try:
                db.close()
            except Exception:
                pass

        # Train RF predictor on simulated data
        try:
            db = SessionLocal()
            ok, msg = rf_predictor.train_model(db, days_back=sim_days)
            if ok:
                logger.info(f"🤖 ML model trained: {msg}")
            else:
                logger.warning(f"⚠️ ML training warning: {msg}")
        except Exception as e:
            logger.error(f"❌ ML training failed: {e}")
        finally:
            try:
                db.close()
            except Exception:
                pass

        async def _simulator_loop():
            while True:
                try:
                    db = SessionLocal()
                    snapshot = tick_once(db)
                    # Broadcast slot snapshot as regular slot_update for UI
                    if hasattr(app.state, "broadcast_update"):
                        await app.state.broadcast_update("slot_update", {
                            "slots": [
                                {"slot_number": k, "status": v} for k, v in snapshot.items()
                            ]
                        })
                except Exception as e:
                    logger.error(f"❌ Simulator loop error: {e}")
                finally:
                    try:
                        db.close()
                    except Exception:
                        pass
                await asyncio.sleep(sim_interval)

        async def _prediction_loop():
            # Periodically compute predictions and push via WS
            while True:
                try:
                    db = SessionLocal()
                    preds = rf_predictor.predict_all_slots(db, minutes_ahead=15)
                    payload = {
                        "horizon_minutes": 15,
                        "predictions": preds
                    }
                    if hasattr(app.state, "broadcast_update"):
                        await app.state.broadcast_update("ml_prediction_update", payload)
                except Exception as e:
                    logger.error(f"❌ Prediction loop error: {e}")
                finally:
                    try:
                        db.close()
                    except Exception:
                        pass
                await asyncio.sleep(max(10, sim_interval))

        # Start background tasks
        app.state.background_tasks.append(asyncio.create_task(_simulator_loop()))
        app.state.background_tasks.append(asyncio.create_task(_prediction_loop()))
    
    logger.info("✅ SmartPark Backend started successfully")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down SmartPark Backend...")
    # Cancel background tasks if any
    tasks = getattr(app.state, "background_tasks", [])
    for t in tasks:
        try:
            t.cancel()
        except Exception:
            pass

# Create FastAPI application
app = FastAPI(
    title="SmartPark IoT Backend",
    description="Backend API for SmartPark IoT Parking Management System (Entry/Exit Detection)",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development
        "http://localhost:5173",  # Vite development
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*"  # Allow all origins for development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(events_router, tags=["Car Events"])
app.include_router(gate_router, tags=["Gate Control"])
app.include_router(slots_router, tags=["Parking Slots"])

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with system information"""
    return {
        "message": "SmartPark IoT Backend API",
        "system": "Entry/Exit Detection with 3-Slot Management",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Entry/Exit detection via IR sensors",
            "Automatic slot assignment",
            "Real-time gate control",
            "WebSocket updates",
            "Reservation management",
            "3-slot logical management"
        ],
        "endpoints": {
            "slots": "/api/get_slots",
            "events": "/api/update_event",
            "gate_open": "/api/open_gate",
            "gate_close": "/api/close_gate",
            "reserve": "/api/reserve_slot",
            "release": "/api/release_slot",
            "websocket": "/ws/realtime"
        },
        "hardware": {
            "total_slots": 3,
            "detection_method": "Entry/Exit IR sensors",
            "gate_control": "Servo motor"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "system": "SmartPark Entry/Exit System",
        "slots_managed": 3,
        "active_websockets": len(manager.active_connections),
        "database": "connected",
        "timestamp": datetime.utcnow().isoformat()
    }

# WebSocket endpoint for real-time updates
@app.websocket("/ws/realtime")
async def websocket_realtime(websocket: WebSocket):
    """WebSocket endpoint for real-time parking updates"""
    await manager.connect(websocket)
    try:
        # Send initial connection confirmation
        await manager.send_personal_message(
            json.dumps({
                "type": "connection",
                "status": "connected",
                "message": "Connected to SmartPark real-time updates",
                "system": "Entry/Exit Detection",
                "slots": 3,
                "timestamp": datetime.utcnow().isoformat()
            }),
            websocket
        )
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                message_type = message.get("type", "unknown")
                
                if message_type == "ping":
                    # Respond to ping with pong
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "pong",
                            "timestamp": datetime.utcnow().isoformat()
                        }),
                        websocket
                    )
                elif message_type == "subscribe":
                    # Handle subscription requests
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "subscribed",
                            "channels": ["slot_updates", "car_events", "gate_events"],
                            "timestamp": datetime.utcnow().isoformat()
                        }),
                        websocket
                    )
                elif message_type == "get_status":
                    # Send current system status
                    from database_entry_exit import get_slot_stats, SessionLocal
                    db = SessionLocal()
                    try:
                        stats = get_slot_stats(db)
                        await manager.send_personal_message(
                            json.dumps({
                                "type": "status_update",
                                "data": stats,
                                "timestamp": datetime.utcnow().isoformat()
                            }),
                            websocket
                        )
                    finally:
                        db.close()
                else:
                    logger.info(f"📡 Received WebSocket message: {message}")
                    
            except json.JSONDecodeError:
                logger.warning(f"⚠️ Invalid JSON received from WebSocket: {data}")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        manager.disconnect(websocket)

# System status endpoint for monitoring
@app.get("/api/system/status")
async def system_status():
    """Detailed system status"""
    from database_entry_exit import get_slot_stats, SessionLocal
    db = SessionLocal()
    try:
        stats = get_slot_stats(db)
        
        return {
            "system": "SmartPark Entry/Exit Detection",
            "status": "operational",
            "components": {
                "api_server": "running",
                "database": "connected",
                "websocket": "active",
                "slots_managed": 3,
                "detection_method": "IR Entry/Exit sensors"
            },
            "statistics": {
                "active_websockets": len(manager.active_connections),
                "current_occupancy": stats,
                "uptime": "N/A"  # Could implement uptime tracking
            },
            "hardware": {
                "arduino_sensors": 2,
                "servo_gate": 1,
                "logical_slots": 3
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        db.close()

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested endpoint was not found",
            "system": "SmartPark Entry/Exit System",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"❌ Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "system": "SmartPark Entry/Exit System",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Helper function to broadcast updates (can be called from routes)
async def broadcast_update(update_type: str, data: Dict[str, Any]):
    """Helper function to broadcast updates to WebSocket clients"""
    try:
        message = json.dumps({
            "type": update_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        })
        await manager.broadcast(message)
        logger.info(f"📡 Broadcasted {update_type} update to {len(manager.active_connections)} clients")
    except Exception as e:
        logger.error(f"❌ Error broadcasting update: {e}")

# Make broadcast function available to routes
app.state.broadcast_update = broadcast_update

# Event handlers for real-time updates
@app.middleware("http")
async def add_real_time_updates(request, call_next):
    """Middleware to add real-time update capabilities"""
    response = await call_next(request)
    
    # Add WebSocket manager to request state for routes to use
    request.state.websocket_manager = manager
    
    return response

# Development server
if __name__ == "__main__":
    import uvicorn
    
    # Configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "true").lower() == "true"
    
    logger.info(f"🚀 Starting SmartPark Entry/Exit System on {host}:{port}")
    logger.info("🎯 Features: 3-slot management, Entry/Exit detection, Real-time updates")
    
    uvicorn.run(
        "main_entry_exit:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
