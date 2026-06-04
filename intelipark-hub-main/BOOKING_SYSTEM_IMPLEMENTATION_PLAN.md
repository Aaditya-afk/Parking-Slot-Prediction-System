# Smart Parking System - Advanced Booking Implementation Plan

## Executive Summary
Extend the existing immediate booking system to support **scheduled**, **hourly**, and **daily** bookings with proper reservation states, conflict detection, and real-time synchronization across all clients.

---

## 1. Data Model Changes

### 1.1 Enhanced Reservation/Booking Schema
```python
# backend/models/parking.py - Update Reservation model

class Reservation(Base):
    __tablename__ = "reservations"
    
    id = Column(Integer, primary_key=True, index=True)
    slot_id = Column(Integer, ForeignKey("parking_slots.id"), nullable=False)
    
    # Booking metadata
    booking_type = Column(String(20), nullable=False)  # 'immediate', 'scheduled', 'hourly', 'daily'
    booking_reference = Column(String(50), unique=True, index=True)  # e.g., "BK-20250108-001"
    
    # User information
    user_id = Column(String(100), index=True)
    user_name = Column(String(100), nullable=False)
    user_email = Column(String(100), nullable=False)
    user_phone = Column(String(20))
    vehicle_number = Column(String(20))
    
    # Time window
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False, index=True)
    duration_minutes = Column(Integer)  # Calculated field for quick queries
    
    # Status tracking
    status = Column(String(20), default="reserved", index=True)
    # Status values: 'reserved', 'active', 'completed', 'cancelled', 'no_show'
    
    # Pricing (optional)
    price_per_hour = Column(Float)
    total_price = Column(Float)
    payment_status = Column(String(20))  # 'pending', 'paid', 'refunded'
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    cancelled_at = Column(DateTime, nullable=True)
    
    # Grace period and no-show tracking
    grace_period_minutes = Column(Integer, default=15)
    no_show_checked_at = Column(DateTime, nullable=True)
    
    # Relationships
    slot = relationship("ParkingSlot", back_populates="reservations")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_slot_time_status', 'slot_id', 'start_time', 'end_time', 'status'),
        Index('idx_status_times', 'status', 'start_time', 'end_time'),
    )
```

### 1.2 Slot Status Enhancement
```python
# ParkingSlot status values:
# - 'free': No reservation or occupation
# - 'reserved': Has active/future reservation (yellow)
# - 'occupied': Vehicle physically present (red)
# - 'maintenance': Under maintenance (gray)

# Note: A slot can be 'occupied' even with a 'reserved' booking if vehicle arrived
```

---

## 2. Backend API Endpoints

### 2.1 New/Updated Booking Endpoints

#### **POST /api/booking/create** (Enhanced)
```python
# Request body:
{
    "slot_number": "SLOT_10",
    "booking_type": "scheduled",  # immediate | scheduled | hourly | daily
    "start_time": "2025-01-08T14:00:00Z",  # ISO 8601 (required for scheduled/hourly/daily)
    "end_time": "2025-01-08T16:00:00Z",    # Optional, calculated if duration provided
    "duration_minutes": 120,                # Alternative to end_time
    "user_name": "John Doe",
    "user_email": "john@example.com",
    "user_phone": "+1234567890",
    "vehicle_number": "ABC-123"
}

# Response:
{
    "success": true,
    "data": {
        "reservation_id": 42,
        "booking_reference": "BK-20250108-042",
        "slot_number": "SLOT_10",
        "status": "reserved",
        "start_time": "2025-01-08T14:00:00Z",
        "end_time": "2025-01-08T16:00:00Z",
        "total_price": 25.00
    },
    "message": "Booking confirmed. Slot reserved from 2:00 PM to 4:00 PM"
}
```

