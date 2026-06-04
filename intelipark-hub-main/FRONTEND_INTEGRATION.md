# 🌐 Frontend Integration Guide - SmartPark 3-Slot System

Complete guide to integrate your existing React frontend with the SmartPark backend for real-time IoT parking management.

## 🎯 **System Overview**

Your React frontend will connect to:
- **Backend API**: `http://localhost:8000` (FastAPI)
- **WebSocket**: `ws://localhost:8000/ws/realtime` (Real-time updates)
- **Arduino**: Via backend serial bridge (transparent to frontend)

---

## 📊 **API Endpoints Reference**

### **Core Endpoints Your Frontend Needs**

| Endpoint | Method | Purpose | Component Usage |
|----------|--------|---------|-----------------|
| `/api/get_slots` | GET | Get all slot statuses | Dashboard, Slots page |
| `/api/update_slots` | POST | Update from Arduino | Backend only |
| `/api/open_gate` | POST | Open parking gate | Reservation confirmation |
| `/api/close_gate` | POST | Close parking gate | Exit process |
| `/api/reserve_slot` | POST | Reserve a slot | Booking form |
| `/api/release_slot` | POST | Release reservation | Check-out |
| `/api/reservations` | GET | Get reservations | My Bookings page |
| `/ws/realtime` | WebSocket | Live updates | All components |

---

## 🔧 **Frontend Code Examples**

### **1. API Service Setup**

Create `src/services/smartparkApi.js`:

```javascript
// SmartPark API Service
class SmartParkAPI {
  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    this.wsURL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws/realtime';
  }

  // Get all parking slots
  async getSlots() {
    try {
      const response = await fetch(`${this.baseURL}/api/get_slots`);
      const data = await response.json();
      
      if (data.success) {
        return {
          slots: data.data.slots,
          summary: data.data.summary
        };
      }
      throw new Error('Failed to fetch slots');
    } catch (error) {
      console.error('Error fetching slots:', error);
      throw error;
    }
  }

  // Reserve a parking slot
  async reserveSlot(slotNumber, userDetails) {
    try {
      const response = await fetch(`${this.baseURL}/api/reserve_slot`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          slot_number: slotNumber,
          user_name: userDetails.name,
          user_email: userDetails.email,
          user_phone: userDetails.phone,
          vehicle_number: userDetails.vehicle,
          duration_hours: userDetails.duration || 2
        })
      });

      const data = await response.json();
      
      if (data.success) {
        return data.data;
      }
      throw new Error(data.message || 'Reservation failed');
    } catch (error) {
      console.error('Error reserving slot:', error);
      throw error;
    }
  }

  // Release a slot
  async releaseSlot(reservationId) {
    try {
      const response = await fetch(`${this.baseURL}/api/release_slot`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          reservation_id: reservationId
        })
      });

      const data = await response.json();
      
      if (data.success) {
        return data.data;
      }
      throw new Error(data.message || 'Release failed');
    } catch (error) {
      console.error('Error releasing slot:', error);
      throw error;
    }
  }

  // Open gate
  async openGate() {
    try {
      const response = await fetch(`${this.baseURL}/api/open_gate`, {
        method: 'POST'
      });
      
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error opening gate:', error);
      throw error;
    }
  }

  // Close gate
  async closeGate() {
    try {
      const response = await fetch(`${this.baseURL}/api/close_gate`, {
        method: 'POST'
      });
      
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error closing gate:', error);
      throw error;
    }
  }

  // Get user reservations
  async getReservations(userEmail) {
    try {
      const url = userEmail 
        ? `${this.baseURL}/api/reservations?user_email=${encodeURIComponent(userEmail)}`
        : `${this.baseURL}/api/reservations`;
        
      const response = await fetch(url);
      const data = await response.json();
      
      if (data.success) {
        return data.data;
      }
      throw new Error('Failed to fetch reservations');
    } catch (error) {
      console.error('Error fetching reservations:', error);
      throw error;
    }
  }

  // ML Predictions
  async getPredictions(minutesAhead = 15) {
    try {
      const response = await fetch(`${this.baseURL}/api/ml/predict/all?minutes_ahead=${minutesAhead}`);
      const data = await response.json();
      
      if (data.success) {
        return data.data;
      }
      throw new Error('Failed to fetch predictions');
    } catch (error) {
      console.error('Error fetching predictions:', error);
      throw error;
    }
  }
}

export const smartparkApi = new SmartParkAPI();
```

