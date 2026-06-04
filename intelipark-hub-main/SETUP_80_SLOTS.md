# Setup 80 Parking Slots

## Current Issues Fixed

1. ✅ **Backend timer fields** - Added `expected_free_time`, `timer_remaining` to `/api/get_slots`
2. ✅ **Frontend timer stability** - Modal now locks to a single target timestamp (no reset)
3. ✅ **Database connection** - Fixed Supabase URL format with `postgresql+psycopg2` and SSL
4. ✅ **Events router mounted** - `/api/get_slots` endpoint is now available
5. ⚠️ **Slot count** - Need to seed 80 slots in Supabase

## Steps to Complete Setup

### 1. Update your `.env` file

Create or update `backend/.env` with:

```env
# Database Configuration
DATABASE_URL=postgresql+psycopg2://postgres:Ambika2214@db.pxzaujuzmypigvvqnjvd.supabase.co:5432/postgres?sslmode=require

# Total slots
TOTAL_PARKING_SLOTS=80

# Arduino Serial Configuration
ARDUINO_PORT=COM3
ARDUINO_BAUDRATE=9600
ARDUINO_TIMEOUT=1.0

# Simulator Mode
SIMULATOR_MODE=false

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS Settings
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080

# Logging
LOG_LEVEL=INFO
LOG_FILE=smartpark.log

# ML Model Settings
ML_TRAINING_DAYS=30
ML_MIN_SAMPLES=100
ML_RETRAIN_INTERVAL_HOURS=24
```

### 2. Seed 80 slots in Supabase

Run the seeding script:

```powershell
cd backend
python seed_80_slots.py
```

This will:
- Delete any existing slots
- Create 80 new slots (SLOT_1 to SLOT_80)
- All slots start as "free" status

### 3. Restart the backend

```powershell
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Verify the setup

1. **Check API response:**
   - Visit: http://localhost:8000/api/get_slots
   - Should show 80 slots with timer fields

2. **Check dashboard:**
   - Should show "Total Slots: 80"
   - Available, Occupied, Reserved counts

3. **Test booking:**
   - Click "Check Availability" - should work now
   - Book a slot - should succeed
   - Click occupied slot - timer should show and not reset

### 5. Test timer functionality

1. Book a slot for 60 minutes
2. Click the occupied slot card
3. Modal shows "Available in: 59m 59s..." counting down
4. Close and reopen - timer continues from same point (no reset)
5. When timer hits zero - slot auto-turns green

## Troubleshooting

### "Failed to fetch" when checking availability

- Check backend logs for errors
- Ensure `psycopg2-binary` is installed: `pip install psycopg2-binary`
- Verify Supabase connection string is correct

### Only 3 slots showing

- Run `seed_80_slots.py` to populate database
- Check `TOTAL_PARKING_SLOTS=80` in `.env`
- Restart backend after seeding

### Timer resets to 20 minutes

- Hard refresh frontend (Ctrl+Shift+R)
- Check `/api/get_slots` returns `expected_free_time` for occupied slots
- Verify backend is using the updated code

### Database connection errors

- Ensure Supabase URL format: `postgresql+psycopg2://...?sslmode=require`
- Check password is correct
- Verify network access to Supabase

## Files Modified

- `backend/database.py` - Fixed URL, changed default to 80 slots
- `backend/database_entry_exit.py` - Fixed URL, changed default to 80 slots
- `backend/routes/events.py` - Added timer fields to `/api/get_slots`
- `backend/routes/bookings_adv.py` - Added error handling
- `backend/main.py` - Mounted events router
- `src/services/smartparkAPI.ts` - Forward timer fields from backend
- `src/components/SlotTimerModal.tsx` - Lock to single target timestamp
- `src/pages/Slots.tsx` - Pass original slot object (no re-derivation)

## Summary

All code changes are complete. You just need to:
1. Update `.env` with the config above
2. Run `python seed_80_slots.py` to populate 80 slots
3. Restart backend
4. Hard refresh frontend

The timer will then work properly and show 80 slots everywhere.
