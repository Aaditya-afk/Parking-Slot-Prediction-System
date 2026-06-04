from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from database_entry_exit import get_db
from models.parking import Feedback

router = APIRouter(prefix="/api/feedback", tags=["feedback"])

# Use IST for display if needed
IST = timezone(timedelta(hours=5, minutes=30))

def to_ist(dt: datetime) -> str:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IST).isoformat()

class FeedbackCreate(BaseModel):
    user_name: str = Field(..., min_length=1)
    user_email: str = Field(..., min_length=3)
    rating: int = Field(..., ge=1, le=5)
    category: str = Field(..., pattern=r"^(complaint|suggestion|praise|bug_report|general)$")
    message: str = Field(..., min_length=3)
    user_id: Optional[str] = None

class FeedbackRespond(BaseModel):
    admin_response: str = Field(..., min_length=1)
    reviewed_by: str = Field(..., min_length=1)

@router.post("/submit")
async def submit_feedback(payload: FeedbackCreate, db: Session = Depends(get_db)):
    fb = Feedback(
        user_id=payload.user_id or "anonymous",
        user_name=payload.user_name,
        user_email=payload.user_email,
        rating=payload.rating,
        category=payload.category,
        message=payload.message,
        status="pending",
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return {
        "success": True,
        "data": {
            "id": fb.id,
            "created_at": to_ist(fb.created_at),
        }
    }

@router.get("/list")
async def list_feedback(status: Optional[str] = None, category: Optional[str] = None, limit: int = 50, db: Session = Depends(get_db)):
    q = db.query(Feedback).order_by(Feedback.created_at.desc())
    if status:
        q = q.filter(Feedback.status == status)
    if category:
        q = q.filter(Feedback.category == category)
    items = q.limit(min(200, max(1, limit))).all()
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
                "created_at": to_ist(f.created_at),
                "admin_response": f.admin_response,
                "reviewed_by": f.reviewed_by,
                "reviewed_at": to_ist(f.reviewed_at),
            } for f in items
        ]
    }

@router.get("/stats")
async def feedback_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Feedback.id)).scalar() or 0
    pending = db.query(func.count(Feedback.id)).filter(Feedback.status == "pending").scalar() or 0
    by_category_rows = db.query(Feedback.category, func.count(Feedback.id)).group_by(Feedback.category).all()
    by_category = {row[0]: row[1] for row in by_category_rows}
    ratings = db.query(func.avg(Feedback.rating)).scalar()
    avg_rating = float(ratings) if ratings is not None else 0.0
    return {
        "success": True,
        "data": {
            "total": total,
            "pending": pending,
            "average_rating": round(avg_rating, 1),
            "by_category": by_category,
        }
    }

@router.put("/{feedback_id}/respond")
async def respond(feedback_id: int, payload: FeedbackRespond, db: Session = Depends(get_db)):
    fb = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback not found")
    fb.admin_response = payload.admin_response
    fb.reviewed_by = payload.reviewed_by
    fb.reviewed_at = datetime.utcnow()
    fb.status = "reviewed"
    db.commit()
    return {"success": True}
