# 🔧 Frontend Update Instructions - Fix 6 Slots → 3 Slots

## 🎯 **Problem Solved**
Your frontend shows **6 total slots** but hardware only has **3 slots**. Here's how to fix it and enable full hardware control.

---

## 📝 **Step-by-Step Updates**

### **Step 1: Update Environment Variables**
Create/update `.env` file in your React project root:

```bash
# SmartPark 3-Slot System Configuration
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws/realtime
VITE_TOTAL_SLOTS=3
VITE_MOCK_DATA=false
VITE_ENABLE_REALTIME=true
```

### **Step 2: Replace Mock Data**
Update your `src/lib/mockData.ts` file:

```typescript
// Replace existing mockData.ts content with:
import { mockLots, mockSlots, getCurrentStats } from './mockData_3slots';

export { mockLots, mockSlots, getCurrentStats };

// Or better yet, replace mock data usage with real API calls
```

### **Step 3: Update Your Dashboard Component**
Replace the data fetching in your Dashboard component:

```typescript
// OLD (using mock data):
import { mockSlots, mockLots } from '@/lib/mockData';

// NEW (using real API):
import { useRealtimeParking } from '@/hooks/useRealtimeParking';

export default function Dashboard() {
  // Replace mock data with real-time hook
  const {
    parkingData,
    isConnected,
    loading,
    error,
    openGate,
    closeGate,
    reserveSlot,
    refresh
  } = useRealtimeParking();

  if (loading) {
    return <div className="loading">Loading parking data...</div>;
  }

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  // Use real data instead of mock data
  const stats = [
    {
      title: 'Total Slots',
      value: parkingData?.totalSlots || 3,  // Now shows 3 instead of 6
      icon: '🚗',
      trend: { value: 0, isPositive: true }
    },
    {
      title: 'Available Now',
      value: parkingData?.availableSlots || 0,
      icon: '🟢',
      trend: { value: 0, isPositive: true }
    },
    {
      title: 'Occupied',
      value: parkingData?.occupiedSlots || 0,
      icon: '🔴',
      trend: { value: 0, isPositive: false }
    },
    {
      title: 'Occupancy Rate',
      value: `${parkingData?.occupancyRate || 0}%`,
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
            {isConnected ? 'Live Hardware Connected' : 'Offline Mode'}
          </span>
        </div>

        {/* Stats Grid - Now shows correct 3-slot data */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat, index) => (
            <StatsCard key={index} {...stat} />
          ))}
        </div>

        {/* Hardware Control Buttons */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <button 
            onClick={openGate}
            className="bg-green-500 hover:bg-green-600 text-white p-4 rounded-lg transition-colors"
          >
            🚪 Open Gate
          </button>
          
          <button 
            onClick={closeGate}
            className="bg-red-500 hover:bg-red-600 text-white p-4 rounded-lg transition-colors"
          >
            🚪 Close Gate
          </button>
        </div>

        {/* Slots Display - Shows exactly 3 slots */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {parkingData?.slots?.map((slot) => (
            <SlotCard 
              key={slot.id} 
              slot={slot} 
              onReserve={(slotId) => reserveSlot(slotId, userDetails)}
            />
          ))}
        </div>

      </div>
    </div>
  );
}
```

### **Step 4: Add Hardware Control Components**

Create a new component for hardware control:

```typescript
// src/components/HardwareControl.tsx
import React from 'react';
import { useRealtimeParking } from '@/hooks/useRealtimeParking';

export const HardwareControl: React.FC = () => {
  const { openGate, closeGate, isConnected } = useRealtimeParking();

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold mb-4">🔧 Hardware Control</h3>
      
      <div className="flex items-center gap-2 mb-4">
        <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
        <span className="text-sm">
          {isConnected ? 'Arduino Connected' : 'Arduino Disconnected'}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <button 
          onClick={openGate}
          disabled={!isConnected}
          className="bg-green-500 hover:bg-green-600 disabled:bg-gray-300 text-white p-3 rounded-lg transition-colors"
        >
          🚪 Open Gate
        </button>
        
        <button 
          onClick={closeGate}
          disabled={!isConnected}
          className="bg-red-500 hover:bg-red-600 disabled:bg-gray-300 text-white p-3 rounded-lg transition-colors"
        >
          🚪 Close Gate
        </button>
      </div>

      <div className="mt-4 text-sm text-gray-600">
        <p>• Gate opens automatically when cars enter/exit</p>
        <p>• Manual control available above</p>
        <p>• Real-time status via WebSocket</p>
      </div>
    </div>
  );
};
```

