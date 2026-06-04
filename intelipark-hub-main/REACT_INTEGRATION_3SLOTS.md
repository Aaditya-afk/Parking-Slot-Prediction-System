# 🌐 React Frontend Integration - SmartPark 3-Slot System

Complete integration guide to connect your existing React frontend with the SmartPark Entry/Exit backend system.

## 🎯 **System Overview**

Your React frontend will display **exactly 3 slots** and connect to:
- **Backend API**: `http://localhost:8000` (FastAPI with entry/exit detection)
- **WebSocket**: `ws://localhost:8000/ws/realtime` (Real-time updates)
- **Arduino**: 2 IR sensors (entry/exit) + 1 servo gate (transparent to frontend)

---

## 📊 **Updated API Endpoints for Your Frontend**

### **Core Endpoints (Replace existing mock data)**

| Endpoint | Method | Purpose | Your Component |
|----------|--------|---------|----------------|
| `/api/get_slots` | GET | Get 3 slot statuses | Dashboard, Slots page |
| `/api/parking_overview` | GET | Overview stats | Dashboard summary |
| `/api/open_gate` | POST | Open parking gate | Entry/Exit buttons |
| `/api/close_gate` | POST | Close parking gate | Manual control |
| `/api/reserve_slot` | POST | Reserve specific slot | Booking form |
| `/api/release_slot` | POST | Release reservation | My Bookings |
| `/api/ai/insights` | GET | AI recommendations | Dashboard insights |
| `/ws/realtime` | WebSocket | Live updates | All components |

---

## 🔧 **Frontend Code Integration**

### **1. Updated API Service (`src/services/smartparkApi.js`)**

```javascript
// SmartPark API Service - 3 Slot Entry/Exit System
class SmartParkAPI {
  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    this.wsURL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws/realtime';
  }

  // Get all 3 parking slots (replaces your mock data)
  async getSlots() {
    try {
      const response = await fetch(`${this.baseURL}/api/get_slots`);
      const data = await response.json();
      
      if (data.success) {
        return {
          slots: data.data.slots,           // Exactly 3 slots
          summary: data.data.summary        // total_slots: 3, free_slots, occupied_slots, etc.
        };
      }
      throw new Error('Failed to fetch slots');
    } catch (error) {
      console.error('Error fetching slots:', error);
      throw error;
    }
  }

  // Get parking overview (for dashboard stats)
  async getParkingOverview() {
    try {
      const response = await fetch(`${this.baseURL}/api/parking_overview`);
      const data = await response.json();
      
      if (data.success) {
        return {
          total_slots: data.data.total_slots,        // Always 3
          free_slots: data.data.free_slots,
          occupied_slots: data.data.occupied_slots,
          reserved_slots: data.data.reserved_slots,
          occupancy_rate: data.data.occupancy_rate,
          slots: data.data.slots,
          recent_activity: data.data.recent_activity
        };
      }
      throw new Error('Failed to fetch overview');
    } catch (error) {
      console.error('Error fetching overview:', error);
      throw error;
    }
  }

  // Reserve a specific slot (slot_id: 1, 2, or 3)
  async reserveSlot(slotId, userDetails) {
    try {
      const response = await fetch(`${this.baseURL}/api/reserve_slot`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          slot_id: slotId,                    // 1, 2, or 3
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

  // Release a slot reservation
  async releaseSlot(reservationId, slotId = null) {
    try {
      const payload = reservationId 
        ? { reservation_id: reservationId }
        : { slot_id: slotId };

      const response = await fetch(`${this.baseURL}/api/release_slot`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
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

  // Manual gate control
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
  async getReservations(userEmail = null) {
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

  // AI Insights and Predictions
  async getAIInsights() {
    try {
      const response = await fetch(`${this.baseURL}/api/ai/insights`);
      const data = await response.json();
      
      if (data.success) {
        return data.data;
      }
      throw new Error('Failed to fetch AI insights');
    } catch (error) {
      console.error('Error fetching AI insights:', error);
      throw error;
    }
  }

  async getOccupancyPredictions(hoursAhead = 2) {
    try {
      const response = await fetch(`${this.baseURL}/api/ai/predict_occupancy?hours_ahead=${hoursAhead}`);
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

  async getSmartRecommendations() {
    try {
      const response = await fetch(`${this.baseURL}/api/ai/recommendations`);
      const data = await response.json();
      
      if (data.success) {
        return data.data;
      }
      throw new Error('Failed to fetch recommendations');
    } catch (error) {
      console.error('Error fetching recommendations:', error);
      throw error;
    }
  }
}

export const smartparkApi = new SmartParkAPI();
```