#### **POST /api/booking/check-availability** (Enhanced)
```python
# Request:
{
    "slot_number": "SLOT_10",
    "start_time": "2025-01-08T14:00:00Z",
    "end_time": "2025-01-08T16:00:00Z"
}

# Response (available):
{
    "available": true,
    "slot_number": "SLOT_10",
    "suggested_slots": []  # Empty if requested slot is available
}

# Response (conflict):
{
    "available": false,
    "slot_number": "SLOT_10",
    "conflict_reason": "Slot already reserved from 2:00 PM to 5:00 PM",
    "conflicting_bookings": [
        {
            "booking_reference": "BK-20250108-035",
            "start_time": "2025-01-08T14:00:00Z",
            "end_time": "2025-01-08T17:00:00Z"
        }
    ],
    "suggested_slots": [
        {
            "slot_number": "SLOT_11",
            "available": true,
            "distance_meters": 15
        },
        {
            "slot_number": "SLOT_9",
            "available": true,
            "distance_meters": 20
        }
    ]
}
```

#### **PUT /api/booking/{reservation_id}/cancel**
```python
# Response:
{
    "success": true,
    "message": "Booking cancelled successfully",
    "refund_amount": 25.00,
    "refund_status": "processing"
}
```

#### **PUT /api/booking/{reservation_id}/modify**
```python
# Request:
{
    "start_time": "2025-01-08T15:00:00Z",  # New start time
    "end_time": "2025-01-08T17:00:00Z"     # New end time
}

# Response:
{
    "success": true,
    "message": "Booking modified successfully",
    "price_adjustment": 5.00
}
```

#### **GET /api/booking/my-bookings**
```python
# Query params: ?user_email=john@example.com&status=reserved,active

# Response:
{
    "success": true,
    "data": [
        {
            "reservation_id": 42,
            "booking_reference": "BK-20250108-042",
            "slot_number": "SLOT_10",
            "booking_type": "scheduled",
            "status": "reserved",
            "start_time": "2025-01-08T14:00:00Z",
            "end_time": "2025-01-08T16:00:00Z",
            "countdown_to_start": 7200,  # seconds
            "can_cancel": true,
            "can_modify": true
        }
    ]
}
```

---

## 3. Conflict Detection & Validation

