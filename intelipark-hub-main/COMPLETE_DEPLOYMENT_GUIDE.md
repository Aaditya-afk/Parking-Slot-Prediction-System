# 🚀 SmartPark Complete Deployment Guide - Entry/Exit 3-Slot System

Step-by-step guide to deploy your complete SmartPark IoT system with entry/exit detection and 3-slot management.

## 🎯 **System Architecture Overview**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Arduino UNO   │───▶│  Serial Bridge  │───▶│  FastAPI Backend │───▶│  React Frontend │
│                 │    │   (Python)      │    │   (Python)      │    │  (JavaScript)   │
│ • IR_ENTRY (Pin2)│    │ • Event parsing │    │ • Slot assignment│    │ • 3-slot display│
│ • IR_EXIT (Pin3) │    │ • Gate commands │    │ • WebSocket     │    │ • Real-time UI  │
│ • Servo (Pin9)   │    │ • Auto-reconnect│    │ • AI predictions│    │ • Reservations  │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 📋 **Pre-Deployment Checklist**

### **Hardware Requirements**
- [ ] Arduino UNO with USB cable
- [ ] 2x IR obstacle sensors (FC-51 or similar) for entry/exit detection
- [ ] 1x Servo motor (SG90 or MG996R) for gate control
- [ ] Breadboard and jumper wires
- [ ] 5V external power supply (recommended for servo)

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
├── IR Sensor 1 (ENTRY) → Pin 2
├── IR Sensor 2 (EXIT) → Pin 3  
├── Servo Motor Signal → Pin 9
├── All VCC → 5V (or external supply)
└── All GND → GND (common ground)
```

### **Physical Setup**
```
Parking Lot Layout:

    [ENTRY IR]     [PARKING AREA]     [EXIT IR]
         │              │                │
    ┌────▼────┐    ┌────▼────┐     ┌────▼────┐
    │ SENSOR  │    │ SLOT_1  │     │ SENSOR  │
    │ PIN 2   │    │ SLOT_2  │     │ PIN 3   │
    │         │    │ SLOT_3  │     │         │
    └─────────┘    └─────────┘     └─────────┘
         │              │                │
    [SERVO GATE]   [3 LOGICAL]     [SERVO GATE]
                    [SLOTS]
```

### **Upload Arduino Code**
1. **Open Arduino IDE**
2. **Load sketch**: `arduino/smartpark_entry_exit.ino`
3. **Select board**: Arduino UNO
4. **Select port**: Check Device Manager (Windows) or `ls /dev/tty*` (Linux)
5. **Upload code**
6. **Test**: Open Serial Monitor (9600 baud) - should see JSON messages

### **Verify Hardware**
```
Expected Serial Output:
{"status":"SYSTEM_READY","sensors":2,"servo":"ATTACHED","mode":"ENTRY_EXIT"}
{"event":"car_entered","timestamp":12345,"entry_sensor":true,"exit_sensor":false}
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
Edit `event_bridge.py` or set environment variable:
```bash
# Windows
set ARDUINO_PORT=COM3

# Linux/Mac
export ARDUINO_PORT=/dev/ttyUSB0
```

### **Test Serial Bridge**
```bash
python event_bridge.py
```

Expected output:
```
🚀 Starting SmartPark Serial Bridge (Entry/Exit System)...
✅ Connected to Arduino on COM3
🚗 Car Event: car_entered
✅ Event sent to backend: car_entered
```

---

## ⚡ **Step 3: Backend Setup**

### **Install Backend Dependencies**
```bash
cd backend
pip install -r requirements.txt
pip install scikit-learn joblib  # For AI predictions
```