### **Step 5: Update Package.json Scripts**
Add these scripts to your `package.json`:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "start:backend": "cd backend && python main_entry_exit.py",
    "start:bridge": "cd serial_bridge && python event_bridge.py",
    "start:full": "concurrently \"npm run start:backend\" \"npm run start:bridge\" \"npm run dev\"",
    "check:api": "curl http://localhost:8000/api/health"
  }
}
```

---

## 🔄 **Complete Integration Flow**

### **Data Flow:**
```
🚗 Car Enters → Arduino IR_ENTRY → Serial Bridge → Backend → WebSocket → Your Frontend (3 slots)
🚗 Car Exits  → Arduino IR_EXIT  → Serial Bridge → Backend → WebSocket → Your Frontend (updates)
🚪 Gate Control → Your Frontend → Backend API → Serial Bridge → Arduino Servo
```

### **Real-time Updates:**
```
Arduino Event → Backend Processing → WebSocket Broadcast → Frontend Auto-Update
```

---

## 🧪 **Testing Your Updates**

### **1. Start the Complete System:**
```bash
# Terminal 1: Backend
cd backend && python main_entry_exit.py

# Terminal 2: Serial Bridge  
cd serial_bridge && python event_bridge.py

# Terminal 3: Frontend
npm run dev
```

### **2. Verify 3-Slot Display:**
- Open http://localhost:5173
- Dashboard should show "Total Slots: 3" (not 6)
- Stats should reflect 3-slot system

### **3. Test Hardware Control:**
- Click "Open Gate" button → Should send command to Arduino
- Click "Close Gate" button → Should send command to Arduino
- Check browser console for WebSocket messages

### **4. Test Real-time Updates:**
- Trigger Arduino IR sensors
- Watch frontend update automatically
- Check WebSocket connection status

---

## 🎯 **Expected Results**

After these updates, your frontend will:

✅ **Show exactly 3 slots** (matching your hardware)  
✅ **Display real occupancy data** from Arduino sensors  
✅ **Control hardware** via web interface (gate open/close)  
✅ **Update in real-time** when cars enter/exit  
✅ **Show connection status** to Arduino  
✅ **Provide manual overrides** for all hardware functions  

---

## 🔧 **Hardware Control Features**

Your web application now controls:

1. **Gate Operations**: Open/close servo motor
2. **Slot Monitoring**: Real-time entry/exit detection  
3. **Reservation Management**: Assign/release slots
4. **Status Monitoring**: Arduino connection health
5. **AI Insights**: Smart recommendations based on real data

---

## 🚨 **Troubleshooting**

### **If still showing 6 slots:**
1. Clear browser cache and reload
2. Check `.env` file has `VITE_TOTAL_SLOTS=3`
3. Verify API endpoint returns 3 slots: `curl http://localhost:8000/api/get_slots`

### **If hardware control not working:**
1. Check Arduino connection in Serial Monitor
2. Verify serial bridge is running
3. Test API directly: `curl -X POST http://localhost:8000/api/open_gate`

### **If real-time updates not working:**
1. Check WebSocket connection in browser console
2. Verify backend WebSocket endpoint
3. Test with: `wscat -c ws://localhost:8000/ws/realtime`

---

## 🎉 **Success!**

Your frontend now perfectly matches your 3-slot hardware and provides complete control over:
- **Real-time slot monitoring**
- **Gate control via web interface**  
- **Automatic updates from Arduino sensors**
- **AI-powered insights and recommendations**

**Your web application is now the master control center for your IoT parking system!** 🚗⚡🎯