### 3.1 Overlap Detection Logic
```python
# backend/services/booking_validator.py

from sqlalchemy import and_, or_
from datetime import datetime, timedelta

class BookingValidator:
    
    @staticmethod
    def check_slot_availability(
        db: Session,
        slot_id: int,
        start_time: datetime,
        end_time: datetime,
        exclude_reservation_id: int = None
    ) -> tuple[bool, str, list]:
        """
        Check if slot is available for the given time window.
        Returns: (is_available, reason, conflicting_bookings)
        """
        
        # Query for overlapping reservations
        query = db.query(Reservation).filter(
            Reservation.slot_id == slot_id,
            Reservation.status.in_(['reserved', 'active']),
            or_(
                # New booking starts during existing booking
                and_(
                    Reservation.start_time <= start_time,
                    Reservation.end_time > start_time
                ),
                # New booking ends during existing booking
                and_(
                    Reservation.start_time < end_time,
                    Reservation.end_time >= end_time
                ),
                # New booking completely contains existing booking
                and_(
                    Reservation.start_time >= start_time,
                    Reservation.end_time <= end_time
                )
            )
        )
        
        if exclude_reservation_id:
            query = query.filter(Reservation.id != exclude_reservation_id)
        
        conflicts = query.all()
        
        if conflicts:
            conflict_details = [
                {
                    "booking_reference": c.booking_reference,
                    "start_time": c.start_time.isoformat(),
                    "end_time": c.end_time.isoformat()
                }
                for c in conflicts
            ]
            reason = f"Slot already booked from {conflicts[0].start_time.strftime('%I:%M %p')} to {conflicts[0].end_time.strftime('%I:%M %p')}"
            return False, reason, conflict_details
        
        return True, "", []
    
    @staticmethod
    def validate_booking_times(
        booking_type: str,
        start_time: datetime,
        end_time: datetime = None,
        duration_minutes: int = None
    ) -> tuple[bool, str, datetime, datetime]:
        """
        Validate and calculate booking times based on type.
        Returns: (is_valid, error_message, final_start_time, final_end_time)
        """
        
        now = datetime.utcnow()
        
        if booking_type == "immediate":
            start_time = now
            if duration_minutes:
                end_time = start_time + timedelta(minutes=duration_minutes)
            elif not end_time:
                return False, "Duration or end_time required for immediate booking", None, None
        
        elif booking_type == "scheduled":
            if start_time <= now:
                return False, "Scheduled booking must be in the future", None, None
            if not end_time and not duration_minutes:
                return False, "End time or duration required for scheduled booking", None, None
            if duration_minutes:
                end_time = start_time + timedelta(minutes=duration_minutes)
        
        elif booking_type == "hourly":
            if duration_minutes and duration_minutes < 60:
                return False, "Hourly booking must be at least 60 minutes", None, None
            if duration_minutes:
                end_time = start_time + timedelta(minutes=duration_minutes)
        
        elif booking_type == "daily":
            if duration_minutes and duration_minutes < 1440:  # 24 hours
                return False, "Daily booking must be at least 24 hours", None, None
            if duration_minutes:
                end_time = start_time + timedelta(minutes=duration_minutes)
        
        else:
            return False, f"Invalid booking type: {booking_type}", None, None
        
        # Validate end time is after start time
        if end_time <= start_time:
            return False, "End time must be after start time", None, None
        
        # Validate maximum booking duration (e.g., 7 days)
        max_duration = timedelta(days=7)
        if end_time - start_time > max_duration:
            return False, "Booking duration cannot exceed 7 days", None, None
        
        return True, "", start_time, end_time
    
    @staticmethod
    def suggest_alternative_slots(
        db: Session,
        start_time: datetime,
        end_time: datetime,
        exclude_slot_id: int = None,
        max_suggestions: int = 3
    ) -> list:
        """Find alternative available slots for the same time window."""
        
        all_slots = db.query(ParkingSlot).filter(
            ParkingSlot.status != 'maintenance'
        ).all()
        
        suggestions = []
        for slot in all_slots:
            if exclude_slot_id and slot.id == exclude_slot_id:
                continue
            
            is_available, _, _ = BookingValidator.check_slot_availability(
                db, slot.id, start_time, end_time
            )
            
            if is_available:
                suggestions.append({
                    "slot_number": slot.slot_number,
                    "slot_id": slot.id,
                    "available": True
                })
            
            if len(suggestions) >= max_suggestions:
                break
        
        return suggestions
```

### 3.2 Race Condition Prevention
```python
# Use database row-level locking for concurrent booking attempts

from sqlalchemy import select
from sqlalchemy.orm import Session

def create_booking_with_lock(db: Session, booking_data: dict):
    """Create booking with row-level lock to prevent race conditions."""
    
    try:
        # Start transaction
        with db.begin_nested():
            # Lock the slot row for update
            slot = db.query(ParkingSlot).filter(
                ParkingSlot.slot_number == booking_data['slot_number']
            ).with_for_update().first()
            
            if not slot:
                raise ValueError("Slot not found")
            
            # Check availability within the locked transaction
            is_available, reason, conflicts = BookingValidator.check_slot_availability(
                db, slot.id, booking_data['start_time'], booking_data['end_time']
            )
            
            if not is_available:
                raise ValueError(reason)
            
            # Create reservation
            reservation = Reservation(
                slot_id=slot.id,
                booking_type=booking_data['booking_type'],
                booking_reference=generate_booking_reference(),
                user_name=booking_data['user_name'],
                user_email=booking_data['user_email'],
                start_time=booking_data['start_time'],
                end_time=booking_data['end_time'],
                duration_minutes=int((booking_data['end_time'] - booking_data['start_time']).total_seconds() / 60),
                status='reserved'
            )
            
            db.add(reservation)
            
            # Update slot status to 'reserved' if booking starts soon
            if booking_data['start_time'] <= datetime.utcnow() + timedelta(minutes=30):
                slot.status = 'reserved'
                slot.last_updated = datetime.utcnow()
            
            db.flush()  # Flush to get reservation ID
            
        db.commit()
        return reservation
        
    except Exception as e:
        db.rollback()
        raise e
```

