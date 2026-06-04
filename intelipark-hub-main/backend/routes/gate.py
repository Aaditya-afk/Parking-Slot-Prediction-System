"""
API routes for gate control
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["gate"])

# Serial bridge configuration
BRIDGE_URL = os.getenv("BRIDGE_URL", "http://localhost:5000")

@router.post("/open_gate")
async def open_gate():
    """Open the parking gate"""
    try:
        # Send command to serial bridge
        response = await send_gate_command("OPEN")
        
        return {
            "success": True,
            "message": "Gate opening command sent",
            "command": "SERVO_OPEN",
            "timestamp": datetime.utcnow().isoformat(),
            "bridge_response": response
        }
        
    except Exception as e:
        logger.error(f"Error opening gate: {e}")
        raise HTTPException(status_code=500, detail="Failed to open gate")

@router.post("/close_gate")
async def close_gate():
    """Close the parking gate"""
    try:
        # Send command to serial bridge
        response = await send_gate_command("CLOSE")
        
        return {
            "success": True,
            "message": "Gate closing command sent",
            "command": "SERVO_CLOSE",
            "timestamp": datetime.utcnow().isoformat(),
            "bridge_response": response
        }
        
    except Exception as e:
        logger.error(f"Error closing gate: {e}")
        raise HTTPException(status_code=500, detail="Failed to close gate")

@router.get("/gate_status")
async def get_gate_status():
    """Get current gate status from Arduino"""
    try:
        # This would query the Arduino through serial bridge
        # For now, return a mock status
        return {
            "success": True,
            "data": {
                "status": "unknown",  # open, closed, moving, unknown
                "last_action": "unknown",
                "last_updated": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting gate status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get gate status")

async def send_gate_command(command: str) -> Dict[str, Any]:
    """Send gate command to serial bridge"""
    try:
        # In a real implementation, this would communicate with the serial bridge
        # For now, we'll simulate the command being sent
        
        logger.info(f"Sending gate command: {command}")
        
        # Simulate successful command
        return {
            "status": "success",
            "command_sent": f"SERVO_{command}",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error sending gate command {command}: {e}")
        raise Exception(f"Failed to send gate command: {e}")

# Direct command endpoint for serial bridge
@router.post("/gate_command")
async def gate_command(command_data: Dict[str, Any]):
    """Direct gate command endpoint for serial bridge integration"""
    try:
        command = command_data.get("command", "").upper()
        
        if command not in ["OPEN", "CLOSE"]:
            raise HTTPException(status_code=400, detail="Invalid command. Use 'OPEN' or 'CLOSE'")
        
        # Process the command
        response = await send_gate_command(command)
        
        return {
            "success": True,
            "message": f"Gate {command.lower()} command processed",
            "response": response
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing gate command: {e}")
        raise HTTPException(status_code=500, detail="Failed to process gate command")
