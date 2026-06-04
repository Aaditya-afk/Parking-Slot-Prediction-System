import { ParkingSlot, ParkingLot, Reservation, Feedback } from '@/types/parking';

// Check if we should use mock data or real API
const USE_MOCK_DATA = (import.meta as any).env?.VITE_MOCK_DATA === 'true';

export const mockLots: ParkingLot[] = [
  {
    id: 'lot-1',
    name: 'SmartPark IoT Lot',
    totalSlots: 3,
    availableSlots: 2,
    location: {
      lat: 37.7749,
      lng: -122.4194,
      address: 'IoT Smart Parking System'
    }
  }
];

export const mockSlots: ParkingSlot[] = [
  { id: '1', lotId: 'lot-1', slotNumber: 'SLOT_1', status: 'available', lastUpdated: new Date().toISOString(), predictedFreeInMinutes: 0 },
  { id: '2', lotId: 'lot-1', slotNumber: 'SLOT_2', status: 'occupied', lastUpdated: new Date().toISOString(), predictedFreeInMinutes: 15 },
  { id: '3', lotId: 'lot-1', slotNumber: 'SLOT_3', status: 'reserved', reservedBy: 'user-001', reservedUntil: new Date(Date.now() + 30 * 60000).toISOString(), lastUpdated: new Date().toISOString() },
];

export const mockReservations: Reservation[] = [
  {
    id: 'res-001',
    userId: 'user-001',
    slotId: 'A-03',
    lotId: 'lot-a',
    startTime: new Date().toISOString(),
    endTime: new Date(Date.now() + 30 * 60000).toISOString(),
    qrCode: 'QR-RES-001-ABC123',
    status: 'active',
    createdAt: new Date(Date.now() - 10 * 60000).toISOString()
  },
  {
    id: 'res-002',
    userId: 'user-001',
    slotId: 'A-08',
    lotId: 'lot-a',
    startTime: new Date(Date.now() - 120 * 60000).toISOString(),
    endTime: new Date(Date.now() - 60 * 60000).toISOString(),
    qrCode: 'QR-RES-002-DEF456',
    status: 'completed',
    createdAt: new Date(Date.now() - 180 * 60000).toISOString()
  }
];

export const mockFeedback: Feedback[] = [
  {
    id: 'fb-001',
    userId: 'user-003',
    rating: 5,
    type: 'general',
    comment: 'Great system! Very easy to use and the real-time updates are fantastic.',
    createdAt: new Date(Date.now() - 2 * 3600000).toISOString()
  },
  {
    id: 'fb-002',
    userId: 'user-004',
    rating: 3,
    type: 'complaint',
    comment: 'Slot A-07 sensor seems to be malfunctioning. It shows occupied but the spot is empty.',
    createdAt: new Date(Date.now() - 4 * 3600000).toISOString()
  },
  {
    id: 'fb-003',
    userId: 'user-005',
    rating: 4,
    type: 'suggestion',
    comment: 'Would be nice to have a mobile app with push notifications for when slots become available.',
    createdAt: new Date(Date.now() - 24 * 3600000).toISOString()
  }
];
