"""
Serial Bridge for Arduino Communication
Handles USB serial communication with Arduino UNO
"""

import serial
import time
import logging
import threading
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class SerialBridge:
    """Manages serial communication with Arduino"""
    
    def __init__(self):
        self.port = os.getenv("ARDUINO_PORT", "COM3")  # Default Windows port
        self.baudrate = int(os.getenv("ARDUINO_BAUDRATE", "9600"))
        self.timeout = float(os.getenv("ARDUINO_TIMEOUT", "1.0"))
        self.serial_connection: Optional[serial.Serial] = None
        self.connected = False
        self.simulator_mode = os.getenv("SIMULATOR_MODE", "false").lower() == "true"
        self.lock = threading.Lock()
        
        # Simulator state for testing
        self.simulator_slots = {
            "SLOT_1": "FREE",
            "SLOT_2": "FREE", 
            "SLOT_3": "FREE",
            "SLOT_4": "FREE",
            "SLOT_5": "FREE",
            "SLOT_6": "FREE"
        }
        self.simulator_counter = 0
        
        self._connect()
    
    def _connect(self):
        """Establish serial connection to Arduino"""
        if self.simulator_mode:
            logger.info("Running in simulator mode - no Arduino connection needed")
            self.connected = True
            return
            
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            time.sleep(2)  # Wait for Arduino to initialize
            self.connected = True
            logger.info(f"Connected to Arduino on {self.port}")
            
        except serial.SerialException as e:
            logger.error(f"Failed to connect to Arduino on {self.port}: {e}")
            logger.info("Falling back to simulator mode")
            self.simulator_mode = True
            self.connected = True
        except Exception as e:
            logger.error(f"Unexpected error connecting to Arduino: {e}")
            self.connected = False
    
    def is_connected(self) -> bool:
        """Check if Arduino is connected"""
        if self.simulator_mode:
            return True
            
        return self.connected and self.serial_connection and self.serial_connection.is_open
    
    def read_arduino(self) -> Optional[str]:
        """Read data from Arduino"""
        if self.simulator_mode:
            return self._simulate_arduino_data()
            
        if not self.is_connected():
            self._reconnect()
            return None
            
        try:
            with self.lock:
                if self.serial_connection.in_waiting > 0:
                    line = self.serial_connection.readline().decode('utf-8').strip()
                    if line:
                        logger.debug(f"Arduino data: {line}")
                        return line
        except Exception as e:
            logger.error(f"Error reading from Arduino: {e}")
            self.connected = False
            
        return None
    
    def send_command(self, command: str) -> bool:
        """Send command to Arduino"""
        if self.simulator_mode:
            logger.info(f"Simulator: Would send command '{command}' to Arduino")
            return True
            
        if not self.is_connected():
            self._reconnect()
            return False
            
        try:
            with self.lock:
                command_bytes = (command + "\n").encode('utf-8')
                self.serial_connection.write(command_bytes)
                self.serial_connection.flush()
                logger.info(f"Sent command to Arduino: {command}")
                return True
                
        except Exception as e:
            logger.error(f"Error sending command to Arduino: {e}")
            self.connected = False
            return False
    
    def _reconnect(self):
        """Attempt to reconnect to Arduino"""
        if self.simulator_mode:
            return
            
        logger.info("Attempting to reconnect to Arduino...")
        self.close()
        time.sleep(1)
        self._connect()
    
    def _simulate_arduino_data(self) -> Optional[str]:
        """Simulate Arduino sensor data for testing"""
        import random
        
        # Generate random sensor events every few calls
        self.simulator_counter += 1
        
        if self.simulator_counter % 50 == 0:  # Every 50 calls (~5 seconds)
            slot = random.choice(list(self.simulator_slots.keys()))
            current_status = self.simulator_slots[slot]
            
            # 30% chance to change status
            if random.random() < 0.3:
                new_status = "OCCUPIED" if current_status == "FREE" else "FREE"
                self.simulator_slots[slot] = new_status
                return f"{slot}: {new_status}"
        
        return None
    
    def close(self):
        """Close serial connection"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            logger.info("Arduino connection closed")
        self.connected = False
    
    def get_status(self) -> dict:
        """Get connection status information"""
        return {
            "connected": self.is_connected(),
            "port": self.port,
            "baudrate": self.baudrate,
            "simulator_mode": self.simulator_mode
        }

# Test function
def test_serial_bridge():
    """Test the serial bridge functionality"""
    bridge = SerialBridge()
    
    print(f"Connection status: {bridge.get_status()}")
    
    # Test sending commands
    bridge.send_command("SERVO_OPEN")
    time.sleep(1)
    bridge.send_command("SERVO_CLOSE")
    
    # Test reading data
    for i in range(10):
        data = bridge.read_arduino()
        if data:
            print(f"Received: {data}")
        time.sleep(0.5)
    
    bridge.close()

if __name__ == "__main__":
    test_serial_bridge()