---

## 4. Background Scheduler Implementation

### 4.1 Scheduler Setup
```python
# backend/scheduler/booking_scheduler.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
import asyncio

scheduler = AsyncIOScheduler()

async def process_reservation_transitions():
    """
    Run every minute to:
    1. Activate reservations that have reached start_time
    2. Complete active bookings that have passed end_time
    3. Mark no-shows for reservations past grace period
    """
    
    db = SessionLocal()
    now = datetime.utcnow()
    
    try:
        # 1. Activate reservations (reserved -> active)
        reservations_to_activate = db.query(Reservation).filter(
            Reservation.status == 'reserved',
            Reservation.start_time <= now
        ).all()
        
        for res in reservations_to_activate:
            res.status = 'active'
            slot = db.query(ParkingSlot).filter(ParkingSlot.id == res.slot_id).first()
            if slot:
                # Keep slot as 'reserved' until vehicle physically arrives
                # Sensor will change it to 'occupied'
                slot.status = 'reserved'
                slot.last_updated = now
            
            # Broadcast activation
            await broadcast_booking_update(res, 'activated')
        
        # 2. Complete active bookings (active -> completed)
        bookings_to_complete = db.query(Reservation).filter(
            Reservation.status == 'active',
            Reservation.end_time <= now
        ).all()
        
        for res in bookings_to_complete:
            res.status = 'completed'
            slot = db.query(ParkingSlot).filter(ParkingSlot.id == res.slot_id).first()
            if slot and slot.status != 'occupied':  # Don't override if vehicle still present
                slot.status = 'free'
                slot.assigned_at = None
                slot.last_updated = now
            
            # Broadcast completion
            await broadcast_booking_update(res, 'completed')
        
        # 3. Check for no-shows (reserved past grace period without activation)
        grace_cutoff = now - timedelta(minutes=15)  # 15-minute grace period
        no_shows = db.query(Reservation).filter(
            Reservation.status == 'reserved',
            Reservation.start_time < grace_cutoff,
            Reservation.no_show_checked_at == None
        ).all()
        
        for res in no_shows:
            # Check if vehicle sensor detected arrival
            slot = db.query(ParkingSlot).filter(ParkingSlot.id == res.slot_id).first()
            if slot and slot.status == 'occupied':
                # Vehicle arrived, activate booking
                res.status = 'active'
            else:
                # No vehicle detected, mark as no-show
                res.status = 'no_show'
                res.no_show_checked_at = now
                if slot:
                    slot.status = 'free'
                    slot.last_updated = now
            
            # Broadcast no-show
            await broadcast_booking_update(res, 'no_show')
        
        db.commit()
        
    except Exception as e:
        print(f"❌ Error in reservation scheduler: {e}")
        db.rollback()
    finally:
        db.close()

# Start scheduler
def start_booking_scheduler():
    scheduler.add_job(
        process_reservation_transitions,
        trigger=IntervalTrigger(seconds=60),  # Run every minute
        id='reservation_transitions',
        replace_existing=True
    )
    scheduler.start()
    print("✅ Booking scheduler started")
```

### 4.2 Integrate Scheduler in main.py
```python
# backend/main.py

from scheduler.booking_scheduler import start_booking_scheduler

@asynccontextmanager
async def lifecycle(app: FastAPI):
    # Initialize databases
    init_legacy_db()
    init_entry_exit_db()
    
    # Start background tasks
    app.state.manager = manager
    app.state._stop_bg = False
    app.state._expire_task = asyncio.create_task(auto_expire_slots())
    
    # Start booking scheduler
    start_booking_scheduler()
    
    yield
    
    # Cleanup
    app.state._stop_bg = True
    try:
        app.state._expire_task.cancel()
    except Exception:
        pass
```

---

## 5. Real-Time WebSocket Updates

