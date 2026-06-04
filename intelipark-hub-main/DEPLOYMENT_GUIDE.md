# 🚀 SmartPark Deployment Guide - Complete Setup

Step-by-step guide to deploy your complete SmartPark IoT system from development to production.

## 🎯 **System Architecture Overview**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Arduino UNO   │───▶│  Serial Bridge  │───▶│  FastAPI Backend │───▶│  React Frontend │
│                 │    │   (Python)      │    │   (Python)      │    │  (JavaScript)   │
│ • 3 IR Sensors  │    │ • USB Serial    │    │ • REST APIs     │    │ • Real-time UI  │
│ • 1 Servo Motor │    │ • Auto-reconnect│    │ • WebSocket     │    │ • Reservations  │
│ • JSON Protocol │    │ • Error Handling│    │ • ML Predictions│    │ • Admin Panel   │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 📋 **Pre-Deployment Checklist**

### **Hardware Requirements**
- [ ] Arduino UNO with USB cable
- [ ] 3x IR obstacle sensors (FC-51 or similar)
- [ ] 1x Servo motor (SG90 or MG996R)
- [ ] Breadboard and jumper wires
- [ ] 5V external power supply (recommended)

### **Software Requirements**
- [ ] Python 3.8+ installed
- [ ] Node.js 16+ installed
- [ ] Arduino IDE installed
- [ ] Git installed

### **System Requirements**
- [ ] Windows 10/11 or Linux/macOS
- [ ] 4GB RAM minimum
- [ ] USB port for Arduino
- [ ] Internet connection

---

## 🔧 **Step 1: Arduino Hardware Setup**

### **Wiring Diagram**
```
Arduino UNO Connections:
├── IR Sensor 1 (SLOT_1) → Pin 2
├── IR Sensor 2 (SLOT_2) → Pin 3  
├── IR Sensor 3 (SLOT_3) → Pin 4
├── Servo Motor Signal → Pin 9
├── All VCC → 5V (or external supply)
└── All GND → GND (common ground)
```

### **Upload Arduino Code**
1. **Open Arduino IDE**
2. **Load sketch**: `arduino/smartpark_3slots.ino`
3. **Select board**: Arduino UNO
4. **Select port**: Check Device Manager (Windows) or `ls /dev/tty*` (Linux)
5. **Upload code**
6. **Test**: Open Serial Monitor (9600 baud) - should see JSON messages

### **Verify Hardware**
```
Expected Serial Output:
{"slot1":0,"slot2":0,"slot3":0,"timestamp":12345,"type":"slot_update"}
{"type":"heartbeat","uptime":30000,"servo_angle":0,"servo_state":"IDLE"}
```

---

## 🐍 **Step 2: Serial Bridge Setup**

### **Install Dependencies**
```bash
cd serial_bridge
pip install -r requirements.txt
```

### **Configure COM Port**
Edit `bridge.py` or set environment variable:
```bash
# Windows
set ARDUINO_PORT=COM3

# Linux/Mac
export ARDUINO_PORT=/dev/ttyUSB0
```

### **Test Serial Bridge**
```bash
python bridge.py
```

Expected output:
```
INFO - Starting SmartPark Serial Bridge...
INFO - Connected to Arduino on COM3
INFO - Received slot update from arduino: {'slot1': 0, 'slot2': 0, 'slot3': 0}
```

---

## ⚡ **Step 3: Backend Setup**

### **Install Backend Dependencies**
```bash
cd backend
pip install -r requirements.txt
```

### **Configure Environment**
Create `.env` file:
```bash
# Database
DATABASE_URL=sqlite:///./smartpark.db

# Arduino
ARDUINO_PORT=COM3
SIMULATOR_MODE=false

# API
HOST=0.0.0.0
PORT=8000
DEBUG=true

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### **Initialize Database**
```bash
python -c "from database import init_db; init_db()"
```

### **Start Backend Server**
```bash
python main.py
```

### **Verify Backend**
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health
- **Slots Endpoint**: http://localhost:8000/api/get_slots

---

## 🌐 **Step 4: Frontend Integration**

### **Install Frontend Dependencies**
```bash
npm install
```

### **Configure Frontend Environment**
Create `.env` file in frontend root:
```bash
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws/realtime
REACT_APP_ENABLE_REALTIME=true
```

### **Add API Integration**
Copy the API service and hooks from `FRONTEND_INTEGRATION.md`:
- `src/services/smartparkApi.js`
- `src/hooks/useRealtimeUpdates.js`

### **Update Your Components**
Integrate the provided code examples into your existing:
- Dashboard component
- Slots page
- Reservations page

### **Start Frontend**
```bash
npm run dev
```

---

## 🧪 **Step 5: System Testing**

### **Test Sequence**
1. **Arduino Test**
   ```bash
   # Check Arduino Serial Monitor
   # Should see JSON messages every second
   ```

2. **Serial Bridge Test**
   ```bash
   python serial_bridge/bridge.py
   # Should connect to Arduino and backend
   ```

3. **Backend Test**
   ```bash
   curl http://localhost:8000/api/get_slots
   # Should return slot data
   ```

4. **Frontend Test**
   ```bash
   # Open http://localhost:5173
   # Should show dashboard with real-time data
   ```

5. **End-to-End Test**
   - Block IR sensor with hand
   - Check Arduino Serial Monitor for state change
   - Verify backend receives update
   - Confirm frontend updates in real-time

### **WebSocket Test**
```javascript
// Browser Console Test
const ws = new WebSocket('ws://localhost:8000/ws/realtime');
ws.onmessage = (event) => console.log('Received:', JSON.parse(event.data));
ws.onopen = () => ws.send(JSON.stringify({type: 'ping'}));
```

---

## 🔄 **Step 6: ML Model Training**

### **Generate Training Data**
Let the system run for a few hours to collect sensor data, then:

```bash
# Train ML model with collected data
curl -X POST http://localhost:8000/api/ml/train
```

### **Test Predictions**
```bash
# Get predictions for all slots
curl http://localhost:8000/api/ml/predict/all?minutes_ahead=30
```

---

## 🚀 **Production Deployment**

### **Option 1: Local Network Deployment**

#### **Backend as Windows Service**
```bash
# Install service wrapper
pip install pywin32

