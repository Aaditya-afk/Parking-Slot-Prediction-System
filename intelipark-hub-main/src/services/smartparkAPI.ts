// SmartPark API Service - Real Hardware Integration
// This replaces mock data with actual backend API calls

interface SlotData {
  id: number;
  slot_number: string;
  status: 'free' | 'occupied' | 'reserved';
  assigned_at?: string;
  last_updated: string;
}

interface ParkingOverview {
  total_slots: number;
  free_slots: number;
  occupied_slots: number;
  reserved_slots: number;
  occupancy_rate: number;
  slots: SlotData[];
  recent_activity?: any[];
}

interface ReservationData {
  slot_id: number;
  user_name: string;
  user_email: string;
  user_phone?: string;
  vehicle_number?: string;
  duration_hours?: number;
}

interface AIInsights {
  current_status: {
    occupied_slots: number;
    free_slots: number;
    occupancy_rate: number;
    is_peak_time: boolean;
  };
  recommendations: {
    message: string;
    best_time_next_4h?: any;
  };
  predictions?: any[];
}

class SmartParkAPI {
  private baseURL: string;
  private wsURL: string;

  constructor() {
    this.baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    this.wsURL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws/realtime';
  }

  // ---------- Admin & Feedback APIs ----------
  async getAdminSummary(): Promise<any> {
    const res = await fetch(`${this.baseURL}/api/admin/summary`);
    return res.json();
  }

  async getFeedbackStats(): Promise<any> {
    const res = await fetch(`${this.baseURL}/api/feedback/stats`);
    return res.json();
  }

  async getFeedbackList(params?: { status?: string; category?: string; limit?: number }): Promise<any> {
    const usp = new URLSearchParams();
    if (params?.status) usp.set('status', params.status);
    if (params?.category) usp.set('category', params.category);
    if (params?.limit) usp.set('limit', String(params.limit));
    const qs = usp.toString();
    const res = await fetch(`${this.baseURL}/api/feedback/list${qs ? `?${qs}` : ''}`);
    return res.json();
  }

