# SmartPark API Documentation

## Base URL
```
http://localhost:3000/api
```

## Authentication
All endpoints except public slot viewing require JWT authentication.

```
Authorization: Bearer <token>
```

---

## Endpoints

### 1. Get All Parking Lots

**GET** `/lots`

Returns list of all parking lots with availability info.

**Response**
```json
{
  "success": true,
  "data": [
    {
      "id": "lot-a",
      "name": "Main Parking Lot A",
      "totalSlots": 20,
      "availableSlots": 12,
      "location": {
        "lat": 37.7749,
        "lng": -122.4194,
        "address": "123 Smart Street, Tech City"
      }
    }
  ]
}
```

---

### 2. Get Slots for Lot

**GET** `/lots/{lot_id}/slots`

Returns all slots for a specific parking lot.

**Parameters**
- `lot_id` (path): Parking lot identifier

**Query Parameters**
- `status` (optional): Filter by status (available, occupied, reserved, maintenance)

**Response**
```json
{
  "success": true,
  "data": [
    {
      "id": "A-01",
      "lotId": "lot-a",
      "slotNumber": "A-01",
      "status": "available",
      "predictedFreeInMinutes": 0,
      "lastUpdated": "2025-10-02T12:34:56Z"
    }
  ]
}
```

---

### 3. Create Reservation

**POST** `/reservations`

Create a new parking slot reservation.

**Request Body**
```json
{
  "slotId": "A-01",
  "lotId": "lot-a",
  "startTime": "2025-10-02T14:00:00Z",
  "endTime": "2025-10-02T16:00:00Z"
}
```

**Response**
```json
{
  "success": true,
  "data": {
    "id": "res-001",
    "userId": "user-001",
    "slotId": "A-01",
    "lotId": "lot-a",
    "startTime": "2025-10-02T14:00:00Z",
    "endTime": "2025-10-02T16:00:00Z",
    "qrCode": "QR-RES-001-ABC123",
    "status": "pending",
    "createdAt": "2025-10-02T12:34:56Z"
  }
}
```

**Error Cases**
- 409: Slot already reserved for that time
- 400: Invalid time range
- 404: Slot not found

---

### 4. Get User Reservations

**GET** `/reservations`

Get all reservations for authenticated user.

**Query Parameters**
- `status` (optional): Filter by status

**Response**
```json
{
  "success": true,
  "data": [
    {
      "id": "res-001",
      "slotId": "A-01",
      "status": "active",
      "startTime": "2025-10-02T14:00:00Z",
      "endTime": "2025-10-02T16:00:00Z",
      "qrCode": "QR-RES-001-ABC123"
    }
  ]
}
```

---

### 5. Release Slot

**POST** `/slots/{slot_id}/release`

Manually release a reserved or occupied slot.

**Parameters**
- `slot_id` (path): Slot identifier

**Response**
```json
{
  "success": true,
  "message": "Slot A-01 released successfully"
}
```

---

### 6. Sensor Update

**POST** `/sensor/update`

Receive sensor data from Arduino gateway.

**Request Body**
```json
{
  "deviceId": "arduino-01",
  "lotId": "lot-a",
  "slotId": "A-03",
  "timestamp": "2025-10-02T12:34:56Z",
  "occupied": true,
  "battery": 3.8
}
```

**Response**
```json
{
  "success": true,
  "message": "Sensor data recorded"
}
```

---

### 7. Submit Feedback

**POST** `/feedback`

Submit user feedback.

**Request Body**
```json
{
  "rating": 5,
  "type": "general",
  "comment": "Great system! Very easy to use."
}
```

**Validation**
- `rating`: 1-5
- `type`: complaint | suggestion | general
- `comment`: max 1000 characters

**Response**
```json
{
  "success": true,
  "data": {
    "id": "fb-001",
    "userId": "user-001",
    "rating": 5,
    "type": "general",
    "comment": "Great system!",
    "createdAt": "2025-10-02T12:34:56Z"
  }
}
```

---

### 8. Get Feedback (Admin)

**GET** `/feedback`

Get all user feedback (admin only).

**Query Parameters**
- `type` (optional): Filter by feedback type
- `minRating` (optional): Minimum rating filter
- `limit` (optional): Number of results (default: 50)

**Response**
```json
{
  "success": true,
  "data": [
    {
      "id": "fb-001",
      "userId": "user-001",
      "rating": 5,
      "type": "general",
      "comment": "Great system!",
      "createdAt": "2025-10-02T12:34:56Z"
    }
  ],
  "stats": {
    "averageRating": 4.2,
    "totalFeedback": 156
  }
}
```

---

### 9. Get Forecast

**GET** `/forecast`

Get ML predictions for slot availability.

**Query Parameters**
- `horizon` (required): Prediction horizon in minutes (max: 120)
- `lotId` (optional): Filter by parking lot

**Response**
```json
{
  "success": true,
  "data": {
    "generatedAt": "2025-10-02T12:34:56Z",
    "horizon": 30,
    "predictions": [
      {
        "slotId": "A-01",
        "timestamp": "2025-10-02T13:00:00Z",
        "predictedOccupancy": 0.75,
        "confidence": 0.88
      }
    ]
  }
}
```

---

## WebSocket Events

### Connection
```javascript
const ws = new WebSocket('ws://localhost:3000/ws/realtime');
```

### Subscribe to Events
```javascript
ws.send(JSON.stringify({
  type: 'subscribe',
  channels: ['slot_updates', 'reservations']
}));
```

### Event Types

#### slot_update
Sent when slot status changes.
```json
{
  "type": "slot_update",
  "data": {
    "slotId": "A-01",
    "status": "occupied",
    "timestamp": "2025-10-02T12:34:56Z"
  }
}
```

#### reservation_update
Sent when reservation status changes.
```json
{
  "type": "reservation_update",
  "data": {
    "reservationId": "res-001",
    "status": "active",
    "slotId": "A-01"
  }
}
```

#### feedback_received
Sent when new feedback is submitted (admin channel).
```json
{
  "type": "feedback_received",
  "data": {
    "feedbackId": "fb-001",
    "rating": 5,
    "type": "general"
  }
}
```

#### sensor_health
Sent when sensor health status changes.
```json
{
  "type": "sensor_health",
  "data": {
    "deviceId": "arduino-01",
    "status": "online",
    "battery": 3.8,
    "lastSeen": "2025-10-02T12:34:56Z"
  }
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "success": false,
  "error": {
    "code": "SLOT_ALREADY_RESERVED",
    "message": "This slot is already reserved for the selected time",
    "details": {}
  }
}
```

### Common Error Codes
- `UNAUTHORIZED`: Authentication required
- `FORBIDDEN`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `VALIDATION_ERROR`: Invalid request data
- `SLOT_ALREADY_RESERVED`: Slot not available
- `DEVICE_OFFLINE`: Arduino device disconnected

---

## Rate Limiting

- Public endpoints: 100 requests/minute
- Authenticated endpoints: 300 requests/minute
- Admin endpoints: 1000 requests/minute

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1633024800
```
