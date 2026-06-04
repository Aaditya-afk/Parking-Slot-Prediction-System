# SmartPark Backend

IoT-based Parking Management System Backend with Arduino integration, ML predictions, and real-time APIs.

## 🚀 Features

- **Arduino Integration**: USB serial communication with IR sensors and servo motor
- **Real-time Updates**: WebSocket connections for live slot status
- **ML Predictions**: Machine learning-based availability forecasting
- **REST APIs**: Complete CRUD operations for slots, reservations, and analytics
- **Admin Dashboard**: System monitoring, analytics, and management
- **Database Support**: SQLite (development) and PostgreSQL (production)
- **Simulator Mode**: Test without Arduino hardware

## 📋 Prerequisites

- Python 3.10+
- Arduino UNO with IR sensors and servo motor
- USB cable for Arduino connection
- PostgreSQL (optional, for production)

## 🛠️ Installation

### 1. Clone and Setup

```bash
cd backend
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
cp .env.example .env
# Edit .env with your settings
```

Key settings in `.env`:
- `ARDUINO_PORT`: COM port for Arduino (e.g., COM3 on Windows)
- `DATABASE_URL`: Database connection string
- `SIMULATOR_MODE`: Set to `true` for testing without Arduino

### 3. Database Setup

```bash
# Initialize database and create tables
python -c "from database import init_db; init_db()"
```

### 4. Arduino Setup

1. Upload `arduino_sketch/smartpark_arduino.ino` to your Arduino UNO
2. Connect hardware as per wiring diagram in the sketch
3. Note the COM port (Device Manager on Windows)
4. Update `ARDUINO_PORT` in `.env`

## 🏃‍♂️ Running the Backend

### Development Mode

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

## 📡 API Endpoints

### Slots
- `GET /api/slots` - Get all parking slots
- `GET /api/slots/{id}` - Get specific slot
- `PUT /api/slots/{id}` - Update slot status
- `GET /api/parking-overview` - Complete parking overview

### Reservations
- `POST /api/reservations` - Create reservation
- `GET /api/reservations` - List reservations
- `PUT /api/reservations/{id}/cancel` - Cancel reservation
- `PUT /api/reservations/{id}/extend` - Extend reservation

### ML Forecasting
- `GET /api/forecast?minutes=30` - Get availability predictions
- `GET /api/forecast/summary` - Forecast summary
- `POST /api/forecast/train` - Train ML model

### Admin
- `GET /api/admin/analytics` - System analytics
- `GET /api/admin/logs` - System logs
- `GET /api/admin/occupancy-trends` - Usage trends
- `GET /api/admin/revenue-report` - Revenue analysis

### WebSocket
- `ws://localhost:8000/ws/slots` - Real-time slot updates

## 🔧 Hardware Setup

### Arduino Wiring

```
IR Sensors (6 slots):
- SLOT_1: Pin 2, SLOT_2: Pin 3, SLOT_3: Pin 4
- SLOT_4: Pin 5, SLOT_5: Pin 6, SLOT_6: Pin 7
- All sensors: VCC -> 5V, GND -> GND

Servo Motor (Barrier Gate):
- Signal -> Pin 9, VCC -> 5V, GND -> GND

USB Connection:
- Arduino to PC via USB cable
```

### Serial Communication

Arduino sends:
```
SLOT_1: OCCUPIED
SLOT_2: FREE
HEARTBEAT: 12345
```

Backend sends:
```
SERVO_OPEN
SERVO_CLOSE
STATUS
RESET
```

## 🤖 Machine Learning

### Training the Model

```bash
# Manual training
python ml_model.py

# Via API
curl -X POST http://localhost:8000/api/forecast/train
```

### Model Features

- Hour of day, day of week, weekend indicator
- Historical occupancy rates (1h, 24h)
- Active reservations count
- Recent sensor activity

### Prediction API

```bash
# Get 30-minute forecast for all slots
curl "http://localhost:8000/api/forecast?minutes=30"

# Get forecast for specific slot
curl "http://localhost:8000/api/forecast?minutes=60&slot_id=1"
```

## 🗄️ Database Schema

### Tables
- `slots`: Parking slot information and status
- `reservations`: User bookings and time slots
- `sensor_logs`: Historical sensor events
- `forecasts`: ML prediction results
- `system_logs`: Application events and errors

### Sample Data

The system automatically creates 6 parking slots (SLOT_1 to SLOT_6) on first run.

## 🔍 Testing

### Without Arduino (Simulator Mode)

Set `SIMULATOR_MODE=true` in `.env`. The system will generate random sensor events for testing.

### With Arduino

1. Connect Arduino with sensors
2. Set correct COM port in `.env`
3. Monitor serial output: `python -c "from serial_bridge import test_serial_bridge; test_serial_bridge()"`

