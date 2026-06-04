# 🔗 SmartPark Frontend-Backend Integration Guide

Complete guide to connect your React frontend with the SmartPark FastAPI backend.

## 🚀 Quick Integration Setup

### 1. **Environment Configuration**

Create `.env` file in your frontend root:
```bash
cp .env.example .env
```

Edit `.env`:
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws/slots
VITE_MOCK_DATA=false
VITE_ENABLE_REALTIME=true
```

### 2. **Start Backend Server**

```bash
cd backend
python run.py
# Backend runs on http://localhost:8000
```

### 3. **Start Frontend**

```bash
npm run dev
# Frontend runs on http://localhost:5173
```

## 🔧 Integration Components Added

### **API Client (`src/lib/api.ts`)**
- Complete TypeScript API client
- Automatic request/response transformation
- Error handling and retry logic
- WebSocket manager for real-time updates

### **React Hooks (`src/hooks/useSmartPark.ts`)**
- `useSlots()` - Get all parking slots with real-time updates
- `useParkingOverview()` - Dashboard overview data
- `useRealtimeSlots()` - WebSocket connection for live updates
- `useCreateReservation()` - Create new reservations
- `useForecast()` - ML-based availability predictions
- `useAnalytics()` - Admin dashboard analytics

### **New Components**
- `RealtimeIndicator` - Shows WebSocket connection status
- `PredictionCard` - Displays ML predictions with confidence
- `SystemStatusCard` - Backend health monitoring

## 📊 Updated Pages Integration

### **Dashboard Page**
Replace mock data usage:

```typescript
// OLD: Using mock data
import { mockSlots, mockLots } from '@/lib/mockData';

// NEW: Using real API
import { useDashboardStats, useSlotPredictions } from '@/hooks/useSmartPark';

export default function Dashboard() {
  const { stats, isLoading, isConnected } = useDashboardStats();
  const { predictions } = useSlotPredictions();
  
  // Use stats.totalSlots, stats.availableSlots, etc.
  // Use predictions for ML forecasts
}
```

### **Slots Page**
```typescript
import { useSlots, useRealtimeSlots } from '@/hooks/useSmartPark';

export default function Slots() {
  const { data: slots, isLoading } = useSlots();
  const { isConnected } = useRealtimeSlots(); // Auto real-time updates
  
  return (
    <div>
      <RealtimeIndicator />
      {slots?.map(slot => (
        <SlotCard key={slot.id} slot={slot} />
      ))}
    </div>
  );
}
```

### **Reservations Page**
```typescript
import { useCreateReservation, useReservations } from '@/hooks/useSmartPark';

export default function Reservations() {
  const createReservation = useCreateReservation();
  const { data: reservations } = useReservations();
  
  const handleReserve = (slotId: number) => {
    createReservation.mutate({
      slot_id: slotId,
      user_id: 123,
      start_time: new Date().toISOString(),
      end_time: new Date(Date.now() + 2 * 60 * 60 * 1000).toISOString()
    });
  };
}
```

### **Admin Page**
```typescript
import { useAnalytics, useSystemStatus } from '@/hooks/useSmartPark';

export default function Admin() {
  const { data: analytics } = useAnalytics();
  const { data: systemStatus } = useSystemStatus();
  
  return (
    <div>
      <SystemStatusCard />
      <PredictionCard />
      {/* Use analytics data for charts */}
    </div>
  );
}
```

## 🎯 Real-time Features

### **WebSocket Integration**
Automatic real-time updates when:
- Slot status changes (Arduino sensors)
- New reservations created
- System events occur

```typescript
// Automatically handled by useRealtimeSlots()
const { isConnected } = useRealtimeSlots();

// Manual WebSocket usage
import { SmartParkWebSocket } from '@/lib/api';

const ws = new SmartParkWebSocket();
ws.connect((data) => {
  console.log('Real-time update:', data);
});
```

### **Toast Notifications**
Real-time slot changes show toast notifications:
- 🚗 "SLOT_1 is now occupied"
- 🟢 "SLOT_2 is now available"

## 🤖 ML Predictions Integration

### **Availability Forecasting**
```typescript
import { useForecast } from '@/hooks/useSmartPark';

const { data: forecasts } = useForecast({ minutes: 30 });

forecasts?.forEach(prediction => {
  console.log(`${prediction.slot_label}: ${prediction.probability_free * 100}% chance free`);
});
```

### **Prediction Cards**
```typescript
import PredictionCard from '@/components/PredictionCard';

{forecasts?.map(prediction => (
  <PredictionCard key={prediction.slot_id} prediction={prediction} />
))}
```

## 📱 Component Updates

### **Enhanced SlotCard**
Your existing `SlotCard` component now receives real-time data:

```typescript
// SlotCard automatically updates when backend sends changes
<SlotCard 
  slot={slot} // Real-time data from useSlots()
  onReserve={(slotId) => createReservation.mutate({...})}
/>
```

### **StatsCard Integration**
```typescript
// Use real backend data instead of mock
const { stats } = useDashboardStats();

<StatsCard
  title="Available Slots"
  value={stats?.availableSlots || 0}
  icon={Zap}
  trend={{ value: 12, isPositive: true }}
/>
```

## 🔧 Development Workflow

### **1. Backend Development Mode**
```bash
cd backend
# Enable simulator mode for testing without Arduino
echo "SIMULATOR_MODE=true" >> .env
python run.py
```

### **2. Frontend Development**
```bash
# Enable mock data fallback during development
echo "VITE_MOCK_DATA=true" >> .env
npm run dev
```

### **3. Full Integration Testing**
```bash
# Backend with real Arduino
cd backend && python run.py

# Frontend with real API
cd .. && npm run dev

# Test real-time updates
python backend/test_system.py
```

## 🚨 Troubleshooting

### **API Connection Issues**
```typescript
// Check backend health
import { useHealth } from '@/hooks/useSmartPark';

const { data: health, error } = useHealth();
if (error) {
  console.error('Backend not reachable:', error);
}
```

### **WebSocket Connection**
```typescript
const { isConnected } = useRealtimeSlots();
if (!isConnected) {
  // Show offline indicator
  // Fallback to polling
}
```

### **CORS Issues**
Update backend `.env`:
```env
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

## 📊 Data Flow

```
Arduino → Backend → WebSocket → Frontend
   ↓         ↓         ↓         ↓
Sensors → FastAPI → Real-time → React UI
   ↓         ↓         ↓         ↓
IR/Servo → Database → Updates → Toast/UI
```

## 🎉 Features Now Available

### **✅ Real-time Parking Status**
- Live slot updates from Arduino sensors
- WebSocket notifications
- Automatic UI refresh

### **✅ Smart Reservations**
- Create/cancel reservations
- Automatic servo gate control
- Conflict detection

### **✅ ML Predictions**
- 30-minute availability forecasts
- Confidence scoring
- Historical pattern analysis

### **✅ Admin Dashboard**
- System health monitoring
- Revenue analytics
- Occupancy trends
- Error logging

### **✅ Arduino Integration**
- USB serial communication
- Sensor event logging
- Servo motor control
- Auto-reconnection

## 🚀 Next Steps

1. **Test Integration**: Run both backend and frontend
2. **Connect Arduino**: Upload sketch and connect sensors
3. **Customize UI**: Adapt components to your design
4. **Add Features**: Extend with payments, notifications, etc.
5. **Deploy**: Use Docker for production deployment

---

**Your SmartPark system is now fully integrated! 🎯**

The frontend will automatically connect to the backend, receive real-time updates, and provide a complete IoT parking management experience.