### **Configure Environment**
Create `.env` file:
```bash
# Database
DATABASE_URL=sqlite:///./smartpark_entry_exit.db

# System Configuration
TOTAL_PARKING_SLOTS=3
DEBUG=true

# API
HOST=0.0.0.0
PORT=8000

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

### **Initialize Database**
```bash
python -c "from database_entry_exit import init_db; init_db()"
```

### **Start Backend Server**
```bash
python main_entry_exit.py
```

### **Verify Backend**
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health
- **Slots Endpoint**: http://localhost:8000/api/get_slots

Expected response from `/api/get_slots`:
```json
{
  "success": true,
  "data": {
    "slots": [
      {"id": 1, "slot_number": "SLOT_1", "status": "free"},
      {"id": 2, "slot_number": "SLOT_2", "status": "free"},
      {"id": 3, "slot_number": "SLOT_3", "status": "free"}
    ],
    "summary": {
      "total_slots": 3,
      "free_slots": 3,
      "occupied_slots": 0,
      "reserved_slots": 0,
      "occupancy_rate": 0.0
    }
  }
}
```

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
REACT_APP_TOTAL_SLOTS=3
```

### **Add API Integration**
Copy the API service from `REACT_INTEGRATION_3SLOTS.md`:
1. Create `src/services/smartparkApi.js`
2. Create `src/hooks/useRealtimeUpdates.js`
3. Update your Dashboard component

### **Update Your Existing Components**

#### **Dashboard.tsx Changes**
```typescript
// Replace mock data imports
// OLD:
// import { mockSlots, mockLots } from '@/lib/mockData';

// NEW:
import { smartparkApi } from '@/services/smartparkApi';
import { useRealtimeUpdates } from '@/hooks/useRealtimeUpdates';

// Update data fetching
const [parkingData, setParkingData] = useState(null);

useEffect(() => {
  const fetchData = async () => {
    try {
      const data = await smartparkApi.getParkingOverview();
      setParkingData(data);
    } catch (error) {
      console.error('Error fetching parking data:', error);
    }
  };
  
  fetchData();
}, []);

// Use real data in stats
const stats = [
  {
    title: 'Total Slots',
    value: parkingData?.total_slots || 3,
    icon: '🚗'
  },
  {
    title: 'Available Now',
    value: parkingData?.free_slots || 0,
    icon: '🟢'
  },
  // ... etc
];
```

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
   # Should see JSON messages when sensors triggered
   ```

2. **Serial Bridge Test**
   ```bash
   python serial_bridge/event_bridge.py
   # Should connect to Arduino and backend
   # Trigger IR sensor → should see event forwarded
   ```

3. **Backend Test**
   ```bash
   curl http://localhost:8000/api/get_slots
   # Should return 3 slots with current status
   ```

4. **Frontend Test**
   ```bash
   # Open http://localhost:5173
   # Should show dashboard with 3 slots
   # Should display real-time connection status
   ```

5. **End-to-End Test**
   - Block IR_ENTRY sensor with hand
   - Check Arduino Serial Monitor for car_entered event
   - Verify backend receives event and assigns slot
   - Confirm frontend updates showing occupied slot
   - Block IR_EXIT sensor
   - Verify slot is freed and frontend updates

### **WebSocket Test**
```javascript
// Browser Console Test
const ws = new WebSocket('ws://localhost:8000/ws/realtime');
ws.onmessage = (event) => console.log('Received:', JSON.parse(event.data));
ws.onopen = () => ws.send(JSON.stringify({type: 'ping'}));
```

---

## 🤖 **Step 6: AI Model Training**

### **Generate Training Data**
Let the system run for a few hours with car entry/exit events, then:

```bash
# Train AI model with collected data
curl -X POST http://localhost:8000/api/ai/train_model
```

### **Test AI Predictions**
```bash
# Get AI insights
curl http://localhost:8000/api/ai/insights

# Get occupancy predictions
curl http://localhost:8000/api/ai/predict_occupancy?hours_ahead=2
```

---

## 🚀 **Production Deployment Options**

### **Option 1: Local Network Deployment**

#### **Backend as Windows Service**
```bash
# Create service script
python -c "
import win32serviceutil
import win32service
import win32event
import servicemanager
import os

class SmartParkService(win32serviceutil.ServiceFramework):
    _svc_name_ = 'SmartParkEntryExit'
    _svc_display_name_ = 'SmartPark Entry/Exit System'
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
    
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
        os.system('python main_entry_exit.py')

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

