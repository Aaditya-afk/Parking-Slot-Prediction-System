"""
ML Forecast API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from database import get_db
from models import Slot, Forecast
from schemas import ForecastResponse
from ml_model import MLPredictor
import utils

logger = logging.getLogger(__name__)
router = APIRouter()

# Global ML predictor instance
ml_predictor = None

def get_ml_predictor():
    """Get or create ML predictor instance"""
    global ml_predictor
    if ml_predictor is None:
        ml_predictor = MLPredictor()
    return ml_predictor

@router.get("/forecast", response_model=List[ForecastResponse])
async def get_parking_forecast(
    minutes: int = Query(30, ge=5, le=1440, description="Forecast horizon in minutes (5-1440)"),
    slot_id: Optional[int] = Query(None, description="Specific slot ID (optional)"),
    db: Session = Depends(get_db)
):
    """Get ML-based parking availability forecast"""
    try:
        predictor = get_ml_predictor()
        
        # Get slots to predict for
        if slot_id:
            slots = db.query(Slot).filter(Slot.id == slot_id).all()
            if not slots:
                raise HTTPException(status_code=404, detail="Slot not found")
        else:
            slots = db.query(Slot).all()
        
        forecasts = []
        
        for slot in slots:
            try:
                # Get prediction from ML model
                probability = predictor.predict_availability(db, slot.id, minutes)
                
                # Determine confidence level
                if probability >= 0.8:
                    confidence = "high"
                elif probability >= 0.6:
                    confidence = "medium"
                else:
                    confidence = "low"
                
                # Save forecast to database
                forecast_record = Forecast(
                    slot_id=slot.id,
                    horizon_minutes=minutes,
                    prediction=probability,
                    generated_at=utils.get_current_time()
                )
                db.add(forecast_record)
                
                # Create response
                forecast_response = ForecastResponse(
                    slot_id=slot.id,
                    slot_label=slot.slot_label,
                    horizon_minutes=minutes,
                    probability_free=probability,
                    confidence=confidence,
                    generated_at=forecast_record.generated_at
                )
                
                forecasts.append(forecast_response)
                
            except Exception as e:
                logger.error(f"Error predicting for slot {slot.id}: {e}")
                # Continue with other slots
                continue
        
        db.commit()
        
        if not forecasts:
            raise HTTPException(status_code=500, detail="Unable to generate forecasts")
        
        logger.info(f"Generated {len(forecasts)} forecasts for {minutes} minutes horizon")
        
        return forecasts
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating forecast: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/forecast/summary")
async def get_forecast_summary(
    minutes: int = Query(30, ge=5, le=1440),
    db: Session = Depends(get_db)
):
    """Get summarized forecast for all slots"""
    try:
        predictor = get_ml_predictor()
        slots = db.query(Slot).all()
        
        total_slots = len(slots)
        likely_free = 0
        likely_occupied = 0
        uncertain = 0
        
        slot_predictions = []
        
        for slot in slots:
            try:
                probability = predictor.predict_availability(db, slot.id, minutes)
                
                if probability >= 0.7:
                    likely_free += 1
                    status = "likely_free"
                elif probability <= 0.3:
                    likely_occupied += 1
                    status = "likely_occupied"
                else:
                    uncertain += 1
                    status = "uncertain"
                
                slot_predictions.append({
                    "slot_id": slot.id,
                    "slot_label": slot.slot_label,
                    "probability_free": probability,
                    "predicted_status": status
                })
                
            except Exception as e:
                logger.error(f"Error predicting for slot {slot.id}: {e}")
                uncertain += 1
                slot_predictions.append({
                    "slot_id": slot.id,
                    "slot_label": slot.slot_label,
                    "probability_free": 0.5,
                    "predicted_status": "error"
                })
        
        return {
            "forecast_horizon_minutes": minutes,
            "generated_at": utils.get_current_time().isoformat(),
            "summary": {
                "total_slots": total_slots,
                "likely_free": likely_free,
                "likely_occupied": likely_occupied,
                "uncertain": uncertain
            },
            "slot_predictions": slot_predictions
        }
        
    except Exception as e:
        logger.error(f"Error generating forecast summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/forecast/train")
async def train_ml_model(db: Session = Depends(get_db)):
    """Train the ML prediction model (admin function)"""
    try:
        predictor = get_ml_predictor()
        
        # Train the model
        success, message = predictor.train_model(db)
        
        if success:
            utils.log_system_event(db, "INFO", "ML model training completed successfully", "ml_model")
            return {
                "message": "Model training completed successfully",
                "details": message
            }
        else:
            utils.log_system_event(db, "ERROR", f"ML model training failed: {message}", "ml_model")
            raise HTTPException(status_code=500, detail=f"Model training failed: {message}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error training ML model: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/forecast/model-info")
async def get_model_info():
    """Get information about the current ML model"""
    try:
        predictor = get_ml_predictor()
        info = predictor.get_model_info()
        
        return {
            "model_info": info,
            "timestamp": utils.get_current_time().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/forecast/accuracy")
async def get_model_accuracy(
    days: int = Query(7, ge=1, le=30, description="Number of days to evaluate"),
    db: Session = Depends(get_db)
):
    """Get model accuracy metrics"""
    try:
        predictor = get_ml_predictor()
        
        # Calculate accuracy metrics
        accuracy_metrics = predictor.evaluate_model(db, days)
        
        return {
            "evaluation_period_days": days,
            "accuracy_metrics": accuracy_metrics,
            "evaluated_at": utils.get_current_time().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error calculating model accuracy: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/forecast/history/{slot_id}")
async def get_forecast_history(
    slot_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Get historical forecasts for a specific slot"""
    try:
        slot = db.query(Slot).filter(Slot.id == slot_id).first()
        if not slot:
            raise HTTPException(status_code=404, detail="Slot not found")
        
        forecasts = db.query(Forecast).filter(
            Forecast.slot_id == slot_id
        ).order_by(Forecast.generated_at.desc()).limit(limit).all()
        
        forecast_history = []
        for forecast in forecasts:
            forecast_history.append({
                "id": forecast.id,
                "generated_at": forecast.generated_at.isoformat(),
                "horizon_minutes": forecast.horizon_minutes,
                "prediction": forecast.prediction
            })
        
        return {
            "slot_id": slot_id,
            "slot_label": slot.slot_label,
            "forecast_count": len(forecast_history),
            "forecasts": forecast_history
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching forecast history for slot {slot_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
