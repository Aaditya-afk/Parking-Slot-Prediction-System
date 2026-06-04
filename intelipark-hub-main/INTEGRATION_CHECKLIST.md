# 🔗 Integration Checklist - Connect All Components

## ✅ What's Already Done

### Backend Files Created:
- ✅ `backend/main_prediction.py` - Complete prediction system with timers
- ✅ `backend/main_ml.py` - ML-driven backend (70 slots)
- ✅ `backend/ml/dataset_generator.py` - Synthetic data generator
- ✅ `backend/ml/predictor_model.py` - ML model training

### Frontend Files Created:
- ✅ `src/components/SlotWithTimer.tsx` - Slot with countdown timer
- ✅ `src/components/SlotCardEnhanced.tsx` - Enhanced slot card
- ✅ `src/pages/PredictedAvailability.tsx` - Predictions page
- ✅ `src/pages/Analytics.tsx` - Analytics dashboard

### Documentation:
- ✅ `PREDICTION_SYSTEM_GUIDE.md` - Complete system guide
- ✅ `START_PREDICTION_SYSTEM.bat` - Quick launcher

## 🔧 Integration Steps

### Step 1: Update Routes (Add New Pages)

Edit `src/App.tsx` or your router file to add:

```tsx
import PredictedAvailability from './pages/PredictedAvailability';
import Analytics from './pages/Analytics';

// Add these routes:
<Route path="/predictions" element={<PredictedAvailability />} />
<Route path="/analytics" element={<Analytics />} />
```

### Step 2: Update Navigation

Add links to your navbar/sidebar:

```tsx
<Link to="/predictions">Predicted Availability</Link>
<Link to="/analytics">Analytics</Link>
```

### Step 3: Replace Existing Slots Page

Option A - Use SlotWithTimer component:
```tsx
// In src/pages/Slots.tsx
import { SlotWithTimer } from '@/components/SlotWithTimer';

// Replace SlotCard with:
<SlotWithTimer 
  slot={slot}
  onBook={handleBook}
  onFree={handleFree}
/>
```

Option B - Keep existing and add timer feature:
- The existing BookingModal already has duration selection
- Just need to connect to the new backend

### Step 4: Update API Base URL

In `src/services/smartparkAPI.ts`, ensure it points to:
```typescript
const baseURL = 'http://localhost:8000';
```

### Step 5: Add WebSocket Connection

Create `src/hooks/useWebSocket.ts`:

```typescript
import { useEffect, useState } from 'react';

export function useWebSocket(url: string) {
  const [data, setData] = useState<any>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);

  useEffect(() => {
    const websocket = new WebSocket(url);
    
    websocket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setData(message);
    };

    setWs(websocket);

    return () => websocket.close();
  }, [url]);

  return { data, ws };
}
```

Use in components:
```typescript
const { data } = useWebSocket('ws://localhost:8000/ws/realtime');

useEffect(() => {
  if (data?.type === 'slot_freed') {
    // Refresh slots
    fetchSlots();
  }
}, [data]);
```

## 🚀 Quick Start Commands

### Start Prediction Backend:
```bash
cd backend
python main_prediction.py
```

### Start Frontend:
```bash
npm run dev
```

### Or use the launcher:
```bash
START_PREDICTION_SYSTEM.bat
```

## 🧪 Testing the System

### Test 1: Book a Slot with Timer
1. Go to http://localhost:5173
2. Click an available (green) slot
3. Select duration: 30 minutes
4. Confirm booking
5. ✅ Slot turns red with countdown timer: `29m 59s`

### Test 2: Auto-Release
1. Wait for timer to reach 0
2. ✅ Slot automatically turns green
3. ✅ All connected clients see the update

### Test 3: Predictions
1. Go to http://localhost:5173/predictions
2. ✅ See slots predicted to be free soon
3. ✅ Smart recommendations displayed

### Test 4: Analytics
1. Go to http://localhost:5173/analytics
2. ✅ See pie chart, bar chart, metrics
3. ✅ Real-time occupancy stats

## 📊 API Integration

### Book Slot with Duration:
```typescript
const bookSlot = async (slotId: number, duration: number) => {
  const response = await fetch(`http://localhost:8000/api/slots/book/${slotId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      slot_id: slotId,
      duration_minutes: duration,
      user_name: 'Guest',
      user_email: 'guest@example.com'
    })
  });
  return response.json();
};
```

### Get Predictions:
```typescript
const getPredictions = async () => {
  const response = await fetch('http://localhost:8000/api/predictions');
  const data = await response.json();
  return data.data.predictions;
};
```

### Get Recommendations:
```typescript
const getRecommendations = async () => {
  const response = await fetch('http://localhost:8000/api/recommendations');
  const data = await response.json();
  return data.data.soon_available;
};
```

## 🎯 Final Integration Points

### 1. Dashboard Page
- Use existing dashboard
- Add link to Predictions page
- Add link to Analytics page

### 2. Slots/Parking Page
- Replace with SlotWithTimer component
- Or add timer display to existing SlotCard
- Connect to new booking API

### 3. Navigation
- Add "Predictions" menu item
- Add "Analytics" menu item

### 4. Real-Time Updates
- Add WebSocket hook
- Listen for slot_freed events
- Auto-refresh slot list

## 🔍 Troubleshooting

### Backend not starting?
```bash
# Install dependencies
pip install fastapi uvicorn websockets

# Run
python main_prediction.py
```

### Frontend not showing timers?
- Check if backend is running on port 8000
- Check browser console for errors
- Verify API calls in Network tab

### WebSocket not connecting?
- Ensure backend WebSocket endpoint is running
- Check firewall settings
- Try polling as fallback (refresh every 5s)

## 📝 Summary

You now have:
1. ✅ Backend with timers and auto-release
2. ✅ ML prediction system
3. ✅ Frontend components with countdown
4. ✅ Predictions page
5. ✅ Analytics dashboard
6. ✅ WebSocket real-time sync
7. ✅ Complete documentation

**Next Steps:**
1. Run `START_PREDICTION_SYSTEM.bat`
2. Add routes to your router
3. Update navigation menu
4. Test the booking flow
5. Enjoy your AI-powered parking system! 🎉