# Create service script
python -c "
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import os

class SmartParkService(win32serviceutil.ServiceFramework):
    _svc_name_ = 'SmartParkBackend'
    _svc_display_name_ = 'SmartPark Backend Service'
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
    
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
    
    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        self.main()
    
    def main(self):
        os.chdir(r'C:\path\to\your\backend')
        os.system('python main.py')

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(SmartParkService)
"
```

#### **Frontend Static Hosting**
```bash
# Build production frontend
npm run build

# Serve with nginx, Apache, or IIS
# Point web server to dist/ folder
```

### **Option 2: Cloud Deployment**

#### **Backend (Railway/Render)**
```yaml
# railway.toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python main.py"

[env]
DATABASE_URL = "postgresql://..."
ARDUINO_PORT = "SIMULATOR"
SIMULATOR_MODE = "true"
```

#### **Frontend (Vercel/Netlify)**
```bash
# Build command
npm run build

# Environment variables
REACT_APP_API_URL=https://your-backend.railway.app
REACT_APP_WS_URL=wss://your-backend.railway.app/ws/realtime
```

### **Option 3: Docker Deployment**

#### **Docker Compose Setup**
```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/smartpark
      - ARDUINO_PORT=/dev/ttyUSB0
    devices:
      - /dev/ttyUSB0:/dev/ttyUSB0
    volumes:
      - ./backend:/app
    depends_on:
      - postgres

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: smartpark
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  frontend:
    build: ./
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    depends_on:
      - backend

volumes:
  postgres_data:
```

---

## 📊 **Monitoring & Maintenance**

### **Health Monitoring**
```bash
# Backend health
curl http://localhost:8000/api/health

# System status
curl http://localhost:8000/api/system/status

# Check logs
tail -f backend/smartpark_backend.log
tail -f serial_bridge/serial_bridge.log
```

### **Database Maintenance**
```bash
# Backup SQLite database
cp backend/smartpark.db backup/smartpark_$(date +%Y%m%d).db

# Clean old logs (keep last 30 days)
python -c "
from datetime import datetime, timedelta
from backend.database import SessionLocal
from backend.models.slots import SlotLog

db = SessionLocal()
cutoff = datetime.utcnow() - timedelta(days=30)
old_logs = db.query(SlotLog).filter(SlotLog.change_timestamp < cutoff).delete()
db.commit()
print(f'Cleaned {old_logs} old log entries')
"
```

### **Performance Optimization**
```bash
# Retrain ML model weekly
curl -X POST http://localhost:8000/api/ml/train

# Monitor WebSocket connections
curl http://localhost:8000/api/health | grep websockets

# Check Arduino connection
python -c "
from serial_bridge.bridge import SerialBridge, BridgeConfig
bridge = SerialBridge(BridgeConfig())
print('Arduino connected:', bridge._connect_serial())
"
```

---

## 🔧 **Troubleshooting**

### **Common Issues**

#### **Arduino Not Detected**
```bash
# Windows: Check Device Manager
# Linux: Check permissions
sudo usermod -a -G dialout $USER
sudo chmod 666 /dev/ttyUSB0

# Test connection
python -c "
import serial
ser = serial.Serial('COM3', 9600, timeout=1)
print('Connected:', ser.is_open)
ser.close()
"
```

#### **Backend Connection Issues**
```bash
# Check if port is in use
netstat -an | findstr :8000  # Windows
lsof -i :8000                # Linux/Mac

# Test database connection
python -c "
from backend.database import engine
try:
    engine.connect()
    print('Database connected')
except Exception as e:
    print('Database error:', e)
"
```

#### **WebSocket Connection Failed**
```bash
# Check CORS settings
# Verify frontend URL in backend ALLOWED_ORIGINS

# Test WebSocket directly
pip install websocket-client
python -c "
import websocket
ws = websocket.WebSocket()
ws.connect('ws://localhost:8000/ws/realtime')
print('WebSocket connected')
ws.close()
"
```

#### **Frontend API Errors**
```bash
# Check network requests in browser dev tools
# Verify API URL in .env file
# Check backend logs for errors
```

---

## 🎯 **Success Metrics**

After successful deployment, verify:

- [ ] **Arduino**: Sensors detect changes, servo responds to commands
- [ ] **Serial Bridge**: Connects automatically, handles disconnections
- [ ] **Backend**: All APIs respond, WebSocket broadcasts work
- [ ] **Frontend**: Real-time updates, reservations work, ML predictions display
- [ ] **End-to-End**: Car detection → Backend update → Frontend refresh < 2 seconds

---

## 🎉 **Deployment Complete!**

Your SmartPark IoT system is now fully operational with:

✅ **Real-time Hardware Integration** - Arduino sensors → Backend → Frontend  
✅ **Smart Reservations** - Web booking → Gate control → User management  
✅ **ML Predictions** - AI-powered availability forecasting  
✅ **Production Ready** - Error handling, monitoring, and scalability  
✅ **Professional Grade** - Complete documentation and maintenance guides  

**Your IoT parking management system is ready for real-world deployment!** 🚗⚡🎯