### **2. WebSocket Hook for Real-time Updates**

Create `src/hooks/useRealtimeUpdates.js`:

```javascript
import { useState, useEffect, useRef } from 'react';

export const useRealtimeUpdates = (onSlotUpdate) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const connect = () => {
    try {
      const wsURL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws/realtime';
      wsRef.current = new WebSocket(wsURL);

      wsRef.current.onopen = () => {
        console.log('🔌 Connected to SmartPark real-time updates');
        setIsConnected(true);
        
        // Send subscription message
        wsRef.current.send(JSON.stringify({
          type: 'subscribe',
          channels: ['slot_updates', 'gate_events']
        }));
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'slot_update') {
            console.log('📡 Received slot update:', data);
            setLastUpdate(data);
            if (onSlotUpdate) {
              onSlotUpdate(data);
            }
          } else if (data.type === 'connection') {
            console.log('✅ WebSocket connection confirmed');
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      wsRef.current.onclose = () => {
        console.log('🔌 WebSocket disconnected');
        setIsConnected(false);
        
        // Attempt to reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('🔄 Attempting to reconnect...');
          connect();
        }, 3000);
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        setIsConnected(false);
      };

    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      setIsConnected(false);
    }
  };

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsConnected(false);
  };

  const sendPing = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'ping' }));
    }
  };

  useEffect(() => {
    connect();

    // Send ping every 30 seconds to keep connection alive
    const pingInterval = setInterval(sendPing, 30000);

    return () => {
      clearInterval(pingInterval);
      disconnect();
    };
  }, []);

  return {
    isConnected,
    lastUpdate,
    disconnect,
    reconnect: connect
  };
};
```

### **3. Dashboard Component Integration**

Update your `Dashboard.tsx`:

```typescript
import React, { useState, useEffect } from 'react';
import { smartparkApi } from '../services/smartparkApi';
import { useRealtimeUpdates } from '../hooks/useRealtimeUpdates';

export default function Dashboard() {
  const [slotsData, setSlotsData] = useState(null);
  const [predictions, setPredictions] = useState(null);
  const [loading, setLoading] = useState(true);

  // Real-time updates
  const { isConnected, lastUpdate } = useRealtimeUpdates((update) => {
    // Refresh slots data when update received
    fetchSlotsData();
  });

  const fetchSlotsData = async () => {
    try {
      const data = await smartparkApi.getSlots();
      setSlotsData(data);
    } catch (error) {
      console.error('Error fetching slots:', error);
    }
  };

  const fetchPredictions = async () => {
    try {
      const data = await smartparkApi.getPredictions(30);
      setPredictions(data);
    } catch (error) {
      console.error('Error fetching predictions:', error);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([
        fetchSlotsData(),
        fetchPredictions()
      ]);
      setLoading(false);
    };

    loadData();

    // Refresh predictions every 5 minutes
    const interval = setInterval(fetchPredictions, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="loading">Loading dashboard...</div>;
  }

  const stats = [
    {
      title: 'Total Slots',
      value: slotsData?.summary?.total_slots || 0,
      icon: '🚗',
      trend: { value: 0, isPositive: true }
    },
    {
      title: 'Available Now',
      value: slotsData?.summary?.free_slots || 0,
      icon: '🟢',
      trend: { value: 0, isPositive: true }
    },
    {
      title: 'Occupied',
      value: slotsData?.summary?.occupied_slots || 0,
      icon: '🔴',
      trend: { value: 0, isPositive: false }
    },
    {
      title: 'Occupancy Rate',
      value: `${slotsData?.summary?.occupancy_rate || 0}%`,
      icon: '📊',
      trend: { value: 0, isPositive: false }
    }
  ];

  return (
    <div className="min-h-screen">
      <div className="container mx-auto px-4 py-8 space-y-8">
        
        {/* Connection Status */}
        <div className="flex items-center gap-2 mb-4">
          <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-sm">
            {isConnected ? 'Live Updates Active' : 'Offline Mode'}
          </span>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat, index) => (
            <div key={index} className="glass-card p-6 rounded-xl border border-primary/20">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">{stat.title}</p>
                  <p className="text-2xl font-bold text-primary">{stat.value}</p>
                </div>
                <div className="text-2xl">{stat.icon}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Slots Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {slotsData?.slots?.map((slot) => (
            <div key={slot.id} className={`
              glass-card p-6 rounded-xl border-2 transition-all duration-300
              ${slot.is_occupied 
                ? 'border-red-500/50 bg-red-500/10' 
                : 'border-green-500/50 bg-green-500/10'
              }
            `}>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">{slot.slot_number.toUpperCase()}</h3>
                <div className={`
                  px-3 py-1 rounded-full text-xs font-medium
                  ${slot.is_occupied 
                    ? 'bg-red-500/20 text-red-400' 
                    : 'bg-green-500/20 text-green-400'
                  }
                `}>
                  {slot.is_occupied ? 'OCCUPIED' : 'FREE'}
                </div>
              </div>
              
              <div className="text-sm text-muted-foreground">
                Last updated: {new Date(slot.last_updated).toLocaleTimeString()}
              </div>

              {/* ML Prediction */}
              {predictions?.predictions?.find(p => p.slot_number === slot.slot_number) && (
                <div className="mt-3 pt-3 border-t border-border/50">
                  <div className="text-xs text-muted-foreground">
                    30min forecast: {
                      predictions.predictions
                        .find(p => p.slot_number === slot.slot_number)
                        ?.prediction === 'free' ? '🟢 Likely Free' : '🔴 Likely Occupied'
                    }
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <button 
            onClick={() => window.location.href = '/slots'}
            className="glass-card p-6 rounded-xl border border-primary/20 hover:border-primary/50 transition-all"
          >
            <div className="text-center">
              <div className="text-2xl mb-2">🅿️</div>
              <h3 className="font-semibold">Find Parking</h3>
              <p className="text-sm text-muted-foreground">View available slots</p>
            </div>
          </button>

          <button 
            onClick={() => window.location.href = '/reservations'}
            className="glass-card p-6 rounded-xl border border-primary/20 hover:border-primary/50 transition-all"
          >
            <div className="text-center">
              <div className="text-2xl mb-2">📅</div>
              <h3 className="font-semibold">My Bookings</h3>
              <p className="text-sm text-muted-foreground">Manage reservations</p>
            </div>
          </button>
        </div>

      </div>
    </div>
  );
}
```

### **4. Reservation Component**

Create `src/components/ReservationForm.jsx`:

```javascript
import React, { useState } from 'react';
import { smartparkApi } from '../services/smartparkApi';

export const ReservationForm = ({ slotNumber, onSuccess, onCancel }) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    vehicle: '',
    duration: 2
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const reservation = await smartparkApi.reserveSlot(slotNumber, formData);
      
      // Open gate after successful reservation
      await smartparkApi.openGate();
      
      onSuccess(reservation);
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-card p-6 rounded-xl border border-primary/20">
      <h3 className="text-lg font-semibold mb-4">
        Reserve {slotNumber.toUpperCase()}
      </h3>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-3 rounded mb-4">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Name</label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({...formData, name: e.target.value})}
            className="w-full p-2 rounded border border-border bg-background"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Email</label>
          <input
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({...formData, email: e.target.value})}
            className="w-full p-2 rounded border border-border bg-background"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Phone</label>
          <input
            type="tel"
            value={formData.phone}
            onChange={(e) => setFormData({...formData, phone: e.target.value})}
            className="w-full p-2 rounded border border-border bg-background"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Vehicle Number</label>
          <input
            type="text"
            value={formData.vehicle}
            onChange={(e) => setFormData({...formData, vehicle: e.target.value})}
            className="w-full p-2 rounded border border-border bg-background"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Duration (hours)</label>
          <select
            value={formData.duration}
            onChange={(e) => setFormData({...formData, duration: parseInt(e.target.value)})}
            className="w-full p-2 rounded border border-border bg-background"
          >
            <option value={1}>1 hour - $5</option>
            <option value={2}>2 hours - $10</option>
            <option value={3}>3 hours - $15</option>
            <option value={4}>4 hours - $20</option>
          </select>
        </div>

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 bg-primary text-primary-foreground p-2 rounded hover:bg-primary/90 disabled:opacity-50"
          >
            {loading ? 'Reserving...' : 'Reserve Slot'}
          </button>
          
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 border border-border rounded hover:bg-muted"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};
```

---

## 🔄 **Real-time Data Flow**

### **Complete Event Flow:**

1. **Car Enters Slot** → Arduino detects → Serial Bridge → Backend `/api/update_slots` → WebSocket broadcast → Frontend updates
2. **User Reserves Slot** → Frontend → Backend `/api/reserve_slot` → Gate opens → WebSocket notification
3. **User Exits** → Arduino detects → Serial Bridge → Backend → WebSocket → Frontend updates

### **WebSocket Message Types:**

```javascript
// Slot update from Arduino
{
  "type": "slot_update",
  "data": {
    "slot1": 1,  // 1 = occupied, 0 = free
    "slot2": 0,
    "slot3": 0
  },
  "timestamp": "2024-01-01T12:00:00Z"
}

// Gate event
{
  "type": "gate_event",
  "data": {
    "action": "OPEN",
    "status": "success",
    "triggered_by": "reservation_123"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

## 🎯 **Integration Checklist**

### **✅ Frontend Setup**
- [ ] Install dependencies: `npm install`
- [ ] Create `.env` file with API URLs
- [ ] Add API service (`smartparkApi.js`)
- [ ] Add WebSocket hook (`useRealtimeUpdates.js`)
- [ ] Update Dashboard component
- [ ] Add reservation components

### **✅ Backend Setup**
- [ ] Start backend: `cd backend && python main.py`
- [ ] Verify API: `http://localhost:8000/docs`
- [ ] Test WebSocket: `ws://localhost:8000/ws/realtime`

### **✅ Arduino Setup**
- [ ] Upload Arduino sketch: `arduino/smartpark_3slots.ino`
- [ ] Start serial bridge: `cd serial_bridge && python bridge.py`
- [ ] Test sensor detection

### **✅ Testing**
- [ ] Frontend connects to backend ✓
- [ ] Real-time updates work ✓
- [ ] Reservations create successfully ✓
- [ ] Gate control functions ✓
- [ ] ML predictions display ✓

---

## 🚀 **Environment Variables**

Create `.env` in your React project root:

```bash
# SmartPark Backend Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws/realtime

# Feature Flags
REACT_APP_ENABLE_ML_PREDICTIONS=true
REACT_APP_ENABLE_REALTIME=true
REACT_APP_DEBUG_MODE=false
```

---

## 🎉 **Your SmartPark System is Ready!**

With this integration:

✅ **Real-time Updates** - Your React UI updates instantly when Arduino detects changes  
✅ **Smart Reservations** - Users can book slots and gates open automatically  
✅ **ML Predictions** - AI forecasts show availability trends  
✅ **Professional UI** - Maintains your existing beautiful design  
✅ **Production Ready** - Error handling, reconnection, and monitoring included  

**Your IoT parking system now connects seamlessly from hardware sensors to web interface!** 🚗⚡🎯
