"""
API routes for ML predictions and forecasting
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime
import logging

from ..database import get_db
from ..ml.predictor import predictor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ml", tags=["ML Predictions"])

@router.get("/predict/{slot_number}")
async def predict_slot(
    slot_number: str,
    minutes_ahead: int = 15,
    db: Session = Depends(get_db)
):
    """Predict availability for a specific slot"""
    try:
        if slot_number not in ["slot1", "slot2", "slot3"]:
            raise HTTPException(status_code=400, detail="Invalid slot number")
        
        if minutes_ahead < 5 or minutes_ahead > 240:
            raise HTTPException(status_code=400, detail="Minutes ahead must be between 5 and 240")
        
        prediction = predictor.predict_slot_availability(db, slot_number, minutes_ahead)
        
        return {
            "success": True,
            "data": prediction,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error predicting slot {slot_number}: {e}")
        raise HTTPException(status_code=500, detail="Prediction failed")

@router.get("/predict/all")
async def predict_all_slots(
    minutes_ahead: int = 15,
    db: Session = Depends(get_db)
):
    """Predict availability for all slots"""
    try:
        if minutes_ahead < 5 or minutes_ahead > 240:
            raise HTTPException(status_code=400, detail="Minutes ahead must be between 5 and 240")
        
        predictions = predictor.predict_all_slots(db, minutes_ahead)
        
        # Calculate summary
        likely_free = sum(1 for p in predictions if p.get('prediction') == 'free')
        likely_occupied = sum(1 for p in predictions if p.get('prediction') == 'occupied')
        
        return {
            "success": True,
            "data": {
                "predictions": predictions,
                "summary": {
                    "total_slots": 3,
                    "likely_free": likely_free,
                    "likely_occupied": likely_occupied,
                    "prediction_horizon_minutes": minutes_ahead
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error predicting all slots: {e}")
        raise HTTPException(status_code=500, detail="Prediction failed")

@router.get("/forecast")
async def get_occupancy_forecast(
    hours_ahead: int = 2,
    db: Session = Depends(get_db)
):
    """Get detailed occupancy forecast"""
    try:
        if hours_ahead < 1 or hours_ahead > 24:
            raise HTTPException(status_code=400, detail="Hours ahead must be between 1 and 24")
        
        forecast = predictor.get_occupancy_forecast(db, hours_ahead)
        
        if "error" in forecast:
            raise HTTPException(status_code=500, detail=forecast["error"])
        
        return {
            "success": True,
            "data": forecast
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating forecast: {e}")
        raise HTTPException(status_code=500, detail="Forecast generation failed")

@router.post("/train")
async def train_model(
    days_back: int = 30,
    db: Session = Depends(get_db)
):
    """Train the ML model with historical data"""
    try:
        if days_back < 7 or days_back > 365:
            raise HTTPException(status_code=400, detail="Days back must be between 7 and 365")
        
        success, message = predictor.train_model(db, days_back)
        
        if success:
            return {
                "success": True,
                "message": message,
                "training_data_days": days_back,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail=message)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error training model: {e}")
        raise HTTPException(status_code=500, detail="Model training failed")

@router.get("/model/info")
async def get_model_info():
    """Get information about the ML model"""
    try:
        return {
            "success": True,
            "data": {
                "is_trained": predictor.is_trained,
                "model_type": "Random Forest Classifier",
                "features": predictor.feature_columns,
                "prediction_horizons": "5-240 minutes",
                "slots_supported": ["slot1", "slot2", "slot3"],
                "confidence_levels": ["low", "medium", "high"]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get model info")

@router.get("/insights")
async def get_parking_insights(db: Session = Depends(get_db)):
    """Get AI-powered parking insights"""
    try:
        # Get current predictions for different time horizons
        predictions_15min = predictor.predict_all_slots(db, 15)
        predictions_30min = predictor.predict_all_slots(db, 30)
        predictions_60min = predictor.predict_all_slots(db, 60)
        
        # Calculate insights
        current_hour = datetime.utcnow().hour
        
        # Determine peak/off-peak
        peak_hours = [8, 9, 12, 13, 17, 18]  # Typical peak hours
        is_peak_time = current_hour in peak_hours
        
        # Best time recommendation
        if is_peak_time:
            best_time_message = "Consider visiting during off-peak hours (10-11 AM or 2-4 PM) for better availability"
        else:
            best_time_message = "Good time to visit - lower demand expected"
        
        # Availability trend
        free_15min = sum(1 for p in predictions_15min if p.get('prediction') == 'free')
        free_30min = sum(1 for p in predictions_30min if p.get('prediction') == 'free')
        free_60min = sum(1 for p in predictions_60min if p.get('prediction') == 'free')
        
        if free_60min > free_15min:
            trend = "improving"
            trend_message = "Availability expected to improve in the next hour"
        elif free_60min < free_15min:
            trend = "declining"
            trend_message = "Availability expected to decline in the next hour"
        else:
            trend = "stable"
            trend_message = "Availability expected to remain stable"
        
        return {
            "success": True,
            "data": {
                "current_time": datetime.utcnow().isoformat(),
                "is_peak_time": is_peak_time,
                "availability_trend": trend,
                "insights": {
                    "best_time_recommendation": best_time_message,
                    "availability_trend": trend_message,
                    "short_term_forecast": f"{free_15min}/3 slots likely free in 15 minutes",
                    "medium_term_forecast": f"{free_30min}/3 slots likely free in 30 minutes",
                    "long_term_forecast": f"{free_60min}/3 slots likely free in 1 hour"
                },
                "predictions": {
                    "15_minutes": predictions_15min,
                    "30_minutes": predictions_30min,
                    "60_minutes": predictions_60min
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate insights")