### **2. Real-time WebSocket Hook (`src/hooks/useRealtimeUpdates.js`)**

```javascript
import { useState, useEffect, useRef } from 'react';

export const useRealtimeUpdates = (onSlotUpdate, onCarEvent) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [lastCarEvent, setLastCarEvent] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const connect = () => {
    try {
      const wsURL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws/realtime';
      wsRef.current = new WebSocket(wsURL);

      wsRef.current.onopen = () => {
        console.log('🔌 Connected to SmartPark Entry/Exit System');
        setIsConnected(true);
        
        // Send subscription message
        wsRef.current.send(JSON.stringify({
          type: 'subscribe',
          channels: ['slot_updates', 'car_events', 'gate_events']
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
          } else if (data.type === 'car_event') {
            console.log('🚗 Received car event:', data);
            setLastCarEvent(data);
            if (onCarEvent) {
              onCarEvent(data);
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
    lastCarEvent,
    disconnect,
    reconnect: connect
  };
};
```

### **3. Updated Dashboard Component**

```typescript
import React, { useState, useEffect } from 'react';
import { smartparkApi } from '../services/smartparkApi';
import { useRealtimeUpdates } from '../hooks/useRealtimeUpdates';

export default function Dashboard() {
  const [parkingData, setParkingData] = useState(null);
  const [aiInsights, setAiInsights] = useState(null);
  const [loading, setLoading] = useState(true);

  // Real-time updates
  const { isConnected, lastUpdate, lastCarEvent } = useRealtimeUpdates(
    (update) => {
      // Refresh parking data when update received
      fetchParkingData();
    },
    (carEvent) => {
      // Show toast notification for car events
      showCarEventNotification(carEvent);
    }
  );

  const fetchParkingData = async () => {
    try {
      const data = await smartparkApi.getParkingOverview();
      setParkingData(data);
    } catch (error) {
      console.error('Error fetching parking data:', error);
    }
  };

  const fetchAIInsights = async () => {
    try {
      const insights = await smartparkApi.getAIInsights();
      setAiInsights(insights);
    } catch (error) {
      console.error('Error fetching AI insights:', error);
      // AI insights are optional, don't show error to user
    }
  };

  const showCarEventNotification = (carEvent) => {
    const message = carEvent.event_type === 'car_entered' 
      ? '🚗 Car entered parking lot' 
      : '🚗 Car exited parking lot';
    
    // Use your existing toast/notification system
    // toast.success(message);
    console.log(message);
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([
        fetchParkingData(),
        fetchAIInsights()
      ]);
      setLoading(false);
    };

    loadData();

    // Refresh AI insights every 10 minutes
    const interval = setInterval(fetchAIInsights, 10 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="loading">Loading dashboard...</div>;
  }

  // Stats for your existing StatsCard components
  const stats = [
    {
      title: 'Total Slots',
      value: parkingData?.total_slots || 3,  // Always 3 for this system
      icon: '🚗',
      trend: { value: 0, isPositive: true }
    },
    {
      title: 'Available Now',
      value: parkingData?.free_slots || 0,
      icon: '🟢',
      trend: { value: 0, isPositive: true }
    },
    {
      title: 'Occupied',
      value: parkingData?.occupied_slots || 0,
      icon: '🔴',
      trend: { value: 0, isPositive: false }
    },
    {
      title: 'Occupancy Rate',
      value: `${parkingData?.occupancy_rate || 0}%`,
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
          <span className="text-xs text-muted-foreground ml-2">
            Entry/Exit Detection System
          </span>
        </div>

        {/* Stats Grid - Use your existing StatsCard component */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat, index) => (
            <StatsCard key={index} {...stat} />
          ))}
        </div>

        {/* Slots Grid - Exactly 3 slots */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {parkingData?.slots?.map((slot) => (
            <div key={slot.id} className={`
              glass-card p-6 rounded-xl border-2 transition-all duration-300
              ${slot.status === 'occupied' 
                ? 'border-red-500/50 bg-red-500/10' 
                : slot.status === 'reserved'
                ? 'border-yellow-500/50 bg-yellow-500/10'
                : 'border-green-500/50 bg-green-500/10'
              }
            `}>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">{slot.slot_number}</h3>
                <div className={`
                  px-3 py-1 rounded-full text-xs font-medium
                  ${slot.status === 'occupied' 
                    ? 'bg-red-500/20 text-red-400' 
                    : slot.status === 'reserved'
                    ? 'bg-yellow-500/20 text-yellow-400'
                    : 'bg-green-500/20 text-green-400'
                  }
                `}>
                  {slot.status.toUpperCase()}
                </div>
              </div>
              
              <div className="text-sm text-muted-foreground">
                Last updated: {new Date(slot.last_updated).toLocaleTimeString()}
              </div>

              {/* Reserve button for free slots */}
              {slot.status === 'free' && (
                <button 
                  onClick={() => handleReserveSlot(slot.id)}
                  className="mt-3 w-full bg-primary text-primary-foreground py-2 px-4 rounded hover:bg-primary/90"
                >
                  Reserve Slot
                </button>
              )}
            </div>
          ))}
        </div>

        {/* AI Insights Section */}
        {aiInsights && (
          <div className="glass-card p-6 rounded-xl border border-primary/20">
            <h3 className="text-lg font-semibold mb-4">🤖 AI Insights</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium mb-2">Current Status</h4>
                <p className="text-sm text-muted-foreground">
                  {aiInsights.current_status?.occupied_slots || 0} of 3 slots occupied 
                  ({aiInsights.current_status?.occupancy_rate || 0}%)
                </p>
              </div>
              
              <div>
                <h4 className="font-medium mb-2">Recommendation</h4>
                <p className="text-sm text-muted-foreground">
                  {aiInsights.recommendations?.message || 'No specific recommendations'}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
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

          <button 
            onClick={handleGateControl}
            className="glass-card p-6 rounded-xl border border-primary/20 hover:border-primary/50 transition-all"
          >
            <div className="text-center">
              <div className="text-2xl mb-2">🚪</div>
              <h3 className="font-semibold">Gate Control</h3>
              <p className="text-sm text-muted-foreground">Open/Close gate</p>
            </div>
          </button>
        </div>

      </div>
    </div>
  );

  // Helper functions
  async function handleReserveSlot(slotId) {
    // Navigate to reservation form or open modal
    window.location.href = `/reserve?slot=${slotId}`;
  }

  async function handleGateControl() {
    try {
      await smartparkApi.openGate();
      // Show success message
      console.log('Gate opened successfully');
    } catch (error) {
      console.error('Failed to open gate:', error);
    }
  }
}
```

