// Real-time parking updates hook
import { useState, useEffect, useRef } from 'react';
import { smartparkApi } from '../services/smartparkAPI';

interface ParkingData {
  totalSlots: number;
  availableSlots: number;
  occupiedSlots: number;
  reservedSlots: number;
  occupancyRate: number;
  slots: any[];
}

interface RealtimeUpdate {
  type: string;
  data: any;
  timestamp: string;
}

export const useRealtimeParking = () => {
  const [parkingData, setParkingData] = useState<ParkingData | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<RealtimeUpdate | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch initial parking data
  const fetchParkingData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const slotsData = await smartparkApi.getSlots();
      
      setParkingData({
        totalSlots: slotsData.summary.totalSlots,
        availableSlots: slotsData.summary.availableSlots,
        occupiedSlots: slotsData.summary.occupiedSlots,
        reservedSlots: slotsData.summary.reservedSlots,
        occupancyRate: slotsData.summary.occupancyRate,
        slots: slotsData.slots
      });
      
    } catch (err) {
      console.error('Error fetching parking data:', err);
      setError('Failed to fetch parking data');
      
      // Fallback to mock data
      setParkingData({
        totalSlots: 80,
        availableSlots: 60,
        occupiedSlots: 15,
        reservedSlots: 5,
        occupancyRate: 25,
        slots: []
      });
    } finally {
      setLoading(false);
    }
  };

  // Handle real-time updates
  const handleRealtimeUpdate = (data: any) => {
    setLastUpdate({
      type: data.type,
      data: data.data,
      timestamp: data.timestamp
    });

    if (data.type === 'slot_update' || data.type === 'car_event' || data.type === 'booking_update') {
      // Refresh parking data when slots change
      fetchParkingData();
    }

    // Merge ML prediction updates into local slot state to enrich UI
    if (data.type === 'ml_prediction_update' && data.data?.predictions && Array.isArray(data.data.predictions)) {
      setParkingData(prev => {
        if (!prev || !prev.slots) return prev;

        // Build map slotId -> prediction
        const preds = data.data.predictions as Array<any>;
        const predMap: Record<string, any> = {};
        preds.forEach((p) => {
          // Normalize like 'slot1' -> 'slot_1'
          if (p.slot_number) {
            const key = String(p.slot_number).toLowerCase();
            predMap[key] = p;
          }
        });

        // Create enriched slots array without mutating original
        const enriched = (prev.slots || []).map((s: any) => {
          const norm = String(s.slotNumber || s.slot_number || s.id || '').toLowerCase().replace('slot_', 'slot');
          const p = predMap[norm];
          if (!p) return s;

          // If predicted free in 15 minutes, surface hint; also attach probability for UI badges
          const predictedFreeInMinutes = p.prediction === 'free' ? (p.minutes_ahead || data.data.horizon_minutes || 15) : 0;
          return {
            ...s,
            predictedFreeInMinutes,
            predictedFreeProbability: typeof p.probability_free === 'number' ? p.probability_free : undefined,
            predictionConfidence: p.confidence,
          };
        });

        return {
          ...prev,
          slots: enriched,
        };
      });
    }
  };

  // Connect to WebSocket
  const connectWebSocket = () => {
    try {
      wsRef.current = smartparkApi.connectWebSocket(handleRealtimeUpdate);
      
      if (wsRef.current) {
        wsRef.current.onopen = () => {
          setIsConnected(true);
          setError(null);
          console.log('✅ Real-time updates connected');
        };

        wsRef.current.onclose = () => {
          setIsConnected(false);
          console.log('🔌 Real-time updates disconnected');
          
          // Auto-reconnect after 3 seconds
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('🔄 Attempting to reconnect...');
            connectWebSocket();
          }, 3000);
        };

        wsRef.current.onerror = (error) => {
          console.error('WebSocket error:', error);
          setIsConnected(false);
          setError('Real-time connection failed');
        };
      }
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      setError('Failed to establish real-time connection');
    }
  };

  // Disconnect WebSocket
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

  // Manual refresh
  const refresh = () => {
    fetchParkingData();
  };

  // Gate control functions
  const openGate = async () => {
    try {
      await smartparkApi.openGate();
      console.log('✅ Gate opened successfully');
      return true;
    } catch (error) {
      console.error('❌ Failed to open gate:', error);
      setError('Failed to open gate');
      return false;
    }
  };

  const closeGate = async () => {
    try {
      await smartparkApi.closeGate();
      console.log('✅ Gate closed successfully');
      return true;
    } catch (error) {
      console.error('❌ Failed to close gate:', error);
      setError('Failed to close gate');
      return false;
    }
  };

  // Reserve slot function
  const reserveSlot = async (slotId: number, userDetails: any) => {
    try {
      const result = await smartparkApi.reserveSlot(slotId, userDetails);
      await fetchParkingData(); // Refresh data
      return result;
    } catch (error) {
      console.error('❌ Failed to reserve slot:', error);
      setError('Failed to reserve slot');
      throw error;
    }
  };

  // Release slot function
  const releaseSlot = async (reservationId?: number, slotId?: number) => {
    try {
      const result = await smartparkApi.releaseSlot(reservationId, slotId);
      await fetchParkingData(); // Refresh data
      return result;
    } catch (error) {
      console.error('❌ Failed to release slot:', error);
      setError('Failed to release slot');
      throw error;
    }
  };

  // Initialize on mount
  useEffect(() => {
    fetchParkingData();
    connectWebSocket();

    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, []);

  // Periodic refresh (every 30 seconds as backup)
  useEffect(() => {
    const interval = setInterval(() => {
      if (!isConnected) {
        fetchParkingData();
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [isConnected]);

  return {
    // Data
    parkingData,
    lastUpdate,
    
    // Connection status
    isConnected,
    loading,
    error,
    
    // Actions
    refresh,
    openGate,
    closeGate,
    reserveSlot,
    releaseSlot,
    
    // Connection control
    disconnect,
    reconnect: connectWebSocket
  };
};
