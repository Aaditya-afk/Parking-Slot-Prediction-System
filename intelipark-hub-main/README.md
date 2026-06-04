# SmartPark - IoT Smart Parking System

A comprehensive real-time parking management system powered by Arduino IoT sensors, AI predictions, and modern web technologies.

## 🚀 Features

- **Real-time Monitoring**: Live parking slot status updates via Arduino IR sensors
- **Smart Reservations**: Book slots in advance with QR code confirmation
- **AI Predictions**: Machine learning forecasts for slot availability
- **User Feedback**: Integrated rating and feedback system
- **Admin Dashboard**: Comprehensive monitoring and management interface
- **Responsive Design**: Works seamlessly on mobile, tablet, and desktop

## 🏗️ Architecture

```
Arduino (IR Sensors + Servo) 
    ↓ USB Serial
Python Serial Gateway
    ↓ HTTP/WebSocket
Backend API (Node.js/FastAPI)
    ↓
PostgreSQL Database
    ↓
React Frontend (Real-time updates via WebSocket)
```

## 📦 Tech Stack

### Frontend
- React 18 + TypeScript
- Tailwind CSS (custom design system)
- Shadcn UI components
- React Router for navigation
- TanStack Query for data management

### Backend (To be implemented)
- Node.js + Express OR Python + FastAPI
- WebSocket for real-time updates
- PostgreSQL database
- RESTful API endpoints

### Hardware
- Arduino board
- IR sensors for slot detection
- Servo motor for gate control
- USB serial connection to PC

### ML Pipeline (To be implemented)
- Python + Jupyter notebooks
- Prophet or XGBoost for forecasting
- Historical data analysis

## 🛠️ Installation

### Prerequisites
- Node.js 18+ and npm
- Python 3.8+ (for serial gateway)
- PostgreSQL 14+ (for backend)
- Arduino IDE (for hardware setup)

### Frontend Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

### Backend Setup (Coming Soon)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run database migrations
npm run migrate

# Start backend server
npm run server
```

### Serial Gateway Setup

```bash
# Install Python serial library
pip install pyserial

# Run gateway script
python gateway/serial_reader.py
```

## 📡 API Endpoints

### Parking Lots
- `GET /api/lots` - List all parking lots
- `GET /api/lots/{lot_id}/slots` - Get slots for a specific lot

### Reservations
- `POST /api/reservations` - Create new reservation
- `GET /api/reservations` - List user reservations
- `POST /api/slots/{slot_id}/release` - Release a reservation

### Sensors
- `POST /api/sensor/update` - Receive sensor data from Arduino

### Feedback
- `POST /api/feedback` - Submit user feedback
- `GET /api/feedback` - Get feedback (admin only)

- `GET /api/forecast?horizon=30` - Get availability predictions

### WebSocket Events
- `slot_update` - Real-time slot status changes
- `reservation_update` - Reservation status changes
- `feedback_received` - New feedback submitted
- `sensor_health` - Device health monitoring

**Note**: This is a demonstration project. Backend API, serial gateway, and ML components require additional implementation. The frontend provides a complete UI mockup with all planned features.
