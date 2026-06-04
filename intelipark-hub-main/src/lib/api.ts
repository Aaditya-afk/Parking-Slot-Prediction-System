/**
 * SmartPark API Client
 * Connects React frontend to FastAPI backend
 */

import { ParkingSlot, Reservation, Forecast } from '@/types/parking';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// API Response Types matching backend schemas
export interface SlotStatus {
  id: number;
  slot_label: string;
  status: 'FREE' | 'OCCUPIED' | 'RESERVED';
  last_updated: string;
  has_active_reservation: boolean;
  reservation_end_time?: string;
}

export interface ParkingOverview {
  total_slots: number;
  free_slots: number;
  occupied_slots: number;
  reserved_slots: number;
  slots: SlotStatus[];
}

export interface ReservationCreate {
  slot_id: number;
  user_id: number;
  user_name?: string;
  user_email?: string;
  start_time: string;
  end_time: string;
}

export interface ReservationResponse {
  id: number;
  slot_id: number;
  user_id: number;
  user_name?: string;
  user_email?: string;
  start_time: string;
  end_time: string;
  status: 'active' | 'completed' | 'canceled';
  created_at: string;
}

export interface ForecastResponse {
  slot_id: number;
  slot_label: string;
  horizon_minutes: number;
  probability_free: number;
  confidence: 'high' | 'medium' | 'low';
  generated_at: string;
}

export interface AdminAnalytics {
  total_slots: number;
  current_occupancy_rate: number;
  avg_daily_occupancy: number;
  total_reservations_today: number;
  revenue_today: number;
  peak_hours: number[];
  recent_events: Array<{
    timestamp: string;
    level: string;
    message: string;
    component: string;
  }>;
}