### 5.1 WebSocket Event Structure
```python
# Event types for booking updates

# 1. Booking Created
{
    "type": "booking_created",
    "data": {
        "reservation_id": 42,
        "booking_reference": "BK-20250108-042",
        "slot_number": "SLOT_10",
        "slot_id": 10,
        "status": "reserved",
        "booking_type": "scheduled",
        "start_time": "2025-01-08T14:00:00Z",
        "end_time": "2025-01-08T16:00:00Z",
        "user_name": "John Doe"
    },
    "timestamp": "2025-01-08T12:00:00Z"
}

# 2. Booking Activated
{
    "type": "booking_activated",
    "data": {
        "reservation_id": 42,
        "slot_number": "SLOT_10",
        "slot_id": 10,
        "status": "active",
        "message": "Booking is now active. Please park within 15 minutes."
    },
    "timestamp": "2025-01-08T14:00:00Z"
}

# 3. Booking Completed
{
    "type": "booking_completed",
    "data": {
        "reservation_id": 42,
        "slot_number": "SLOT_10",
        "slot_id": 10,
        "status": "completed",
        "slot_status": "free"
    },
    "timestamp": "2025-01-08T16:00:00Z"
}

# 4. Booking Cancelled
{
    "type": "booking_cancelled",
    "data": {
        "reservation_id": 42,
        "slot_number": "SLOT_10",
        "slot_id": 10,
        "slot_status": "free",
        "refund_amount": 25.00
    },
    "timestamp": "2025-01-08T13:00:00Z"
}

# 5. Slot Status Changed
{
    "type": "slot_status_changed",
    "data": {
        "slot_number": "SLOT_10",
        "slot_id": 10,
        "old_status": "free",
        "new_status": "reserved",
        "reason": "booking_created",
        "reservation_id": 42
    },
    "timestamp": "2025-01-08T12:00:00Z"
}
```

### 5.2 Broadcast Helper Function
```python
# backend/websocket/broadcaster.py

async def broadcast_booking_update(reservation: Reservation, event_type: str):
    """Broadcast booking updates to all connected WebSocket clients."""
    
    manager = app.state.manager  # WebSocket connection manager
    
    event_data = {
        "type": f"booking_{event_type}",
        "data": {
            "reservation_id": reservation.id,
            "booking_reference": reservation.booking_reference,
            "slot_number": reservation.slot.slot_number,
            "slot_id": reservation.slot_id,
            "status": reservation.status,
            "booking_type": reservation.booking_type,
            "start_time": reservation.start_time.isoformat(),
            "end_time": reservation.end_time.isoformat(),
            "user_name": reservation.user_name
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await manager.broadcast(json.dumps(event_data))
    
    # Also broadcast slot status change
    slot_event = {
        "type": "slot_status_changed",
        "data": {
            "slot_number": reservation.slot.slot_number,
            "slot_id": reservation.slot_id,
            "status": reservation.slot.status.upper(),
            "reservation_id": reservation.id,
            "reason": event_type
        },
        "timestamp": datetime.utcnow().isoformat()
    }
    
    await manager.broadcast(json.dumps(slot_event))
```

---

## 6. Frontend UI Updates

