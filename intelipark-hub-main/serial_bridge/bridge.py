"""
SmartPark Serial Bridge - Arduino to Backend Communication
Handles real-time data flow between Arduino and FastAPI backend.

Features:
- Continuous serial monitoring with auto-reconnection
- JSON data parsing and validation
- HTTP API communication with backend
- Command queue for gate control
- Error handling and logging
- Configurable settings

Author: SmartPark System
Version: 1.0 - Production Ready
"""

import serial
import json
import time
import threading
import requests
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import queue
import os
from dataclasses import dataclass
import serial.tools.list_ports

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('serial_bridge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class BridgeConfig:
    """Configuration for the serial bridge"""
    # Serial Configuration
    serial_port: str = "COM3"  # Change to your Arduino port
    baud_rate: int = 9600
    timeout: float = 1.0
    
    # Backend Configuration
    backend_url: str = "http://localhost:8000"
    update_endpoint: str = "/api/update_slots"
    gate_endpoint: str = "/api/gate_command"
    
    # Timing Configuration
    reconnect_delay: float = 5.0
    heartbeat_timeout: float = 60.0
    request_timeout: float = 5.0
    
    # Retry Configuration
    max_retries: int = 3
    retry_delay: float = 1.0

class SerialBridge:
    """Main serial bridge class for Arduino-Backend communication"""
    
    def __init__(self, config: BridgeConfig):
        self.config = config
        self.serial_connection: Optional[serial.Serial] = None
        self.is_running = False
        self.last_heartbeat = time.time()
        
        # Threading components
        self.command_queue = queue.Queue()
        self.read_thread: Optional[threading.Thread] = None
        self.write_thread: Optional[threading.Thread] = None
        
        # State tracking
        self.last_slot_data = {}
        self.connection_attempts = 0
        
    def start(self):
        """Start the serial bridge"""
        logger.info("Starting SmartPark Serial Bridge...")
        self.is_running = True
        
        # Start communication threads
        self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
        self.write_thread = threading.Thread(target=self._write_loop, daemon=True)
        
        self.read_thread.start()
        self.write_thread.start()
        
        logger.info("Serial Bridge started successfully")
        
    def stop(self):
        """Stop the serial bridge"""
        logger.info("Stopping Serial Bridge...")
        self.is_running = False
        
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            
        logger.info("Serial Bridge stopped")
        
    def _connect_serial(self) -> bool:
        """Establish serial connection to Arduino"""
        try:
            # Auto-detect Arduino if port not specified
            if self.config.serial_port == "AUTO":
                self.config.serial_port = self._find_arduino_port()
                
            if not self.config.serial_port:
                logger.error("No Arduino port found")
                return False
                
            # Close existing connection
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
                
            # Create new connection
            self.serial_connection = serial.Serial(
                port=self.config.serial_port,
                baudrate=self.config.baud_rate,
                timeout=self.config.timeout
            )
            
            # Wait for Arduino to initialize
            time.sleep(2)
            
            # Test connection with ping
            if self._test_connection():
                logger.info(f"Connected to Arduino on {self.config.serial_port}")
                self.connection_attempts = 0
                return True
            else:
                logger.warning("Arduino connection test failed")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to Arduino: {e}")
            return False
            
    def _find_arduino_port(self) -> Optional[str]:
        """Auto-detect Arduino port"""
        arduino_ports = []
        ports = serial.tools.list_ports.comports()
        
        for port in ports:
            # Look for Arduino-like devices
            if any(keyword in port.description.lower() for keyword in 
                   ['arduino', 'ch340', 'ch341', 'ftdi', 'usb serial']):
                arduino_ports.append(port.device)
                
        if arduino_ports:
            logger.info(f"Found potential Arduino ports: {arduino_ports}")
            return arduino_ports[0]  # Return first found
            
        return None
        
    def _test_connection(self) -> bool:
        """Test Arduino connection with ping command"""
        try:
            if not self.serial_connection or not self.serial_connection.is_open:
                return False
                
            # Send ping command
            self.serial_connection.write(b"PING\n")
            self.serial_connection.flush()
            
            # Wait for response
            start_time = time.time()
            while time.time() - start_time < 3:
                if self.serial_connection.in_waiting > 0:
                    response = self.serial_connection.readline().decode().strip()
                    if response:
                        try:
                            data = json.loads(response)
                            if data.get("type") == "pong":
                                return True
                        except json.JSONDecodeError:
                            continue
                time.sleep(0.1)
                
            return False
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
            
    def _read_loop(self):
        """Main reading loop for Arduino data"""
        while self.is_running:
            try:
                # Ensure connection
                if not self._ensure_connection():
                    time.sleep(self.config.reconnect_delay)
                    continue
                    
                # Read data from Arduino
                if self.serial_connection.in_waiting > 0:
                    line = self.serial_connection.readline().decode().strip()
                    if line:
                        self._process_arduino_data(line)
                        
                # Check for heartbeat timeout
                if time.time() - self.last_heartbeat > self.config.heartbeat_timeout:
                    logger.warning("Heartbeat timeout - Arduino may be disconnected")
                    self.serial_connection = None
                    
                time.sleep(0.1)  # Small delay to prevent CPU overload
                
            except Exception as e:
                logger.error(f"Error in read loop: {e}")
                self.serial_connection = None
                time.sleep(self.config.reconnect_delay)
                
    def _write_loop(self):
        """Main writing loop for commands to Arduino"""
        while self.is_running:
            try:
                # Get command from queue (blocking with timeout)
                command = self.command_queue.get(timeout=1.0)
                
                # Ensure connection
                if not self._ensure_connection():
                    logger.warning(f"Cannot send command '{command}' - no connection")
                    continue
                    
                # Send command to Arduino
                self._send_command(command)
                
            except queue.Empty:
                continue  # No commands to process
            except Exception as e:
                logger.error(f"Error in write loop: {e}")
                
    def _ensure_connection(self) -> bool:
        """Ensure serial connection is active"""
        if self.serial_connection and self.serial_connection.is_open:
            return True
            
        self.connection_attempts += 1
        logger.info(f"Attempting to connect to Arduino (attempt {self.connection_attempts})...")
        
        return self._connect_serial()
        
    def _process_arduino_data(self, line: str):
        """Process incoming data from Arduino"""
        try:
            # Parse JSON data
            data = json.loads(line)
            data_type = data.get("type", "unknown")
            
            if data_type == "slot_update":
                self._handle_slot_update(data)
            elif data_type == "servo_response":
                self._handle_servo_response(data)
            elif data_type == "heartbeat":
                self._handle_heartbeat(data)
            elif data_type == "system_status":
                self._handle_system_status(data)
            else:
                logger.debug(f"Received unknown data type: {data_type}")
                
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON from Arduino: {line} - Error: {e}")
        except Exception as e:
            logger.error(f"Error processing Arduino data: {e}")
            
    def _handle_slot_update(self, data: Dict[str, Any]):
        """Handle slot status updates from Arduino"""
        try:
            # Extract slot data
            slot_data = {
                "slot1": data.get("slot1", 0),
                "slot2": data.get("slot2", 0),
                "slot3": data.get("slot3", 0),
                "timestamp": data.get("timestamp", int(time.time() * 1000))
            }
            
            # Check if data has changed
            if slot_data != self.last_slot_data:
                logger.info(f"Slot update: {slot_data}")
                
                # Send to backend
                self._send_to_backend(slot_data)
                self.last_slot_data = slot_data.copy()
            
        except Exception as e:
            logger.error(f"Error handling slot update: {e}")
            
    def _handle_servo_response(self, data: Dict[str, Any]):
        """Handle servo command responses"""
        status = data.get("status", "UNKNOWN")
        angle = data.get("angle", 0)
        detail = data.get("detail", "")
        
        logger.info(f"Servo response: {status} (angle: {angle}°) {detail}")
        
        # Could send this back to backend for status updates
        
    def _handle_heartbeat(self, data: Dict[str, Any]):
        """Handle heartbeat from Arduino"""
        self.last_heartbeat = time.time()
        uptime = data.get("uptime", 0)
        logger.debug(f"Heartbeat received - Arduino uptime: {uptime}ms")
        
    def _handle_system_status(self, data: Dict[str, Any]):
        """Handle system status from Arduino"""
        logger.info(f"Arduino system status: {data}")
        
    def _send_to_backend(self, slot_data: Dict[str, Any]):
        """Send slot data to backend API"""
        url = f"{self.config.backend_url}{self.config.update_endpoint}"
        
        # Prepare payload
        payload = {
            "slots": slot_data,
            "source": "arduino",
            "bridge_timestamp": datetime.now().isoformat()
        }
        
        # Send with retries
        for attempt in range(self.config.max_retries):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    timeout=self.config.request_timeout,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    logger.debug("Successfully sent slot data to backend")
                    return
                else:
                    logger.warning(f"Backend returned status {response.status_code}: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"Failed to send to backend (attempt {attempt + 1}): {e}")
                
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay)
                    
        logger.error("Failed to send slot data to backend after all retries")
        
    def _send_command(self, command: str):
        """Send command to Arduino"""
        try:
            if not self.serial_connection or not self.serial_connection.is_open:
                logger.error("Cannot send command - no serial connection")
                return
                
            # Send command
            command_bytes = f"{command}\n".encode()
            self.serial_connection.write(command_bytes)
            self.serial_connection.flush()
            
            logger.info(f"Sent command to Arduino: {command}")
            
        except Exception as e:
            logger.error(f"Error sending command '{command}': {e}")
            
    def send_gate_command(self, command: str):
        """Public method to send gate commands"""
        if command.upper() in ["SERVO_OPEN", "SERVO_CLOSE"]:
            self.command_queue.put(command.upper())
            logger.info(f"Queued gate command: {command}")
        else:
            logger.warning(f"Invalid gate command: {command}")

class BridgeAPI:
    """Simple HTTP API for external control of the bridge"""
    
    def __init__(self, bridge: SerialBridge):
        self.bridge = bridge
        
    def handle_gate_command(self, command: str) -> Dict[str, Any]:
        """Handle gate command from backend"""
        try:
            if command.upper() in ["OPEN", "CLOSE"]:
                servo_command = f"SERVO_{command.upper()}"
                self.bridge.send_gate_command(servo_command)
                
                return {
                    "status": "success",
                    "message": f"Gate command '{command}' queued",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "message": f"Invalid command: {command}",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error handling gate command: {e}")
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }

def main():
    """Main function to run the serial bridge"""
    # Load configuration from environment or use defaults
    config = BridgeConfig(
        serial_port=os.getenv("ARDUINO_PORT", "COM3"),
        backend_url=os.getenv("BACKEND_URL", "http://localhost:8000")
    )
    
    # Create and start bridge
    bridge = SerialBridge(config)
    
    try:
        bridge.start()
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        bridge.stop()

if __name__ == "__main__":
    main()