class SmartParkAPI {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API Error [${endpoint}]:`, error);
      throw error;
    }
  }

  // Health & Status
  async getHealth() {
    return this.request<{ status: string; serial_connected: boolean; active_websockets: number }>('/api/health');
  }

  // Slots API
  async getSlots(): Promise<SlotStatus[]> {
    return this.request<SlotStatus[]>('/api/slots');
  }

  async getSlot(slotId: number): Promise<SlotStatus> {
    return this.request<SlotStatus>(`/api/slots/${slotId}`);
  }

  async getParkingOverview(): Promise<ParkingOverview> {
    return this.request<ParkingOverview>('/api/parking-overview');
  }

  async updateSlotStatus(slotLabel: string, status: string) {
    return this.request('/api/slots/update', {
      method: 'POST',
      body: JSON.stringify({ slot_label: slotLabel, status }),
    });
  }

  // Reservations API
  async createReservation(reservation: ReservationCreate): Promise<ReservationResponse> {
    return this.request<ReservationResponse>('/api/reservations', {
      method: 'POST',
      body: JSON.stringify(reservation),
    });
  }

  async getReservations(params?: {
    user_id?: number;
    status?: string;
    limit?: number;
  }): Promise<ReservationResponse[]> {
    const searchParams = new URLSearchParams();
    if (params?.user_id) searchParams.append('user_id', params.user_id.toString());
    if (params?.status) searchParams.append('status', params.status);
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    
    const query = searchParams.toString();
    return this.request<ReservationResponse[]>(`/api/reservations${query ? `?${query}` : ''}`);
  }

  async getReservation(reservationId: number): Promise<ReservationResponse> {
    return this.request<ReservationResponse>(`/api/reservations/${reservationId}`);
  }

  async cancelReservation(reservationId: number) {
    return this.request(`/api/reservations/${reservationId}/cancel`, {
      method: 'PUT',
    });
  }

  async extendReservation(reservationId: number, minutes: number) {
    return this.request(`/api/reservations/${reservationId}/extend`, {
      method: 'PUT',
      body: JSON.stringify({ minutes }),
    });
  }

  // Forecast API
  async getForecast(params?: {
    minutes?: number;
    slot_id?: number;
  }): Promise<ForecastResponse[]> {
    const searchParams = new URLSearchParams();
    if (params?.minutes) searchParams.append('minutes', params.minutes.toString());
    if (params?.slot_id) searchParams.append('slot_id', params.slot_id.toString());
    
    const query = searchParams.toString();
    return this.request<ForecastResponse[]>(`/api/forecast${query ? `?${query}` : ''}`);
  }

  async getForecastSummary(minutes: number = 30) {
    return this.request(`/api/forecast/summary?minutes=${minutes}`);
  }

  async trainMLModel() {
    return this.request('/api/forecast/train', { method: 'POST' });
  }

  async getModelInfo() {
    return this.request('/api/forecast/model-info');
  }

  // Admin API
  async getAnalytics(): Promise<AdminAnalytics> {
    return this.request<AdminAnalytics>('/api/admin/analytics');
  }

  async getSystemLogs(params?: {
    level?: string;
    component?: string;
    limit?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.level) searchParams.append('level', params.level);
    if (params?.component) searchParams.append('component', params.component);
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    
    const query = searchParams.toString();
    return this.request(`/api/admin/logs${query ? `?${query}` : ''}`);
  }

  async getSensorLogs(params?: {
    slot_id?: number;
    hours?: number;
  }) {
    const searchParams = new URLSearchParams();
    if (params?.slot_id) searchParams.append('slot_id', params.slot_id.toString());
    if (params?.hours) searchParams.append('hours', params.hours.toString());
    
    const query = searchParams.toString();
    return this.request(`/api/admin/sensor-logs${query ? `?${query}` : ''}`);
  }

  async getOccupancyTrends(days: number = 7) {
    return this.request(`/api/admin/occupancy-trends?days=${days}`);
  }

  async getRevenueReport(days: number = 30) {
    return this.request(`/api/admin/revenue-report?days=${days}`);
  }

  async getSystemStatus() {
    return this.request('/api/admin/system-status');
  }
}

// WebSocket Manager for real-time updates
export class SmartParkWebSocket {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  constructor(url: string = `ws://localhost:8000/ws/slots`) {
    this.url = url;
  }

  connect(onMessage: (data: any) => void, onError?: (error: Event) => void) {
    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('🔌 WebSocket connected to SmartPark backend');
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage(data);
        } catch (error) {
          console.error('WebSocket message parse error:', error);
        }
      };

      this.ws.onclose = () => {
        console.log('🔌 WebSocket disconnected');
        this.attemptReconnect(onMessage, onError);
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        if (onError) onError(error);
      };

    } catch (error) {
      console.error('WebSocket connection failed:', error);
      if (onError) onError(error as Event);
    }
  }

  private attemptReconnect(onMessage: (data: any) => void, onError?: (error: Event) => void) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`🔄 Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
      
      setTimeout(() => {
        this.connect(onMessage, onError);
      }, this.reconnectDelay * this.reconnectAttempts);
    } else {
      console.error('❌ Max reconnection attempts reached');
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(message: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }
}

// Transform backend data to frontend format
export const transformSlotData = (backendSlot: SlotStatus): ParkingSlot => {
  const statusMap: Record<SlotStatus['status'], ParkingSlot['status']> = {
    'FREE': 'available',
    'OCCUPIED': 'occupied',
    'RESERVED': 'reserved'
  };

  return {
    id: backendSlot.id.toString(),
    lotId: 'lot-1', // Default lot ID
    slotNumber: backendSlot.slot_label,
    status: statusMap[backendSlot.status] || 'available',
    reservedBy: backendSlot.has_active_reservation ? 'user' : undefined,
    reservedUntil: backendSlot.reservation_end_time || undefined,
    lastUpdated: backendSlot.last_updated,
  };
};

export const transformReservationData = (backendReservation: ReservationResponse): Reservation => {
  return {
    id: backendReservation.id.toString(),
    userId: backendReservation.user_id.toString(),
    slotId: backendReservation.slot_id.toString(),
    lotId: 'lot-1', // Default lot ID
    startTime: backendReservation.start_time,
    endTime: backendReservation.end_time,
    qrCode: `QR-${backendReservation.id}`, // Generate QR code ID
    status: backendReservation.status === 'canceled' ? 'cancelled' : backendReservation.status,
    createdAt: backendReservation.created_at,
  };
};

// Export singleton instance
export const api = new SmartParkAPI();
export default api;