### 6.1 Enhanced Booking Modal
```typescript
// src/components/BookingModal.tsx

interface BookingFormData {
  bookingType: 'immediate' | 'scheduled' | 'hourly' | 'daily';
  startDate?: Date;
  startTime?: string;
  duration?: number;
  userName: string;
  userEmail: string;
  userPhone?: string;
  vehicleNumber?: string;
}

function BookingModal({ slotNumber, onClose, onBooked }) {
  const [formData, setFormData] = useState<BookingFormData>({
    bookingType: 'immediate',
    userName: '',
    userEmail: '',
  });
  
  const [availability, setAvailability] = useState<any>(null);
  const [checking, setChecking] = useState(false);
  
  const checkAvailability = async () => {
    setChecking(true);
    const response = await smartparkApi.checkAvailability(
      slotNumber,
      calculateStartTime(),
      calculateEndTime()
    );
    setAvailability(response);
    setChecking(false);
  };
  
  const handleSubmit = async () => {
    const bookingData = {
      slot_number: slotNumber,
      booking_type: formData.bookingType,
      start_time: calculateStartTime().toISOString(),
      end_time: calculateEndTime().toISOString(),
      user_name: formData.userName,
      user_email: formData.userEmail,
      user_phone: formData.userPhone,
      vehicle_number: formData.vehicleNumber,
    };
    
    try {
      const result = await smartparkApi.createAdvancedBooking(bookingData);
      toast.success(`Booking confirmed! Reference: ${result.booking_reference}`);
      onBooked();
      onClose();
    } catch (error) {
      toast.error(error.message || 'Booking failed');
    }
  };
  
  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Book {slotNumber}</DialogTitle>
        </DialogHeader>
        
        {/* Booking Type Selection */}
        <div className="space-y-4">
          <div>
            <Label>Booking Type</Label>
            <Select value={formData.bookingType} onValueChange={(v) => setFormData({...formData, bookingType: v})}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="immediate">Immediate (Now)</SelectItem>
                <SelectItem value="scheduled">Scheduled (Future)</SelectItem>
                <SelectItem value="hourly">Hourly</SelectItem>
                <SelectItem value="daily">Daily</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          {/* Scheduled/Hourly/Daily: Show date/time pickers */}
          {formData.bookingType !== 'immediate' && (
            <>
              <div>
                <Label>Start Date & Time</Label>
                <Input type="datetime-local" onChange={(e) => {/* handle */}} />
              </div>
              <div>
                <Label>Duration (hours)</Label>
                <Input type="number" min="1" onChange={(e) => {/* handle */}} />
              </div>
            </>
          )}
          
          {/* User Details */}
          <Input placeholder="Your Name" value={formData.userName} onChange={(e) => setFormData({...formData, userName: e.target.value})} />
          <Input placeholder="Email" type="email" value={formData.userEmail} onChange={(e) => setFormData({...formData, userEmail: e.target.value})} />
          <Input placeholder="Phone (optional)" value={formData.userPhone} onChange={(e) => setFormData({...formData, userPhone: e.target.value})} />
          <Input placeholder="Vehicle Number (optional)" value={formData.vehicleNumber} onChange={(e) => setFormData({...formData, vehicleNumber: e.target.value})} />
          
          {/* Availability Check */}
          {formData.bookingType !== 'immediate' && (
            <Button variant="outline" onClick={checkAvailability} disabled={checking}>
              {checking ? 'Checking...' : 'Check Availability'}
            </Button>
          )}
          
          {/* Availability Result */}
          {availability && !availability.available && (
            <Alert variant="destructive">
              <AlertTitle>Slot Not Available</AlertTitle>
              <AlertDescription>
                {availability.conflict_reason}
                {availability.suggested_slots?.length > 0 && (
                  <div className="mt-2">
                    <p>Try these alternatives:</p>
                    <ul>
                      {availability.suggested_slots.map(s => (
                        <li key={s.slot_number}>{s.slot_number}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </AlertDescription>
            </Alert>
          )}
          
          {/* Submit */}
          <Button onClick={handleSubmit} disabled={availability && !availability.available}>
            Confirm Booking
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
```

### 6.2 Slot Card - Reserved State Display
```typescript
// src/components/SlotCard.tsx - Add reserved state

const getStatusConfig = () => {
  switch (slot.status) {
    case 'available':
      return { /* ... green ... */ };
    case 'occupied':
      return { /* ... red ... */ };
    case 'reserved':  // NEW
      return {
        icon: Clock,
        label: 'RESERVED',
        cardClass: 'border-warning/50 bg-warning/5',
        iconClass: 'text-warning',
        glowClass: 'shadow-glow-amber',
        badgeClass: 'bg-gradient-neon-amber text-warning-foreground border-warning/30',
      };
    case 'maintenance':
      return { /* ... gray ... */ };
  }
};

// Show reservation countdown for reserved slots
{slot.status === 'reserved' && slot.reservation_start_time && (
  <div className="flex items-center gap-1.5 px-2 py-1 rounded-full bg-warning/10 border border-warning/30">
    <Clock className="h-3 w-3 text-warning animate-pulse" />
    <span className="text-xs font-exo text-warning">
      Starts in {formatCountdown(slot.reservation_start_time)}
    </span>
  </div>
)}
```

