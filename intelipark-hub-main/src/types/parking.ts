export type SlotStatus = 'available' | 'occupied' | 'reserved' | 'maintenance';

export interface ParkingSlot {
  id: string;
  lotId: string;
  slotNumber: string;
  status: SlotStatus;
  reservedBy?: string;
  reservedUntil?: string;
  predictedFreeInMinutes?: number;
  lastUpdated: string;
}

export interface ParkingLot {
  id: string;
  name: string;
  totalSlots: number;
  availableSlots: number;
  location: {
    lat: number;
    lng: number;
    address: string;
  };
}

export interface Reservation {
  id: string;
  userId: string;
  slotId: string;
  lotId: string;
  startTime: string;
  endTime: string;
  qrCode: string;
  status: 'pending' | 'active' | 'completed' | 'cancelled';
  createdAt: string;
}

export interface Feedback {
  id: string;
  userId: string;
  rating: number;
  type: 'complaint' | 'suggestion' | 'general';
  comment: string;
  createdAt: string;
}

export interface SensorReading {
  deviceId: string;
  lotId: string;
  slotId: string;
  timestamp: string;
  occupied: boolean;
  battery?: number;
}

export interface Forecast {
  slotId: string;
  timestamp: string;
  predictedOccupancy: number;
  confidence: number;
}