  async submitFeedback(payload: {
    user_name: string;
    user_email: string;
    rating: number; // 1..5
    category: 'complaint' | 'suggestion' | 'praise' | 'bug_report' | 'general';
    message: string;
    user_id?: string;
  }): Promise<any> {
    const res = await fetch(`${this.baseURL}/api/feedback/submit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return res.json();
  }

  async respondFeedback(id: number, payload: { admin_response: string; reviewed_by: string }): Promise<any> {
    const res = await fetch(`${this.baseURL}/api/feedback/${id}/respond`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return res.json();
  }

  async getRecentReservations(limit: number = 20): Promise<any> {
    const res = await fetch(`${this.baseURL}/api/admin/recent-reservations?limit=${limit}`);
    return res.json();
  }

  // Get all parking slots (N slots, unified entry/exit model)
  async getSlots(): Promise<{ slots: any[]; summary: any }> {
    try {
      // Use unified slots endpoint
      const response = await fetch(`${this.baseURL}/api/slots`);
      const data = await response.json();
      // /api/slots returns a plain list (response_model=List[SlotStatus])
      if (Array.isArray(data)) {
        const IST_OFFSET_MINUTES = 330; // +05:30
        const nowIstMs = Date.now() + IST_OFFSET_MINUTES * 60000 - new Date().getTimezoneOffset() * 60000;

        const transformedSlots = data.map((slot: any) => {
          // Backend sends: id, slot_label, status (UPPERCASE), last_updated, has_active_reservation, reservation_end_time
          const status = this.mapStatus((slot.status || '').toLowerCase());
          const expectedFree: string | undefined = slot.reservation_end_time || undefined;

          // Compute remaining minutes from end time (clamped to >= 0)
          let predictedFreeInMinutes = 0;
          if (expectedFree) {
            const endMs = new Date(expectedFree).getTime();
            const remainingMs = endMs - (Date.now());
            if (!Number.isNaN(remainingMs)) {
              predictedFreeInMinutes = Math.max(0, Math.ceil(remainingMs / 60000));
            }
          }

          return {
            id: String(slot.id),
            lotId: 'lot-1',
            slotNumber: slot.slot_label,
            status,
            lastUpdated: slot.last_updated,
            expected_free_time: expectedFree,
            reservedUntil: status === 'reserved' ? expectedFree : undefined,
            predictedFreeInMinutes,
          };
        });

        // We don't have summary here; compute minimal summary for UI counters if needed
        const totalSlots = transformedSlots.length;
        const availableSlots = transformedSlots.filter(s => s.status === 'available').length;
        const occupiedSlots = transformedSlots.filter(s => s.status === 'occupied').length;
        const reservedSlots = transformedSlots.filter(s => s.status === 'reserved').length;
        const occupancyRate = totalSlots ? Math.round((occupiedSlots / totalSlots) * 1000) / 10 : 0;

        return {
          slots: transformedSlots,
          summary: { totalSlots, availableSlots, occupiedSlots, reservedSlots, occupancyRate },
        };
      }
      throw new Error('Failed to fetch slots (unexpected response)');
    } catch (error) {
      console.error('Error fetching slots:', error);
      // Fallback to mock data if API fails
      return this.getMockData();
    }
  }

  // Get parking overview for dashboard
  async getParkingOverview(): Promise<ParkingOverview> {
    try {
      const response = await fetch(`${this.baseURL}/api/parking_overview`);
      const data = await response.json();

      if (data.success) {
        return {
          total_slots: data.data.total_slots,
          free_slots: data.data.free_slots,
          occupied_slots: data.data.occupied_slots,
          reserved_slots: data.data.reserved_slots,
          occupancy_rate: data.data.occupancy_rate,
          slots: data.data.slots || [],
          recent_activity: data.data.recent_activity || [],
        } as ParkingOverview;
      }
      throw new Error('Failed to fetch overview');
    } catch (error) {
      console.error('Error fetching overview:', error);
      // Return fallback data
      return {
        total_slots: 3,
        free_slots: 2,
        occupied_slots: 1,
        reserved_slots: 0,
        occupancy_rate: 33.3,
        slots: [],
      } as ParkingOverview;
    }
  }

  // Reserve a specific slot (legacy 3-slot API)
  async reserveSlot(slotId: number, userDetails: ReservationData): Promise<any> {
    try {
      const response = await fetch(`${this.baseURL}/api/reserve_slot`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          slot_id: slotId,
          user_name: userDetails.user_name,
          user_email: userDetails.user_email,
          user_phone: userDetails.user_phone,
          vehicle_number: userDetails.vehicle_number,
          duration_hours: userDetails.duration_hours || 2,
        }),
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

  // Release a slot reservation (legacy)
  async releaseSlot(reservationId?: number, slotId?: number): Promise<any> {
    try {
      const payload = reservationId ? { reservation_id: reservationId } : { slot_id: slotId };

      const response = await fetch(`${this.baseURL}/api/release_slot`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
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
  async openGate(): Promise<any> {
    try {
      const response = await fetch(`${this.baseURL}/api/open_gate`, {
        method: 'POST',
      });

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error opening gate:', error);
      throw error;
    }
  }

  async closeGate(): Promise<any> {
    try {
      const response = await fetch(`${this.baseURL}/api/close_gate`, {
        method: 'POST',
      });

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error closing gate:', error);
      throw error;
    }
  }

  // Legacy reservations list (kept for compatibility)
  async getReservations(userEmail?: string): Promise<any[]> {
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
      return [];
    }
  }

  // AI Insights and Predictions
  async getAIInsights(): Promise<AIInsights | null> {
    try {
      const response = await fetch(`${this.baseURL}/api/ai/insights`);
      const data = await response.json();

      if (data.success) {
        return data.data as AIInsights;
      }
      return null;
    } catch (error) {
      console.error('Error fetching AI insights:', error);
      return null;
    }
  }

  async getOccupancyPredictions(hoursAhead: number = 2): Promise<any> {
    try {
      const response = await fetch(`${this.baseURL}/api/ai/predict_occupancy?hours_ahead=${hoursAhead}`);
      const data = await response.json();

      if (data.success) {
        return data.data;
      }
      return null;
    } catch (error) {
      console.error('Error fetching predictions:', error);
      return null;
    }
  }

  async getSmartRecommendations(): Promise<any> {
    try {
      const response = await fetch(`${this.baseURL}/api/ai/recommendations`);
      const data = await response.json();

      if (data.success) {
        return data.data;
      }
      return null;
    } catch (error) {
      console.error('Error fetching recommendations:', error);
      return null;
    }
  }

  // WebSocket connection for real-time updates
  connectWebSocket(onMessage: (data: any) => void): WebSocket | null {
    try {
      const ws = new WebSocket(this.wsURL);

      ws.onopen = () => {
        console.log(' Connected to SmartPark real-time updates');
        // Subscribe to updates
        ws.send(
          JSON.stringify({
            type: 'subscribe',
            channels: ['slot_updates', 'car_events', 'gate_events'],
          }),
        );
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        console.log(' WebSocket disconnected');
        // Auto-reconnect after 3 seconds
        setTimeout(() => {
          this.connectWebSocket(onMessage);
        }, 3000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      return ws;
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      return null;
    }
  }

  // ---------- Advanced booking APIs ----------
  async checkAvailability(
    slotNumber: string,
    startISO: string,
    endISO: string,
  ): Promise<{ available: boolean; ml?: any; reason?: string } | null> {
    try {
      const res = await fetch(`${this.baseURL}/api/booking/availability`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slot_number: slotNumber, start_time: startISO, end_time: endISO }),
      });
      const data = await res.json();
      if (res.ok) return { available: !!data.available, ml: data.ml, reason: data.reason };
      return null;
    } catch (error) {
      console.error('Error checking availability', error);
      return null;
    }
  }

  async createAdvancedBooking(payload: {
    slot_number: string;
    booking_type: 'immediate' | 'scheduled' | 'hourly' | 'daily';
    start_time?: string;
    end_time?: string;
    duration_minutes?: number;
    user_name: string;
    user_email: string;
    user_phone?: string;
    vehicle_number?: string;
  }): Promise<any> {
    console.log('🚀 Creating booking with payload:', payload);
    const res = await fetch(`${this.baseURL}/api/booking/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    console.log('📥 Backend response:', { status: res.status, ok: res.ok, data });
    
    if (!res.ok) {
      const errorMsg = data?.detail || data?.message || `HTTP ${res.status}: Failed to create booking`;
      console.error('❌ Booking failed:', errorMsg);
      throw new Error(errorMsg);
    }
    
    if (data?.success === false) {
      const errorMsg = data?.message || 'Booking failed';
      console.error('❌ Booking failed:', errorMsg);
      throw new Error(errorMsg);
    }
    
    console.log('✅ Booking created successfully:', data);
    return data?.data || data;
  }

  async getPredictions(minutesAhead: number = 15): Promise<any> {
    try {
      const res = await fetch(`${this.baseURL}/api/booking/predictions?minutes_ahead=${minutesAhead}`);
      const data = await res.json();
      if (data?.success) return data.data;
      return null;
    } catch (error) {
      console.error('Error getting predictions', error);
      return null;
    }
  }

  async getAdvancedReservations(limit: number = 100): Promise<any[]> {
    try {
      const res = await fetch(`${this.baseURL}/api/booking/reservations?limit=${limit}`);
      const data = await res.json();
      if (data?.success) return data.data;
      return [];
    } catch (e) {
      console.error('getAdvancedReservations failed', e);
      return [];
    }
  }

  async modifyAdvancedReservation(id: number, payload: { start_time?: string; end_time?: string }): Promise<boolean> {
    const res = await fetch(`${this.baseURL}/api/booking/${id}/modify`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return res.ok;
  }

  async cancelAdvancedReservation(id: number): Promise<boolean> {
    const res = await fetch(`${this.baseURL}/api/booking/${id}/cancel`, { method: 'PUT' });
    return res.ok;
  }

  // Helper methods
  private mapStatus(backendStatus: string): 'available' | 'occupied' | 'reserved' {
    const s = (backendStatus || '').toLowerCase().trim();
    console.log(`🔄 mapStatus: "${backendStatus}" -> "${s}"`);
    switch (s) {
      case 'free':
      case 'available':
        return 'available';
      case 'occupied':
        return 'occupied';
      case 'reserved':
        return 'reserved';
      case 'maintenance':
        return 'available'; // Treat maintenance as available for now
      default:
        // Fallback: treat unknown as available to avoid blocking UI
        console.warn(`⚠️ Unknown status "${backendStatus}" (normalized: "${s}"), defaulting to 'available'`);
        return 'available';
    }
  }

  private getMockData() {
    // Fallback mock data for 3 slots
    return {
      slots: [
        { id: '1', lotId: 'lot-1', slotNumber: 'SLOT_1', status: 'available', lastUpdated: new Date().toISOString() },
        { id: '2', lotId: 'lot-1', slotNumber: 'SLOT_2', status: 'occupied', lastUpdated: new Date().toISOString() },
        { id: '3', lotId: 'lot-1', slotNumber: 'SLOT_3', status: 'available', lastUpdated: new Date().toISOString() },
      ],
      summary: {
        totalSlots: 3,
        availableSlots: 2,
        occupiedSlots: 1,
        reservedSlots: 0,
        occupancyRate: 33.3,
      },
    };
  }

  // Health check
  async checkHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseURL}/api/health`);
      return response.ok;
    } catch (error) {
      return false;
    }
  }
}

export const smartparkApi = new SmartParkAPI();
export default smartparkApi;