### 6.3 WebSocket Integration - Handle Booking Events
```typescript
// src/hooks/useRealtimeParking.ts

useEffect(() => {
  const ws = smartparkApi.connectWebSocket((message) => {
    const data = JSON.parse(message);
    
    switch (data.type) {
      case 'booking_created':
      case 'booking_activated':
      case 'booking_completed':
      case 'booking_cancelled':
      case 'slot_status_changed':
        // Refresh slot data
        fetchSlots();
        break;
    }
  });
  
  return () => ws?.close();
}, []);
```

---

## 7. Testing Plan

### 7.1 Unit Tests
```python
# tests/test_booking_validator.py

def test_overlap_detection():
    # Test case 1: No overlap
    assert BookingValidator.check_slot_availability(
        db, slot_id=1,
        start_time=datetime(2025, 1, 8, 14, 0),
        end_time=datetime(2025, 1, 8, 16, 0)
    ) == (True, "", [])
    
    # Test case 2: Partial overlap
    # Existing: 14:00-16:00
    # New: 15:00-17:00 (should conflict)
    assert BookingValidator.check_slot_availability(...) == (False, "...", [...])
    
    # Test case 3: Complete overlap
    # Test case 4: New booking contains existing
    # Test case 5: Existing contains new booking

def test_booking_time_validation():
    # Test immediate booking
    # Test scheduled booking in past (should fail)
    # Test daily booking < 24 hours (should fail)
    # Test booking > 7 days (should fail)

def test_race_condition_prevention():
    # Simulate concurrent booking attempts
    # Verify only one succeeds
```

### 7.2 Integration Tests
```python
# tests/test_booking_flow.py

async def test_scheduled_booking_lifecycle():
    # 1. Create scheduled booking for tomorrow 2PM-4PM
    booking = await create_booking(...)
    assert booking.status == 'reserved'
    
    # 2. Verify slot status is 'reserved'
    slot = get_slot(booking.slot_id)
    assert slot.status == 'reserved'
    
    # 3. Fast-forward time to start_time
    # 4. Run scheduler
    # 5. Verify booking status changed to 'active'
    # 6. Verify WebSocket broadcast sent
    
    # 7. Fast-forward to end_time
    # 8. Run scheduler
    # 9. Verify booking completed and slot freed

async def test_no_show_detection():
    # 1. Create booking
    # 2. Don't simulate vehicle arrival
    # 3. Fast-forward past grace period
    # 4. Run scheduler
    # 5. Verify booking marked as no_show
    # 6. Verify slot freed

async def test_concurrent_booking_attempts():
    # Simulate 10 users trying to book same slot simultaneously
    # Verify only 1 succeeds, others get conflict error
```

### 7.3 Manual QA Checklist
- [ ] Immediate booking creates reservation and shows slot as occupied
- [ ] Scheduled booking shows slot as reserved (yellow) immediately
- [ ] Hourly booking validates minimum 1-hour duration
- [ ] Daily booking validates minimum 24-hour duration
- [ ] Conflict detection prevents double bookings
- [ ] Alternative slot suggestions work correctly
- [ ] Booking activation at start_time changes status to active
- [ ] Booking completion at end_time frees the slot
- [ ] No-show detection marks booking and frees slot after grace period
- [ ] Cancellation immediately frees slot and updates UI
- [ ] WebSocket updates all connected clients in real-time
- [ ] Slot colors sync correctly: green (available), yellow (reserved), red (occupied)
- [ ] Timer on occupied slots continues to work correctly
- [ ] Modification of booking validates new time window
- [ ] Payment integration works (if applicable)

---

## 8. Acceptance Criteria