---

## 🔄 **Real-time Event Flow**

### **Complete Data Flow:**

1. **Car Enters** → Arduino IR_ENTRY → Serial Bridge → Backend `/api/update_event` → Slot assigned → WebSocket broadcast → Frontend updates
2. **Car Exits** → Arduino IR_EXIT → Serial Bridge → Backend → Slot freed → WebSocket broadcast → Frontend updates
3. **User Reserves** → Frontend → Backend `/api/reserve_slot` → Database updated → WebSocket notification
4. **Gate Control** → Frontend → Backend `/api/open_gate` → Serial Bridge → Arduino servo

### **WebSocket Message Types:**

```javascript
// Slot update (when car enters/exits)
{
  "type": "slot_update",
  "data": {
    "slots": [...],  // Updated 3 slots
    "summary": {...} // New stats
  },
  "timestamp": "2024-01-01T12:00:00Z"
}

// Car event (entry/exit detection)
{
  "type": "car_event",
  "event_type": "car_entered", // or "car_exited"
  "data": {
    "assigned_slot_id": 2,
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

---

## 🎯 **Environment Configuration**

Create `.env` in your React project root:

```bash
# SmartPark Backend Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws/realtime

# Feature Flags
REACT_APP_ENABLE_AI_INSIGHTS=true
REACT_APP_ENABLE_REALTIME=true
REACT_APP_TOTAL_SLOTS=3
```

---

## 🎉 **Perfect Alignment with Your Project**

### **✅ Exact 3-Slot Display**
- Your frontend will show exactly 3 slots (SLOT_1, SLOT_2, SLOT_3)
- Stats will reflect 3 total slots maximum
- All calculations based on 3-slot system

### **✅ Your Existing Components Enhanced**
- `StatsCard` → Now shows real occupancy data
- `SlotCard` → Displays live slot status from Arduino
- Dashboard → Real-time updates from entry/exit detection
- Booking system → Works with actual slot assignment

### **✅ Real-time Integration**
- Car enters → Slot automatically assigned → UI updates instantly
- Car exits → Slot automatically freed → UI updates instantly
- WebSocket notifications for all changes
- AI insights for smart recommendations

**Your beautiful React UI now connects seamlessly to real Arduino hardware with intelligent slot management!** 🚗⚡🎯
