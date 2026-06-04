"""
Pydantic schemas for request/response validation
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

# Slot schemas
class SlotBase(BaseModel):
    slot_label: str
    status: str

class SlotCreate(SlotBase):
    pass

class SlotUpdate(BaseModel):
    status: Optional[str] = None

class Slot(SlotBase):
    id: int
    last_updated: datetime
    
    class Config:
        from_attributes = True

# Reservation schemas
class ReservationBase(BaseModel):
    slot_id: int
    user_id: int
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    start_time: datetime
    end_time: datetime

class ReservationCreate(ReservationBase):
    pass

class ReservationUpdate(BaseModel):
    status: Optional[str] = None
    end_time: Optional[datetime] = None

class Reservation(ReservationBase):
    id: int
    status: str
    created_at: datetime
    slot: Optional[Slot] = None
    
    class Config:
        from_attributes = True

# Sensor log schemas
class SensorLogBase(BaseModel):
    slot_id: int
    occupied: bool

class SensorLogCreate(SensorLogBase):
    pass

class SensorLog(SensorLogBase):
    id: int
    timestamp: datetime
    slot: Optional[Slot] = None
    
    class Config:
        from_attributes = True

# Forecast schemas
class ForecastBase(BaseModel):
    slot_id: int
    horizon_minutes: int
    prediction: float = Field(..., ge=0.0, le=1.0)

class ForecastCreate(ForecastBase):
    pass

class Forecast(ForecastBase):
    id: int
    generated_at: datetime
    slot: Optional[Slot] = None
    
    class Config:
        from_attributes = True

# API Response schemas
class SlotStatus(BaseModel):
    """Real-time slot status for frontend"""
    id: int
    slot_label: str
    status: str
    last_updated: datetime
    has_active_reservation: bool = False
    reservation_end_time: Optional[datetime] = None

class ParkingOverview(BaseModel):
    """Overview of parking lot status"""
    total_slots: int
    free_slots: int
    occupied_slots: int
    reserved_slots: int
    slots: List[SlotStatus]

class ForecastResponse(BaseModel):
    """ML prediction response"""
    slot_id: int
    slot_label: str
    horizon_minutes: int
    probability_free: float
    confidence: str
    generated_at: datetime

class AdminAnalytics(BaseModel):
    """Admin dashboard analytics"""
    total_slots: int
    current_occupancy_rate: float
    avg_daily_occupancy: float
    total_reservations_today: int
    revenue_today: float
    peak_hours: List[int]
    recent_events: List[dict]

# WebSocket message schemas
class WebSocketMessage(BaseModel):
    type: str
    data: dict

class SlotUpdateMessage(BaseModel):
    type: str = "slot_update"
    slot_id: int
    slot_label: str
    status: str
    timestamp: datetime

# Error response schema
class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[dict] = None