### **Option 2: Docker Deployment**

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
      - DATABASE_URL=sqlite:///./smartpark_entry_exit.db
      - TOTAL_PARKING_SLOTS=3
      - ARDUINO_PORT=/dev/ttyUSB0
    devices:
      - /dev/ttyUSB0:/dev/ttyUSB0  # Arduino connection
    volumes:
      - ./backend:/app
      - ./data:/app/data

  frontend:
    build: ./
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
      - REACT_APP_TOTAL_SLOTS=3
    depends_on:
      - backend

  serial-bridge:
    build: ./serial_bridge
    environment:
      - ARDUINO_PORT=/dev/ttyUSB0
      - BACKEND_URL=http://backend:8000
    devices:
      - /dev/ttyUSB0:/dev/ttyUSB0
    depends_on:
      - backend
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
tail -f backend/smartpark_entry_exit.log
tail -f serial_bridge/smartpark_bridge.log
```

### **Database Maintenance**
```bash
# Backup SQLite database
cp backend/smartpark_entry_exit.db backup/smartpark_$(date +%Y%m%d).db

# Clean old logs (keep last 30 days)
python -c "
from datetime import datetime, timedelta
from backend.database_entry_exit import SessionLocal, cleanup_old_logs

db = SessionLocal()
try:
    cleaned = cleanup_old_logs(db, days_to_keep=30)
    print(f'Cleaned {cleaned} old log entries')
finally:
    db.close()
"
```

### **AI Model Maintenance**
```bash
# Retrain AI model weekly
curl -X POST http://localhost:8000/api/ai/train_model

# Update occupancy stats
curl -X POST http://localhost:8000/api/ai/update_stats

# Check model performance
curl http://localhost:8000/api/ai/model_info
```

---

## 🔧 **Troubleshooting Guide**

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
from backend.database_entry_exit import engine
try:
    engine.connect()
    print('Database connected')
except Exception as e:
    print('Database error:', e)
"
```

#### **Frontend Not Showing 3 Slots**
```bash
# Check API response
curl http://localhost:8000/api/get_slots

# Verify environment variables
echo $REACT_APP_TOTAL_SLOTS  # Should be 3

# Check browser console for errors
# Verify API URL in .env file
```

#### **Real-time Updates Not Working**
```bash
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

---

## 🎯 **Success Metrics**

After successful deployment, verify:

- [ ] **Arduino**: IR sensors detect entry/exit, servo responds to commands
- [ ] **Serial Bridge**: Connects automatically, handles disconnections
- [ ] **Backend**: All APIs respond, WebSocket broadcasts work, 3 slots managed
- [ ] **Frontend**: Shows exactly 3 slots, real-time updates, AI insights display
- [ ] **End-to-End**: Car detection → Slot assignment → Frontend refresh < 3 seconds

---

## 🎉 **Deployment Complete!**

Your SmartPark Entry/Exit system is now fully operational with:

✅ **Entry/Exit Detection** - Arduino IR sensors → Automatic slot assignment  
✅ **3-Slot Management** - Perfect alignment with your frontend requirements  
✅ **Real-time Updates** - WebSocket broadcasting for instant UI refresh  
✅ **AI Predictions** - Smart occupancy forecasting and recommendations  
✅ **Production Ready** - Complete monitoring, logging, and maintenance tools  

**Your IoT parking system now intelligently manages 3 slots using entry/exit detection!** 🚗⚡🎯

---

## 📞 **Quick Start Commands**

```bash
# 1. Upload Arduino code
# arduino/smartpark_entry_exit.ino → Arduino UNO

# 2. Start Serial Bridge
cd serial_bridge && python event_bridge.py

# 3. Start Backend
cd backend && python main_entry_exit.py

# 4. Start Frontend
npm run dev

# 5. Test System
# Trigger IR sensors → Watch real-time updates
# Visit: http://localhost:5173
```

**Your SmartPark system is ready for real-world deployment!** 🎯