### API Testing

```bash
# Health check
curl http://localhost:8000/api/health

# Get all slots
curl http://localhost:8000/api/slots

# Create reservation
curl -X POST http://localhost:8000/api/reservations \
  -H "Content-Type: application/json" \
  -d '{
    "slot_id": 1,
    "user_id": 123,
    "user_name": "John Doe",
    "start_time": "2024-01-01T10:00:00Z",
    "end_time": "2024-01-01T12:00:00Z"
  }'
```

## 📊 Monitoring

### System Health

```bash
curl http://localhost:8000/api/admin/system-status
```

### Real-time Logs

```bash
# View recent logs
curl "http://localhost:8000/api/admin/logs?limit=50"

# Filter by level
curl "http://localhost:8000/api/admin/logs?level=ERROR"
```

### Analytics Dashboard

Access comprehensive analytics at:
```bash
curl http://localhost:8000/api/admin/analytics
```

## 🚨 Troubleshooting

### Arduino Connection Issues

1. **Check COM Port**: Use Device Manager (Windows) or `ls /dev/tty*` (Linux/Mac)
2. **Driver Issues**: Install Arduino IDE and drivers
3. **Permission**: Run as administrator if needed
4. **Fallback**: Enable `SIMULATOR_MODE=true`

### Database Issues

```bash
# Reset database
rm smartpark.db
python -c "from database import init_db; init_db()"
```

### ML Model Issues

```bash
# Retrain model
python ml_model.py

# Check model status
curl http://localhost:8000/api/forecast/model-info
```

## 🔒 Security

### Production Deployment

1. **Environment Variables**: Use secure values for `SECRET_KEY`
2. **Database**: Use PostgreSQL with proper credentials
3. **CORS**: Configure `ALLOWED_ORIGINS` for your frontend domain
4. **HTTPS**: Use reverse proxy (nginx) with SSL certificates
5. **Firewall**: Restrict access to necessary ports only

### API Security

- Admin endpoints require authentication (implement JWT tokens)
- Input validation on all endpoints
- Rate limiting for public APIs
- Sanitized Arduino input processing

## 📈 Performance

### Optimization Tips

1. **Database Indexing**: Add indexes for frequently queried columns
2. **Connection Pooling**: Configure SQLAlchemy pool settings
3. **Caching**: Implement Redis for frequent queries
4. **Background Tasks**: Use Celery for heavy ML operations

### Scaling

- **Horizontal**: Multiple backend instances with load balancer
- **Database**: Read replicas for analytics queries
- **ML**: Separate ML service with job queue
- **WebSocket**: Redis pub/sub for multi-instance WebSocket

## 🤝 Integration with Frontend

### WebSocket Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/slots');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Update UI with real-time slot changes
};
```

### API Integration

```javascript
// Get parking overview
const response = await fetch('http://localhost:8000/api/parking-overview');
const data = await response.json();

// Create reservation
const reservation = await fetch('http://localhost:8000/api/reservations', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    slot_id: 1,
    user_id: 123,
    start_time: '2024-01-01T10:00:00Z',
    end_time: '2024-01-01T12:00:00Z'
  })
});
```

## 📝 Development

### Adding New Features

1. **Models**: Add SQLAlchemy models in `models.py`
2. **Schemas**: Add Pydantic schemas in `schemas.py`
3. **Routes**: Create new router in `routes/`
4. **Include**: Add router to `main.py`

### Code Structure

```
backend/
├── main.py              # FastAPI app and WebSocket
├── database.py          # Database connection
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic schemas
├── serial_bridge.py     # Arduino communication
├── ml_model.py          # Machine learning
├── utils.py             # Helper functions
├── routes/              # API endpoints
│   ├── slots.py
│   ├── reservations.py
│   ├── forecast.py
│   └── admin.py
└── arduino_sketch/      # Arduino code
```

## 📞 Support

For issues and questions:

1. Check logs: `tail -f smartpark.log`
2. Test Arduino: Use Arduino IDE Serial Monitor
3. Verify database: Check table contents
4. API testing: Use Postman or curl
5. WebSocket: Test with browser developer tools

## 🎯 Next Steps

1. **Authentication**: Implement JWT-based user authentication
2. **Payment**: Integrate payment gateway for reservations
3. **Mobile App**: Create mobile app with push notifications
4. **IoT Expansion**: Add more sensors (temperature, lighting)
5. **Advanced ML**: Implement LSTM for better predictions
6. **Cloud Deployment**: Deploy on AWS/Azure with CI/CD

---

**SmartPark Backend v1.0** - Built with FastAPI, SQLAlchemy, and Arduino integration.