### ✅ Core Functionality
1. **Booking Creation**
   - [ ] All booking types (immediate, scheduled, hourly, daily) can be created successfully
   - [ ] Slot immediately shows as "reserved" (yellow) after scheduled/hourly/daily booking
   - [ ] Immediate booking shows slot as "occupied" (red)
   - [ ] Booking reference generated and returned to user

2. **Conflict Prevention**
   - [ ] System rejects overlapping bookings with clear error message
   - [ ] Alternative slots suggested when requested slot unavailable
   - [ ] Race conditions handled - concurrent attempts result in only one success

3. **Status Transitions**
   - [ ] Reserved → Active at start_time (automated)
   - [ ] Active → Completed at end_time (automated)
   - [ ] Reserved → No-show if vehicle doesn't arrive within grace period
   - [ ] Any status → Cancelled when user cancels

4. **Real-Time Sync**
   - [ ] All clients see slot color change immediately when booking created
   - [ ] WebSocket broadcasts all booking state changes
   - [ ] UI updates without page refresh

5. **Timer Preservation**
   - [ ] Occupied slot timer continues to function exactly as before
   - [ ] Timer shows countdown for occupied slots
   - [ ] No data loss or interruption to existing timer logic

### ✅ Edge Cases Handled
- [ ] Timezone conversions correct
- [ ] Daylight saving time handled
- [ ] Admin can override bookings
- [ ] Cancellation policy enforced (e.g., no refund if < 1 hour to start)
- [ ] Maximum booking duration enforced
- [ ] Minimum booking duration enforced per type

### ✅ Performance
- [ ] Booking creation < 500ms
- [ ] Availability check < 200ms
- [ ] WebSocket latency < 100ms
- [ ] Scheduler runs reliably every minute

---

## 9. Implementation Timeline

### Phase 1: Backend Foundation (Week 1)
- [ ] Update database models
- [ ] Implement BookingValidator service
- [ ] Create/update booking API endpoints
- [ ] Add conflict detection logic
- [ ] Implement row-level locking

### Phase 2: Scheduler & Automation (Week 1-2)
- [ ] Set up APScheduler
- [ ] Implement reservation transition logic
- [ ] Add no-show detection
- [ ] Test scheduler reliability

### Phase 3: Real-Time Updates (Week 2)
- [ ] Enhance WebSocket event structure
- [ ] Implement broadcast functions
- [ ] Test WebSocket reliability

### Phase 4: Frontend Integration (Week 2-3)
- [ ] Update BookingModal with booking types
- [ ] Add date/time pickers for scheduled bookings
- [ ] Implement availability checker UI
- [ ] Update SlotCard for reserved state
- [ ] Add reservation countdown display
- [ ] Handle WebSocket events

### Phase 5: Testing & QA (Week 3)
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual QA
- [ ] Performance testing
- [ ] Bug fixes

### Phase 6: Deployment (Week 4)
- [ ] Database migration
- [ ] Deploy backend updates
- [ ] Deploy frontend updates
- [ ] Monitor production
- [ ] User training/documentation

---

## 10. Rollback Plan

If critical issues arise:
1. **Database**: Keep old schema alongside new (backward compatible)
2. **API**: Version endpoints (`/api/v2/booking/...`)
3. **Feature Flag**: Toggle new booking types on/off
4. **Monitoring**: Alert on booking failures, scheduler errors, WebSocket disconnects

---

## Summary

This implementation plan provides a complete roadmap for extending your Smart Parking system with advanced booking capabilities. Key highlights:

✅ **Robust Conflict Detection** - Prevents double bookings with database-level locking  
✅ **Automated State Transitions** - Scheduler handles reserved→active→completed flow  
✅ **Real-Time Synchronization** - WebSocket broadcasts keep all clients in sync  
✅ **Preserved Timer Logic** - Existing occupied-slot timer remains untouched  
✅ **Comprehensive Testing** - Unit, integration, and manual QA ensure reliability  
✅ **Clear UI/UX** - Reserved slots show yellow, countdowns, and booking details  

The system will support immediate, scheduled, hourly, and daily bookings with proper validation, real-time updates, and seamless user experience.
