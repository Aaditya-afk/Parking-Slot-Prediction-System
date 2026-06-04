# Fix Dashboard to Show 80 Slots

## Problem
- Dashboard shows: 3 total slots, 2 available
- Parking page shows: 80 slots correctly
- They need to be synchronized

## Solution

### Find the Dashboard Component
Look for the file that contains "TOTAL SLOTS" and "AVAILABLE NOW" text.
Likely locations:
- `src/pages/Dashboard.tsx`
- `src/pages/Home.tsx`
- `src/components/Dashboard.tsx`

### Fix the Data Source

The dashboard is currently using the wrong API endpoint or mock data.

**Change this:**
```typescript
// Old - using legacy 3-slot endpoint
const overview = await smartparkApi.getParkingOverview();
```

**To this:**
```typescript
// New - using 80-slot endpoint
const slotsData = await smartparkApi.getSlots();
const overview = {
  total_slots: slotsData.summary.totalSlots,
  free_slots: slotsData.summary.availableSlots,
  occupied_slots: slotsData.summary.occupiedSlots,
  reserved_slots: slotsData.summary.reservedSlots,
  occupancy_rate: slotsData.summary.occupancyRate,
  slots: slotsData.slots
};
```

### Alternative: Use useRealtimeParking Hook

If the dashboard already uses `useRealtimeParking()`, it should work automatically.

**Check if this exists:**
```typescript
const { parkingData } = useRealtimeParking();

// Then use:
parkingData.totalSlots      // Should be 80
parkingData.availableSlots  // Should match parking page
```

## Quick Test

1. Open browser DevTools (F12)
2. Go to Network tab
3. Refresh dashboard
4. Look for API calls - should call `/api/get_slots` not `/api/parking_overview`

## Files to Check

1. `src/pages/Dashboard.tsx` - Main dashboard
2. `src/hooks/useRealtimeParking.ts` - Already fixed to use 80 slots
3. `src/services/smartparkAPI.ts` - API methods

The `useRealtimeParking` hook already fetches 80 slots correctly, so the dashboard just needs to use it!
