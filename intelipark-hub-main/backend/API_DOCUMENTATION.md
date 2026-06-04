# SmartPark API Documentation

Complete API reference for the SmartPark IoT Parking Management System.

## Base URL
```
http://localhost:8000
```

## Authentication
Currently, most endpoints are public. Admin endpoints will require JWT authentication in production.

---

## 🚗 Slots API

### Get All Slots
```http
GET /api/slots
```

**Response:**
```json
[
  {
    "id": 1,
    "slot_label": "SLOT_1",
    "status": "FREE",
    "last_updated": "2024-01-01T12:00:00Z",
    "has_active_reservation": false,
    "reservation_end_time": null
  }
]
```

### Get Specific Slot
```http
GET /api/slots/{slot_id}
```

### Update Slot Status
```http
POST /api/slots/update
```

**Body:**
```json
{
  "slot_label": "SLOT_1",
  "status": "OCCUPIED"
}
```

### Get Parking Overview
```http
GET /api/parking-overview
```

**Response:**
```json
{
  "total_slots": 6,
  "free_slots": 4,
  "occupied_slots": 1,
  "reserved_slots": 1,
  "slots": [...]
}
```

---

## 📅 Reservations API

### Create Reservation
```http
POST /api/reservations
```

**Body:**
```json
{
  "slot_id": 1,
  "user_id": 123,
  "user_name": "John Doe",
  "user_email": "john@example.com",
  "start_time": "2024-01-01T14:00:00Z",
  "end_time": "2024-01-01T16:00:00Z"
}
```

**Response:**
```json
{
  "id": 1,
  "slot_id": 1,
  "user_id": 123,
  "status": "active",
  "created_at": "2024-01-01T12:00:00Z"
}
```

### Get Reservations
```http
GET /api/reservations?user_id=123&status=active&limit=50
```

### Cancel Reservation
```http
PUT /api/reservations/{reservation_id}/cancel
```

### Extend Reservation
```http
PUT /api/reservations/{reservation_id}/extend
```

**Body:**
```json
{
  "minutes": 30
}
```

---

## 🔮 Forecast API

### Get Availability Forecast
```http
GET /api/forecast?minutes=30&slot_id=1
```

**Parameters:**
- `minutes` (required): Forecast horizon (5-1440 minutes)
- `slot_id` (optional): Specific slot ID

**Response:**
```json
[
  {
    "slot_id": 1,
    "slot_label": "SLOT_1",
    "horizon_minutes": 30,
    "probability_free": 0.75,
    "confidence": "high",
    "generated_at": "2024-01-01T12:00:00Z"
  }
]
```

### Get Forecast Summary
```http
GET /api/forecast/summary?minutes=60
```

**Response:**
```json
{
  "forecast_horizon_minutes": 60,
  "summary": {
    "total_slots": 6,
    "likely_free": 4,
    "likely_occupied": 1,
    "uncertain": 1
  },
  "slot_predictions": [...]
}
```

### Train ML Model
```http
POST /api/forecast/train
```

### Get Model Info
```http
GET /api/forecast/model-info
```

---

## 👨‍💼 Admin API

### Get Analytics
```http
GET /api/admin/analytics
```

**Response:**
```json
{
  "total_slots": 6,
  "current_occupancy_rate": 33.3,
  "avg_daily_occupancy": 45.2,
  "total_reservations_today": 12,
  "revenue_today": 150.0,
  "peak_hours": [9, 14, 18],
  "recent_events": [...]
}
```

### Get System Logs
```http
GET /api/admin/logs?level=ERROR&component=serial_bridge&limit=100
```

### Get Sensor Logs
```http
GET /api/admin/sensor-logs?slot_id=1&hours=24
```

### Get Occupancy Trends
```http
GET /api/admin/occupancy-trends?days=7
```

### Get Revenue Report
```http
GET /api/admin/revenue-report?days=30
```

### Get System Status
```http
GET /api/admin/system-status
```

**Response:**
```json
{
  "overall_status": "healthy",
  "components": {
    "database": "healthy",
    "sensors": "healthy",
    "error_rate": "healthy"
  },
  "metrics": {
    "recent_sensor_events": 45,
    "recent_errors": 0,
    "uptime_hours": 24
  }
}
```

---

## 🔌 WebSocket API

### Real-time Slot Updates
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/slots');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Slot update:', data);
};
```

**Message Format:**
```json
{
  "type": "slot_update",
  "slot_id": 1,
  "slot_label": "SLOT_1",
  "status": "OCCUPIED",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

## 🏥 Health & Monitoring

### Health Check
```http
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "serial_connected": true,
  "active_websockets": 3
}
```

### Root Endpoint
```http
GET /
```

---

## 📊 Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `409` - Conflict (e.g., slot not available)
- `500` - Internal Server Error

## 🔧 Error Response Format

```json
{
  "error": "ValidationError",
  "message": "Invalid reservation time",
  "details": {
    "field": "start_time",
    "issue": "Must be in the future"
  }
}
```

---

## 📝 Usage Examples

### Frontend Integration

```javascript
// Get parking overview
const overview = await fetch('/api/parking-overview')
  .then(res => res.json());

// Create reservation
const reservation = await fetch('/api/reservations', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    slot_id: 1,
    user_id: 123,
    start_time: '2024-01-01T14:00:00Z',
    end_time: '2024-01-01T16:00:00Z'
  })
}).then(res => res.json());

// WebSocket for real-time updates
const ws = new WebSocket('ws://localhost:8000/ws/slots');
ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  updateSlotUI(update.slot_id, update.status);
};
```

### Arduino Integration

The backend automatically processes Arduino messages:

```
// Arduino sends:
SLOT_1: OCCUPIED
SLOT_2: FREE

// Backend sends:
SERVO_OPEN
SERVO_CLOSE
```

### ML Predictions

```javascript
// Get 30-minute forecast
const forecast = await fetch('/api/forecast?minutes=30')
  .then(res => res.json());

forecast.forEach(prediction => {
  console.log(`${prediction.slot_label}: ${prediction.probability_free * 100}% chance free`);
});
```

---

## 🔒 Rate Limiting

- Public endpoints: 100 requests/minute
- Admin endpoints: 50 requests/minute
- WebSocket connections: 10 per IP

## 📱 CORS Configuration

Configure allowed origins in `.env`:
```
ALLOWED_ORIGINS=http://localhost:3000,https://yourfrontend.com
```

---

## 🐛 Debugging

### Enable Debug Mode
Set `DEBUG=true` in `.env` for detailed logging.

### Test Endpoints
```bash
# Test all endpoints
python test_system.py

# Test specific endpoint
curl -X GET http://localhost:8000/api/slots
```

### Monitor Logs
```bash
# View real-time logs
tail -f smartpark.log

# Check system logs via API
curl http://localhost:8000/api/admin/logs?level=ERROR
```
