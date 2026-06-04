# Admin Panel & Feedback System - Implementation Plan

## Current Issues

### 1. Admin Dashboard
- ❌ Shows mock data (Active Bookings: 1, Total Feedback: 3)
- ❌ Not connected to real database
- ❌ System Health percentage is static
- ❌ No real-time updates

### 2. Feedback System
- ❌ Feedback submission not saving to database
- ❌ Admin panel shows mock feedback entries
- ❌ Dates are incorrect (showing 7/10/2025 instead of current IST)
- ❌ No backend API endpoints for feedback

### 3. Missing Features
- ❌ No feedback database model
- ❌ No API endpoints for feedback CRUD operations
- ❌ No real-time statistics calculation
- ❌ No action items tracking

---

## Solution: Complete Admin & Feedback Implementation

### Phase 1: Database Model for Feedback

**File: `backend/models/parking.py`**

Add Feedback model:
```python
class Feedback(Base):
    """User feedback model"""
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True)
    user_name = Column(String(100))
    user_email = Column(String(100))
    
    # Feedback content
    rating = Column(Integer)  # 1-5 stars
    category = Column(String(50))  # 'complaint', 'suggestion', 'praise', 'bug_report'
    message = Column(Text)
    
    # Status tracking
    status = Column(String(20), default="pending")  # pending, reviewed, resolved, dismissed
    priority = Column(String(20), default="normal")  # low, normal, high, critical
    
    # Admin response
    admin_response = Column(Text, nullable=True)
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Feedback(id={self.id}, rating={self.rating}, category='{self.category}', status='{self.status}')>"
```

### Phase 2: Backend API Endpoints

**File: `backend/routes/feedback.py` (NEW)**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from database_entry_exit import get_db
from models.parking import Feedback

router = APIRouter(prefix="/api/feedback", tags=["feedback"])

class FeedbackCreate(BaseModel):
    user_name: str
    user_email: str
    rating: int  # 1-5
    category: str  # complaint, suggestion, praise, bug_report
    message: str
    user_id: Optional[str] = None

class FeedbackResponse(BaseModel):
    admin_response: str
    reviewed_by: str

@router.post("/submit")
async def submit_feedback(feedback: FeedbackCreate, db: Session = Depends(get_db)):
    """Submit user feedback"""
    new_feedback = Feedback(
        user_id=feedback.user_id or "anonymous",
        user_name=feedback.user_name,
        user_email=feedback.user_email,
        rating=feedback.rating,
        category=feedback.category,
        message=feedback.message,
        status="pending"
    )
    db.add(new_feedback)
    db.commit()
    db.refresh(new_feedback)
    
    return {
        "success": True,
        "message": "Feedback submitted successfully",
        "feedback_id": new_feedback.id
    }

