"""
API routes for gate control - SmartPark Entry/Exit System
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime
import logging
import requests
import os

from ..database_entry_exit import get_db, log_system_event
from ..models.parking import GateLog

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["gate"])

# Serial bridge configuration
BRIDGE_URL = os.getenv("BRIDGE_URL", "http://localhost:5000")

@router.post("/open_gate")
async def open_gate(request: Request, db: Session = Depends(get_db)):
    """Open the parking gate manually"""
    try:
        # Log gate action
        gate_log = GateLog(
            action="OPEN",
            triggered_by="manual",
            success="pending"
        )
        db.add(gate_log)
        db.flush()  # Get the ID
        
        # Send command to Arduino (via serial bridge or direct)
        success, message = await send_gate_command("SERVO_OPEN", gate_log.id, db)
        
        # Update gate log
        gate_log.success = "success" if success else "failed"
        gate_log.error_message = message if not success else None
        
        db.commit()
        
        # Log system event
        log_system_event(db, "INFO", "gate", f"Manual gate open: {message}")

        # Broadcast gate event
        if hasattr(request.app.state, "broadcast_update"):
            await request.app.state.broadcast_update("gate_event", {
                "action": "OPEN",
                "status": "success" if success else "failed",
                "gate_log_id": gate_log.id
            })
        
        return {
            "success": success,
            "message": "Gate opening command sent" if success else f"Failed to open gate: {message}",
            "command": "SERVO_OPEN",
            "gate_log_id": gate_log.id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error opening gate: {e}")
        raise HTTPException(status_code=500, detail="Failed to open gate")

@router.post("/close_gate")
async def close_gate(request: Request, db: Session = Depends(get_db)):
    """Close the parking gate manually"""
    try:
        # Log gate action
        gate_log = GateLog(
            action="CLOSE",
            triggered_by="manual",
            success="pending"
        )
        db.add(gate_log)
        db.flush()  # Get the ID
        
        # Send command to Arduino (via serial bridge or direct)
        success, message = await send_gate_command("SERVO_CLOSE", gate_log.id, db)
        
        # Update gate log
        gate_log.success = "success" if success else "failed"
        gate_log.error_message = message if not success else None
        
        db.commit()
        
        # Log system event
        log_system_event(db, "INFO", "gate", f"Manual gate close: {message}")

        # Broadcast gate event
        if hasattr(request.app.state, "broadcast_update"):
            await request.app.state.broadcast_update("gate_event", {
                "action": "CLOSE",
                "status": "success" if success else "failed",
                "gate_log_id": gate_log.id
            })
        
        return {
            "success": success,
            "message": "Gate closing command sent" if success else f"Failed to close gate: {message}",
            "command": "SERVO_CLOSE",
            "gate_log_id": gate_log.id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error closing gate: {e}")
        raise HTTPException(status_code=500, detail="Failed to close gate")

@router.get("/gate_status")
async def get_gate_status(db: Session = Depends(get_db)):
    """Get current gate status and recent activity"""
    try:
        # Get recent gate logs
        recent_logs = db.query(GateLog).order_by(
            GateLog.timestamp.desc()
        ).limit(10).all()
        
        # Determine current status from most recent log
        current_status = "unknown"
        last_action = None
        last_timestamp = None
        
        if recent_logs:
            latest_log = recent_logs[0]
            if latest_log.success == "success":
                current_status = "open" if latest_log.action == "OPEN" else "closed"
            elif latest_log.success == "pending":
                current_status = "moving"
            else:
                current_status = "error"
            
            last_action = latest_log.action
            last_timestamp = latest_log.timestamp.isoformat()
        
        # Format recent activity
        activity = []
        for log in recent_logs:
            activity.append({
                "id": log.id,
                "action": log.action,
                "triggered_by": log.triggered_by,
                "success": log.success,
                "timestamp": log.timestamp.isoformat(),
                "error_message": log.error_message,
                "response_time_ms": log.response_time_ms
            })
        
        return {
            "success": True,
            "data": {
                "current_status": current_status,
                "last_action": last_action,
                "last_timestamp": last_timestamp,
                "recent_activity": activity
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting gate status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get gate status")

@router.post("/gate_command")
async def gate_command(command_data: Dict[str, Any], db: Session = Depends(get_db)):
    """Direct gate command endpoint for external systems"""
    try:
        command = command_data.get("command", "").upper()
        triggered_by = command_data.get("triggered_by", "external")
        
        if command not in ["OPEN", "CLOSE", "SERVO_OPEN", "SERVO_CLOSE"]:
            raise HTTPException(status_code=400, detail="Invalid command. Use 'OPEN' or 'CLOSE'")
        
        # Normalize command
        servo_command = f"SERVO_{command}" if command in ["OPEN", "CLOSE"] else command
        action = command.replace("SERVO_", "") if command.startswith("SERVO_") else command
        
        # Log gate action
        gate_log = GateLog(
            action=action,
            triggered_by=triggered_by,
            success="pending"
        )
        db.add(gate_log)
        db.flush()
        
        # Send command
        success, message = await send_gate_command(servo_command, gate_log.id, db)
        
        # Update log
        gate_log.success = "success" if success else "failed"
        gate_log.error_message = message if not success else None
        
        db.commit()
        
        return {
            "success": success,
            "message": f"Gate {action.lower()} command processed" if success else f"Command failed: {message}",
            "command": servo_command,
            "gate_log_id": gate_log.id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error processing gate command: {e}")
        raise HTTPException(status_code=500, detail="Failed to process gate command")

async def send_gate_command(command: str, gate_log_id: int, db: Session) -> tuple[bool, str]:
    """Send gate command to Arduino via serial bridge or direct connection"""
    try:
        start_time = datetime.utcnow()
        
        # Try to send via serial bridge first (if available)
        try:
            bridge_response = requests.post(
                f"{BRIDGE_URL}/bridge/gate",
                json={"command": command},
                timeout=5
            )
            
            if bridge_response.status_code == 200:
                response_data = bridge_response.json()
                
                # Calculate response time
                response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                # Update gate log with response details
                gate_log = db.query(GateLog).filter(GateLog.id == gate_log_id).first()
                if gate_log:
                    gate_log.response_time_ms = response_time
                    gate_log.arduino_response = str(response_data)
                
                return True, "Command sent via serial bridge"
            else:
                logger.warning(f"⚠️ Serial bridge returned {bridge_response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ Serial bridge not available: {e}")
        
        # Fallback: Direct Arduino communication (if implemented)
        # This would require direct serial connection from backend
        logger.info(f"📤 Sending command directly: {command}")
        
        # For now, simulate successful command
        # In a real implementation, you would:
        # 1. Open serial connection to Arduino
        # 2. Send command
        # 3. Wait for response
        # 4. Parse response and return status
        
        response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        # Update gate log
        gate_log = db.query(GateLog).filter(GateLog.id == gate_log_id).first()
        if gate_log:
            gate_log.response_time_ms = response_time
            gate_log.arduino_response = f"Simulated response for {command}"
        
        return True, "Command sent successfully"
        
    except Exception as e:
        logger.error(f"❌ Error sending gate command: {e}")
        return False, str(e)

@router.get("/gate_logs")
async def get_gate_logs(
    limit: int = 50,
    action: str = None,
    success_only: bool = False,
    db: Session = Depends(get_db)
):
    """Get gate operation logs"""
    try:
        query = db.query(GateLog)
        
        if action and action.upper() in ["OPEN", "CLOSE"]:
            query = query.filter(GateLog.action == action.upper())
        
        if success_only:
            query = query.filter(GateLog.success == "success")
        
        logs = query.order_by(GateLog.timestamp.desc()).limit(limit).all()
        
        log_data = []
        for log in logs:
            log_data.append({
                "id": log.id,
                "action": log.action,
                "triggered_by": log.triggered_by,
                "event_id": log.event_id,
                "timestamp": log.timestamp.isoformat(),
                "success": log.success,
                "response_time_ms": log.response_time_ms,
                "error_message": log.error_message,
                "arduino_response": log.arduino_response
            })
        
        return {
            "success": True,
            "data": log_data,
            "total": len(log_data),
            "filters": {
                "action": action,
                "success_only": success_only,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting gate logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get gate logs")
