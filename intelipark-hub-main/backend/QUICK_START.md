# 🚀 SmartPark Backend - Quick Start Guide

Get your SmartPark IoT parking system running in 5 minutes!

## ⚡ Super Quick Setup (Windows)

1. **Run Setup Script**
   ```cmd
   cd backend
   scripts\setup.bat
   ```

2. **Configure Arduino Port**
   - Edit `.env` file
   - Set `ARDUINO_PORT=COM3` (check Device Manager for correct port)
   - Or set `SIMULATOR_MODE=true` for testing without Arduino

3. **Start Backend**
   ```cmd
   scripts\start.bat
   ```

4. **Test System**
   ```cmd
   scripts\test.bat
   ```

## ⚡ Super Quick Setup (Linux/Mac)

1. **Run Setup Script**
   ```bash
   cd backend
   chmod +x scripts/*.sh
   ./scripts/setup.sh
   ```

2. **Configure Arduino Port**
   ```bash
   nano .env
   # Set ARDUINO_PORT=/dev/ttyUSB0
   # Or SIMULATOR_MODE=true
   ```

3. **Start Backend**
   ```bash
   ./scripts/start.sh
   ```

## 🔧 Manual Setup (If Scripts Don't Work)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup environment
cp .env.example .env
# Edit .env with your settings

# 3. Initialize database
python -c "from database import init_db; init_db()"

# 4. Start server
python run.py
```

## 🎯 Verify Installation

Open browser and check:
- **API Health**: http://localhost:8000/api/health
- **Parking Overview**: http://localhost:8000/api/parking-overview
- **API Docs**: http://localhost:8000/docs

## 🔌 Arduino Setup

1. **Upload Sketch**
   - Open `arduino_sketch/smartpark_arduino.ino` in Arduino IDE
   - Upload to Arduino UNO

2. **Hardware Wiring**
   ```
   IR Sensors: Pins 2-7 (6 sensors)
   Servo Motor: Pin 9
   USB: Connect to PC
   ```

3. **Test Connection**
   ```bash
   python -c "from serial_bridge import test_serial_bridge; test_serial_bridge()"
   ```

## 🤖 Train ML Model

```bash
# Train with 30 days of data
python scripts/train_ml.py train --days 30

# Or via API
curl -X POST http://localhost:8000/api/forecast/train
```

## 📱 Frontend Integration

Your React frontend can now connect to:
- **REST API**: `http://localhost:8000/api/`
- **WebSocket**: `ws://localhost:8000/ws/slots`

Example:
```javascript
// Get all slots
const slots = await fetch('http://localhost:8000/api/slots')
  .then(res => res.json());

// Real-time updates
const ws = new WebSocket('ws://localhost:8000/ws/slots');
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  // Update your UI
};
```

## 🚨 Troubleshooting

### Arduino Not Connecting?
- Check COM port in Device Manager (Windows) or `ls /dev/tty*` (Linux)
- Install Arduino drivers
- Set `SIMULATOR_MODE=true` in `.env` for testing

### Database Issues?
```bash
# Reset database
rm smartpark.db
python -c "from database import init_db; init_db()"
```

### Port Already in Use?
- Change `API_PORT=8001` in `.env`
- Or kill existing process: `taskkill /f /im python.exe` (Windows)

## 📊 Test Everything

```bash
# Run comprehensive tests
python test_system.py

# Test specific features
curl http://localhost:8000/api/slots
curl http://localhost:8000/api/forecast?minutes=30
```

## 🎉 You're Ready!

Your SmartPark backend is now running with:
- ✅ 6 parking slots (SLOT_1 to SLOT_6)
- ✅ Real-time Arduino communication
- ✅ ML-based availability predictions
- ✅ WebSocket for live updates
- ✅ Complete REST API
- ✅ Admin dashboard endpoints

## 📚 Next Steps

1. **Connect Frontend**: Point your React app to `http://localhost:8000`
2. **Add Hardware**: Connect IR sensors and servo motor
3. **Customize**: Modify slot count, pricing, features
4. **Deploy**: Use Docker or cloud deployment
5. **Monitor**: Check `/api/admin/analytics` for insights

## 🔗 Useful Links

- **API Documentation**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Full README**: [README.md](README.md)
- **Frontend Repo**: https://github.com/abhishek123405/intelipark-hub

---

**Need Help?** Check the logs at `smartpark.log` or run `python test_system.py` for diagnostics.
