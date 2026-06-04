# SmartPark Quick Start - 70+ Slots with Booking Duration

## Current System Status ✅

Your system is **fully implemented** with:
- ✅ 80 parking slots (SLOT_1 to SLOT_80) 
- ✅ Booking modal with duration selection (15 min to 24 hours)
- ✅ Real-time WebSocket updates
- ✅ ML prediction integration
- ✅ Pagination (20 slots per page)
- ✅ Countdown timers on reservations

## How to Start the System

### Option 1: Use Existing Batch File (Recommended)
```bash
# Double-click or run:
run_system.bat
```

This will:
1. Start backend on http://localhost:8000
2. Start frontend on http://localhost:5173
3. Seed 80 slots automatically on first run

### Option 2: Manual Start

**Backend:**
```bash
cd backend
set TOTAL_PARKING_SLOTS=80
python main.py
```

**Frontend (separate terminal):**
```bash
npm run dev
```

## How to Use the Booking System

### 1. View All Slots
- Go to **PARKING** page
- You'll see 20 slots per page (use Prev/Next buttons)
- Green = Available, Red = Occupied, Amber = Reserved

### 2. Make a Booking
1. Click any **green (available) slot**
2. **Booking Modal** opens with:
   - **Booking Type**: 
     - Immediate (starts now)
     - Scheduled (pick start time)
     - Hourly (1-24 hours)
     - Daily (full day)
   - **Duration**: Enter minutes (60 = 1 hour, 120 = 2 hours, etc.)
   - **Start/End Time**: Auto-calculated or manual
3. Click **"Check Availability"** (optional - uses ML)
4. Click **"Confirm Booking"**
5. Slot turns **amber** and shows countdown

### 3. Manage Bookings
- Go to **BOOKINGS** page
- See all active reservations with countdown timers
- **Extend +30m**: Add 30 minutes to booking
- **Cancel**: Release the slot

## Database Reset (If Needed)

If you only see 3 slots instead of 80:

```bash
# Stop backend (Ctrl+C)
# Delete old database
del backend\smartpark.db
# Restart backend - fresh DB with 80 slots
cd backend
set TOTAL_PARKING_SLOTS=80
python main.py
```

## API Endpoints

- `GET /api/get_slots` - Returns all 80 slots
- `POST /api/booking/create` - Create booking with duration
- `GET /api/booking/reservations` - List all bookings
- `PUT /api/booking/{id}/modify` - Extend/shorten booking
- `PUT /api/booking/{id}/cancel` - Cancel booking
- `POST /api/booking/availability` - Check with ML validation

## Troubleshooting

### "No slots showing"
- Restart backend to trigger seeding
- Check http://localhost:8000/api/get_slots in browser
- Should return JSON with 80 slots

### "Booking modal not opening"
- Check browser console for errors
- Ensure frontend is running on port 5173
- Clear browser cache and reload

### "Only 3 slots visible"
- Delete `backend/smartpark.db`
- Set `TOTAL_PARKING_SLOTS=80` environment variable
- Restart backend

## System Architecture

```
Frontend (React + TypeScript)
  ↓ HTTP/WebSocket
Backend (FastAPI + Python)
  ↓ SQLAlchemy
Database (SQLite)
  - parking_slots table (80 slots)
  - reservations table (bookings with duration)
```

## Next Steps

1. **Start the system** using `run_system.bat`
2. **Open** http://localhost:5173
3. **Click** PARKING → Click any green slot
4. **Select duration** (e.g., 60 minutes)
5. **Confirm booking**
6. **View** in BOOKINGS page with countdown

---

**All code is complete and ready to use!** 🎉