@router.get("/list")
async def list_feedback(
    status: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get all feedback (admin only)"""
    query = db.query(Feedback).order_by(Feedback.created_at.desc())
    
    if status:
        query = query.filter(Feedback.status == status)
    if category:
        query = query.filter(Feedback.category == category)
    
    feedbacks = query.limit(limit).all()
    
    return {
        "success": True,
        "data": [
            {
                "id": f.id,
                "user_name": f.user_name,
                "user_email": f.user_email,
                "rating": f.rating,
                "category": f.category,
                "message": f.message,
                "status": f.status,
                "priority": f.priority,
                "created_at": f.created_at.isoformat(),
                "admin_response": f.admin_response,
                "reviewed_at": f.reviewed_at.isoformat() if f.reviewed_at else None
            }
            for f in feedbacks
        ]
    }

@router.put("/{feedback_id}/respond")
async def respond_to_feedback(
    feedback_id: int,
    response: FeedbackResponse,
    db: Session = Depends(get_db)
):
    """Admin responds to feedback"""
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    feedback.admin_response = response.admin_response
    feedback.reviewed_by = response.reviewed_by
    feedback.reviewed_at = datetime.utcnow()
    feedback.status = "reviewed"
    
    db.commit()
    
    return {"success": True, "message": "Response added successfully"}

@router.get("/stats")
async def feedback_stats(db: Session = Depends(get_db)):
    """Get feedback statistics"""
    total = db.query(Feedback).count()
    pending = db.query(Feedback).filter(Feedback.status == "pending").count()
    resolved = db.query(Feedback).filter(Feedback.status == "resolved").count()
    
    # Average rating
    ratings = db.query(Feedback.rating).all()
    avg_rating = sum(r[0] for r in ratings) / len(ratings) if ratings else 0
    
    # Category breakdown
    categories = db.query(Feedback.category, func.count(Feedback.id)).group_by(Feedback.category).all()
    
    return {
        "success": True,
        "data": {
            "total_feedback": total,
            "pending": pending,
            "resolved": resolved,
            "average_rating": round(avg_rating, 1),
            "by_category": {cat: count for cat, count in categories}
        }
    }
```

### Phase 3: Admin Dashboard API

**File: `backend/routes/admin.py` (NEW)**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from database_entry_exit import get_db
from models.parking import ParkingSlot, Reservation, Feedback, CarEvent

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/dashboard")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get real-time admin dashboard statistics"""
    
    # Active bookings count
    active_bookings = db.query(Reservation).filter(
        Reservation.status.in_(["active", "reserved"])
    ).count()
    
    # Total feedback count
    total_feedback = db.query(Feedback).count()
    
    # Average rating
    ratings = db.query(Feedback.rating).all()
    avg_rating = sum(r[0] for r in ratings) / len(ratings) if ratings else 0
    
    # System health calculation
    total_slots = db.query(ParkingSlot).count()
    free_slots = db.query(ParkingSlot).filter(ParkingSlot.status == "free").count()
    maintenance_slots = db.query(ParkingSlot).filter(ParkingSlot.status == "maintenance").count()
    
    # System health = (working slots / total slots) * 100
    working_slots = total_slots - maintenance_slots
    system_health = (working_slots / total_slots * 100) if total_slots > 0 else 0
    
    # Recent activity (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(hours=24)
    recent_bookings = db.query(Reservation).filter(
        Reservation.created_at >= yesterday
    ).count()
    recent_feedback = db.query(Feedback).filter(
        Feedback.created_at >= yesterday
    ).count()
    
    # Pending actions
    pending_feedback = db.query(Feedback).filter(Feedback.status == "pending").count()
    critical_feedback = db.query(Feedback).filter(
        Feedback.priority == "critical",
        Feedback.status == "pending"
    ).count()
    
    return {
        "success": True,
        "data": {
            "active_bookings": active_bookings,
            "total_feedback": total_feedback,
            "average_rating": round(avg_rating, 1),
            "system_health": round(system_health, 1),
            "recent_activity": {
                "bookings_24h": recent_bookings,
                "feedback_24h": recent_feedback
            },
            "pending_actions": {
                "pending_feedback": pending_feedback,
                "critical_issues": critical_feedback
            },
            "slot_status": {
                "total": total_slots,
                "free": free_slots,
                "occupied": db.query(ParkingSlot).filter(ParkingSlot.status == "occupied").count(),
                "reserved": db.query(ParkingSlot).filter(ParkingSlot.status == "reserved").count(),
                "maintenance": maintenance_slots
            }
        }
    }

@router.get("/action-items")
async def get_action_items(db: Session = Depends(get_db)):
    """Get items requiring admin attention"""
    
    # Critical feedback
    critical = db.query(Feedback).filter(
        Feedback.priority == "critical",
        Feedback.status == "pending"
    ).all()
    
    # Pending feedback
    pending = db.query(Feedback).filter(
        Feedback.status == "pending"
    ).order_by(Feedback.created_at.desc()).limit(10).all()
    
    # Maintenance slots
    maintenance = db.query(ParkingSlot).filter(
        ParkingSlot.status == "maintenance"
    ).all()
    
    return {
        "success": True,
        "data": {
            "critical_feedback": [
                {
                    "id": f.id,
                    "message": f.message,
                    "category": f.category,
                    "created_at": f.created_at.isoformat()
                }
                for f in critical
            ],
            "pending_feedback": [
                {
                    "id": f.id,
                    "user_name": f.user_name,
                    "rating": f.rating,
                    "category": f.category,
                    "message": f.message[:100] + "..." if len(f.message) > 100 else f.message,
                    "created_at": f.created_at.isoformat()
                }
                for f in pending
            ],
            "maintenance_slots": [
                {
                    "slot_number": s.slot_number,
                    "last_updated": s.last_updated.isoformat()
                }
                for s in maintenance
            ]
        }
    }
```

### Phase 4: Frontend Integration

**Update `src/services/smartparkAPI.ts`:**

```typescript
// Feedback APIs
async submitFeedback(feedback: {
  user_name: string;
  user_email: string;
  rating: number;
  category: string;
  message: string;
}): Promise<any> {
  const res = await fetch(`${this.baseURL}/api/feedback/submit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(feedback),
  });
  return res.json();
}

async getFeedbackList(status?: string, category?: string): Promise<any> {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  if (category) params.append('category', category);
  
  const res = await fetch(`${this.baseURL}/api/feedback/list?${params}`);
  return res.json();
}

async getFeedbackStats(): Promise<any> {
  const res = await fetch(`${this.baseURL}/api/feedback/stats`);
  return res.json();
}

// Admin APIs
async getAdminDashboard(): Promise<any> {
  const res = await fetch(`${this.baseURL}/api/admin/dashboard`);
  return res.json();
}

async getActionItems(): Promise<any> {
  const res = await fetch(`${this.baseURL}/api/admin/action-items`);
  return res.json();
}
```

### Phase 5: Update Admin Page

**Update Admin Dashboard to fetch real data:**

```typescript
// src/pages/Admin.tsx
useEffect(() => {
  const fetchDashboardData = async () => {
    try {
      const response = await smartparkApi.getAdminDashboard();
      if (response.success) {
        setActiveBookings(response.data.active_bookings);
        setTotalFeedback(response.data.total_feedback);
        setAverageRating(response.data.average_rating);
        setSystemHealth(response.data.system_health);
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    }
  };
  
  fetchDashboardData();
  // Refresh every 30 seconds
  const interval = setInterval(fetchDashboardData, 30000);
  return () => clearInterval(interval);
}, []);
```

---

## Implementation Steps

### Step 1: Backend Setup
1. Add `Feedback` model to `models/parking.py`
2. Create `routes/feedback.py` with all endpoints
3. Create `routes/admin.py` with dashboard endpoints
4. Register routes in `main.py`:
   ```python
   from routes.feedback import router as feedback_router
   from routes.admin import router as admin_router
   
   app.include_router(feedback_router)
   app.include_router(admin_router)
   ```
5. Delete old database and restart server to create new tables

### Step 2: Frontend Integration
1. Add feedback API methods to `smartparkAPI.ts`
2. Update Admin page to fetch real data
3. Update Feedback page to submit to API
4. Add IST date formatting for feedback timestamps

### Step 3: Testing
1. Submit test feedback from Feedback page
2. Verify it appears in Admin panel
3. Check dashboard statistics update in real-time
4. Test admin response functionality

---

## Expected Results

✅ **Admin Dashboard:**
- Shows real active bookings count
- Shows real feedback count
- Calculates actual system health
- Updates every 30 seconds

✅ **Feedback System:**
- Users can submit feedback with rating and category
- Feedback saves to database
- Admin sees all feedback with correct IST timestamps
- Admin can respond to feedback

✅ **Action Items:**
- Shows critical feedback requiring attention
- Lists maintenance slots
- Displays pending feedback count

✅ **Real-Time Updates:**
- Dashboard refreshes automatically
- WebSocket broadcasts feedback submissions
- All timestamps in IST format
