/**
 * SmartPark React Hooks
 * Custom hooks for integrating with the SmartPark backend
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect, useState, useCallback } from 'react';
import { toast } from 'sonner';
import { 
  api, 
  SmartParkWebSocket, 
  transformSlotData, 
  transformReservationData,
  type ReservationCreate,
  type SlotStatus,
  type ParkingOverview,
  type ForecastResponse,
  type AdminAnalytics
} from '@/lib/api';
import type { ParkingSlot, Reservation } from '@/types/parking';

// Query Keys
export const QUERY_KEYS = {
  slots: ['slots'],
  slot: (id: number) => ['slots', id],
  parkingOverview: ['parking-overview'],
  reservations: (params?: any) => ['reservations', params],
  reservation: (id: number) => ['reservations', id],
  forecast: (params?: any) => ['forecast', params],
  analytics: ['admin', 'analytics'],
  systemLogs: (params?: any) => ['admin', 'logs', params],
  systemStatus: ['admin', 'system-status'],
  health: ['health'],
} as const;

// Slots Hooks
export const useSlots = () => {
  return useQuery({
    queryKey: QUERY_KEYS.slots,
    queryFn: async () => {
      const slots = await api.getSlots();
      return slots.map(transformSlotData);
    },
    refetchInterval: 30000, // Refetch every 30 seconds
    staleTime: 10000, // Consider data stale after 10 seconds
  });
};

export const useSlot = (slotId: number) => {
  return useQuery({
    queryKey: QUERY_KEYS.slot(slotId),
    queryFn: async () => {
      const slot = await api.getSlot(slotId);
      return transformSlotData(slot);
    },
    enabled: !!slotId,
  });
};

export const useParkingOverview = () => {
  return useQuery({
    queryKey: QUERY_KEYS.parkingOverview,
    queryFn: () => api.getParkingOverview(),
    refetchInterval: 15000, // Refetch every 15 seconds for overview
    staleTime: 5000,
  });
};

// Real-time WebSocket Hook
export const useRealtimeSlots = () => {
  const queryClient = useQueryClient();
  const [isConnected, setIsConnected] = useState(false);
  const [ws] = useState(() => new SmartParkWebSocket());

  useEffect(() => {
    const handleMessage = (data: any) => {
      if (data.type === 'slot_update') {
        // Update individual slot cache
        queryClient.setQueryData(
          QUERY_KEYS.slot(data.slot_id),
          (oldData: ParkingSlot | undefined) => {
            if (!oldData) return oldData;
            return {
              ...oldData,
              status: data.status.toLowerCase(),
              lastUpdated: data.timestamp,
            };
          }
        );

        // Invalidate related queries to trigger refetch
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.slots });
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.parkingOverview });

        // Show toast notification
        const statusEmoji = data.status === 'OCCUPIED' ? '🚗' : '🟢';
        toast(`${statusEmoji} ${data.slot_label} is now ${data.status.toLowerCase()}`, {
          duration: 3000,
        });
      }
    };

    const handleError = (error: Event) => {
      setIsConnected(false);
      toast.error('Lost connection to parking system', {
        description: 'Attempting to reconnect...',
      });
    };

    ws.connect(handleMessage, handleError);
    setIsConnected(true);

    return () => {
      ws.disconnect();
      setIsConnected(false);
    };
  }, [queryClient, ws]);

  return { isConnected };
};

// Reservations Hooks
export const useReservations = (params?: { user_id?: number; status?: string; limit?: number }) => {
  return useQuery({
    queryKey: QUERY_KEYS.reservations(params),
    queryFn: async () => {
      const reservations = await api.getReservations(params);
      return reservations.map(transformReservationData);
    },
  });
};

export const useCreateReservation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (reservation: ReservationCreate) => api.createReservation(reservation),
    onSuccess: (data) => {
      // Invalidate and refetch reservations
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.reservations() });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.slots });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.parkingOverview });

      toast.success('🎉 Reservation created successfully!', {
        description: `Slot ${data.slot_id} reserved until ${new Date(data.end_time).toLocaleTimeString()}`,
      });
    },
    onError: (error: Error) => {
      toast.error('Failed to create reservation', {
        description: error.message,
      });
    },
  });
};

export const useCancelReservation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (reservationId: number) => api.cancelReservation(reservationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.reservations() });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.slots });
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.parkingOverview });

      toast.success('Reservation cancelled successfully');
    },
    onError: (error: Error) => {
      toast.error('Failed to cancel reservation', {
        description: error.message,
      });
    },
  });
};

export const useExtendReservation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ reservationId, minutes }: { reservationId: number; minutes: number }) =>
      api.extendReservation(reservationId, minutes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.reservations() });
      toast.success('Reservation extended successfully');
    },
    onError: (error: Error) => {
      toast.error('Failed to extend reservation', {
        description: error.message,
      });
    },
  });
};

// Forecast Hooks
export const useForecast = (params?: { minutes?: number; slot_id?: number }) => {
  return useQuery({
    queryKey: QUERY_KEYS.forecast(params),
    queryFn: () => api.getForecast(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 10 * 60 * 1000, // Refetch every 10 minutes
  });
};

export const useForecastSummary = (minutes: number = 30) => {
  return useQuery({
    queryKey: ['forecast-summary', minutes],
    queryFn: () => api.getForecastSummary(minutes),
    staleTime: 5 * 60 * 1000,
  });
};

export const useTrainMLModel = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => api.trainMLModel(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['forecast'] });
      queryClient.invalidateQueries({ queryKey: ['model-info'] });
      toast.success('🤖 ML model training completed!');
    },
    onError: (error: Error) => {
      toast.error('ML model training failed', {
        description: error.message,
      });
    },
  });
};

// Admin Hooks
export const useAnalytics = () => {
  return useQuery({
    queryKey: QUERY_KEYS.analytics,
    queryFn: () => api.getAnalytics(),
    refetchInterval: 60000, // Refetch every minute
  });
};

export const useSystemLogs = (params?: { level?: string; component?: string; limit?: number }) => {
  return useQuery({
    queryKey: QUERY_KEYS.systemLogs(params),
    queryFn: () => api.getSystemLogs(params),
    refetchInterval: 30000,
  });
};

export const useSystemStatus = () => {
  return useQuery({
    queryKey: QUERY_KEYS.systemStatus,
    queryFn: () => api.getSystemStatus(),
    refetchInterval: 15000,
  });
};

export const useOccupancyTrends = (days: number = 7) => {
  return useQuery({
    queryKey: ['occupancy-trends', days],
    queryFn: () => api.getOccupancyTrends(days),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
};

export const useRevenueReport = (days: number = 30) => {
  return useQuery({
    queryKey: ['revenue-report', days],
    queryFn: () => api.getRevenueReport(days),
    staleTime: 30 * 60 * 1000, // 30 minutes
  });
};

// Health Check Hook
export const useHealth = () => {
  return useQuery({
    queryKey: QUERY_KEYS.health,
    queryFn: () => api.getHealth(),
    refetchInterval: 30000,
    retry: 3,
  });
};

// Custom hook for slot predictions with enhanced UI data
export const useSlotPredictions = () => {
  const { data: forecast } = useForecast({ minutes: 30 });
  const { data: slots } = useSlots();

  const predictionsWithSlots = useCallback(() => {
    if (!forecast || !slots) return [];

    return forecast.map(prediction => {
      const slot = slots.find(s => s.id === prediction.slot_id.toString());
      return {
        ...prediction,
        slot,
        predictedStatus: prediction.probability_free > 0.7 ? 'likely_free' : 
                        prediction.probability_free < 0.3 ? 'likely_occupied' : 'uncertain',
        confidenceColor: prediction.confidence === 'high' ? 'text-green-500' :
                        prediction.confidence === 'medium' ? 'text-yellow-500' : 'text-red-500',
      };
    });
  }, [forecast, slots]);

  return {
    predictions: predictionsWithSlots(),
    isLoading: !forecast || !slots,
  };
};

// Hook for dashboard stats with real-time updates
export const useDashboardStats = () => {
  const { data: overview, isLoading } = useParkingOverview();
  const { data: analytics } = useAnalytics();
  const { isConnected } = useRealtimeSlots();

  const stats = useCallback(() => {
    if (!overview) return null;

    const occupancyRate = overview.total_slots > 0 
      ? Math.round(((overview.total_slots - overview.free_slots) / overview.total_slots) * 100)
      : 0;

    return {
      totalSlots: overview.total_slots,
      availableSlots: overview.free_slots,
      occupiedSlots: overview.occupied_slots,
      reservedSlots: overview.reserved_slots,
      occupancyRate,
      revenueToday: analytics?.revenue_today || 0,
      reservationsToday: analytics?.total_reservations_today || 0,
      isRealTimeConnected: isConnected,
    };
  }, [overview, analytics, isConnected]);

  return {
    stats: stats(),
    isLoading,
    isConnected,
  };
};
