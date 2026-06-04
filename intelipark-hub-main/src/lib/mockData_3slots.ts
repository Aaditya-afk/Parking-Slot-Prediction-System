// Updated Mock Data for 3-Slot System
// This will be replaced by real API calls

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

export interface ParkingSlot {
  id: string;
  lotId: string;
  slotNumber: string;
  status: 'available' | 'occupied' | 'reserved';
  lastUpdated: string;
  predictedFreeInMinutes?: number;
  reservedBy?: string;
  reservedUntil?: string;
}

// Check if we should use mock data or real API
const USE_MOCK_DATA = (import.meta as any).env?.VITE_MOCK_DATA === 'true';

export const mockLots: ParkingLot[] = [
  {
    id: 'lot-1',
    name: 'SmartPark IoT Lot',
    totalSlots: 3,  // Changed from 6 to 3
    availableSlots: 2,
    location: {
      lat: 37.7749,
      lng: -122.4194,
      address: 'IoT Smart Parking System - Entry/Exit Detection'
    }
  }
];

// Updated to show exactly 3 slots
export const mockSlots: ParkingSlot[] = [
  { 
    id: '1', 
    lotId: 'lot-1', 
    slotNumber: 'SLOT_1', 
    status: 'available', 
    lastUpdated: new Date().toISOString(), 
    predictedFreeInMinutes: 0 
  },
  { 
    id: '2', 
    lotId: 'lot-1', 
    slotNumber: 'SLOT_2', 
    status: 'occupied', 
    lastUpdated: new Date().toISOString(), 
    predictedFreeInMinutes: 15 
  },
  { 
    id: '3', 
    lotId: 'lot-1', 
    slotNumber: 'SLOT_3', 
    status: 'reserved', 
    reservedBy: 'user-001', 
    reservedUntil: new Date(Date.now() + 30 * 60000).toISOString(), 
    lastUpdated: new Date().toISOString() 
  }
];

// Helper function to get current stats
export const getCurrentStats = () => {
  const totalSlots = 3;
  const availableSlots = mockSlots.filter(slot => slot.status === 'available').length;
  const occupiedSlots = mockSlots.filter(slot => slot.status === 'occupied').length;
  const reservedSlots = mockSlots.filter(slot => slot.status === 'reserved').length;
  const occupancyRate = Math.round((occupiedSlots / totalSlots) * 100);

  return {
    totalSlots,
    availableSlots,
    occupiedSlots,
    reservedSlots,
    occupancyRate
  };
};
