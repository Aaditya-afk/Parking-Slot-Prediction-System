"""
API routes for AI/ML insights and predictions - SmartPark Entry/Exit System
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime
import logging

from ..database_entry_exit import get_db, log_system_event
from ..ml.occupancy_predictor import predictor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["AI Insights"])

@router.get("/predict_occupancy")
async def predict_occupancy(
    hours_ahead: int = 2,
    db: Session = Depends(get_db)
):
    """Get AI-powered occupancy predictions for the next few hours"""
    try:
        if hours_ahead < 1 or hours_ahead > 24:
            raise HTTPException(status_code=400, detail="Hours ahead must be between 1 and 24")
        
        predictions = predictor.predict_occupancy(db, hours_ahead)
        
        if not predictions.get("success"):
            error_msg = predictions.get("error", "Prediction failed")
            if "not trained" in error_msg.lower():
                raise HTTPException(status_code=503, detail="AI model not trained yet. Please train the model first.")
            else:
                raise HTTPException(status_code=500, detail=error_msg)
        
        return {
            "success": True,
            "data": predictions,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting occupancy predictions: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate predictions")

@router.get("/insights")
async def get_parking_insights(db: Session = Depends(get_db)):
    """Get comprehensive AI-powered parking insights"""
    try:
        insights = predictor.get_occupancy_insights(db)
        
        if "error" in insights:
            error_msg = insights["error"]
            if "not trained" in error_msg.lower():
                raise HTTPException(status_code=503, detail="AI model not trained yet. Please train the model first.")
            else:
                raise HTTPException(status_code=500, detail=error_msg)
        
        return {
            "success": True,
            "data": insights,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate insights")

@router.post("/train_model")
async def train_ai_model(
    days_back: int = 30,
    db: Session = Depends(get_db)
):
    """Train the AI occupancy prediction model"""
    try:
        if days_back < 7 or days_back > 365:
            raise HTTPException(status_code=400, detail="Days back must be between 7 and 365")
        
        success, message = predictor.train_model(db, days_back)
        
        if success:
            # Log training event
            log_system_event(db, "INFO", "ai", f"Model trained successfully: {message}")
            
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
        logger.error(f"❌ Error training model: {e}")
        raise HTTPException(status_code=500, detail="Model training failed")

@router.get("/model_info")
async def get_model_info():
    """Get information about the AI model"""
    try:
        return {
            "success": True,
            "data": {
                "is_trained": predictor.is_trained,
                "model_type": "Random Forest Regressor",
                "features": predictor.feature_columns,
                "prediction_horizons": "1-24 hours",
                "total_slots": predictor.total_slots,
                "confidence_levels": ["low", "medium", "high"],
                "capabilities": [
                    "Occupancy rate prediction",
                    "Trend analysis",
                    "Best time recommendations",
                    "Peak hour detection"
                ]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting model info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get model info")

@router.get("/occupancy_trends")
async def get_occupancy_trends(
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get historical occupancy trends for analysis"""
    try:
        from datetime import timedelta
        from ..models.parking import OccupancyStats
        
        if hours < 1 or hours > 168:  # Max 1 week
            raise HTTPException(status_code=400, detail="Hours must be between 1 and 168")
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Get occupancy stats
        stats = db.query(OccupancyStats).filter(
            OccupancyStats.timestamp >= cutoff_time
        ).order_by(OccupancyStats.timestamp).all()
        
        if not stats:
            return {
                "success": True,
                "data": {
                    "trends": [],
                    "summary": {
                        "period_hours": hours,
                        "data_points": 0,
                        "average_occupancy": 0,
                        "peak_occupancy": 0,
                        "lowest_occupancy": 0
                    }
                },
                "message": "No historical data available"
            }
        
        # Format trend data
        trends = []
        occupancy_rates = []
        
        for stat in stats:
            trend_point = {
                "timestamp": stat.timestamp.isoformat(),
                "hour": stat.hour,
                "day_of_week": stat.day_of_week,
                "occupancy_rate": stat.occupancy_rate,
                "occupied_slots": stat.occupied_slots,
                "free_slots": stat.free_slots,
                "entry_events": stat.entry_events_hour,
                "exit_events": stat.exit_events_hour
            }
            trends.append(trend_point)
            occupancy_rates.append(stat.occupancy_rate)
        
        # Calculate summary statistics
        avg_occupancy = sum(occupancy_rates) / len(occupancy_rates)
        peak_occupancy = max(occupancy_rates)
        lowest_occupancy = min(occupancy_rates)
        
        # Find peak hours
        hourly_avg = {}
        for stat in stats:
            if stat.hour not in hourly_avg:
                hourly_avg[stat.hour] = []
            hourly_avg[stat.hour].append(stat.occupancy_rate)
        
        peak_hours = []
        for hour, rates in hourly_avg.items():
            avg_rate = sum(rates) / len(rates)
            if avg_rate > avg_occupancy:
                peak_hours.append(hour)
        
        return {
            "success": True,
            "data": {
                "trends": trends,
                "summary": {
                    "period_hours": hours,
                    "data_points": len(trends),
                    "average_occupancy": round(avg_occupancy, 1),
                    "peak_occupancy": round(peak_occupancy, 1),
                    "lowest_occupancy": round(lowest_occupancy, 1),
                    "peak_hours": sorted(peak_hours)
                }
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting occupancy trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to get occupancy trends")

@router.post("/update_stats")
async def update_occupancy_stats(db: Session = Depends(get_db)):
    """Manually update occupancy statistics (admin endpoint)"""
    try:
        predictor.update_occupancy_stats(db)
        
        return {
            "success": True,
            "message": "Occupancy statistics updated successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error updating occupancy stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to update occupancy stats")

@router.get("/recommendations")
async def get_smart_recommendations(db: Session = Depends(get_db)):
    """Get smart parking recommendations based on AI analysis"""
    try:
        insights = predictor.get_occupancy_insights(db)
        
        if "error" in insights:
            # Return basic recommendations without AI
            from ..database_entry_exit import get_slot_stats
            stats = get_slot_stats(db)
            
            basic_recommendations = {
                "current_availability": {
                    "free_slots": stats["free_slots"],
                    "total_slots": stats["total_slots"],
                    "occupancy_rate": stats["occupancy_rate"]
                },
                "recommendations": [
                    {
                        "type": "availability",
                        "message": f"{stats['free_slots']} out of {stats['total_slots']} slots currently available",
                        "priority": "high" if stats["free_slots"] > 0 else "low"
                    },
                    {
                        "type": "general",
                        "message": "Visit during off-peak hours (10-11 AM, 2-4 PM) for better availability",
                        "priority": "medium"
                    }
                ],
                "ai_status": "Model not trained - showing basic recommendations"
            }
            
            return {
                "success": True,
                "data": basic_recommendations,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Extract recommendations from AI insights
        recommendations = []
        
        # Current availability
        current_status = insights["current_status"]
        if current_status["free_slots"] > 0:
            recommendations.append({
                "type": "availability",
                "message": f"{current_status['free_slots']} slots available now",
                "priority": "high",
                "action": "park_now"
            })
        else:
            recommendations.append({
                "type": "availability",
                "message": "No slots currently available",
                "priority": "low",
                "action": "wait_or_reserve"
            })
        
        # Best time recommendation
        best_time = insights["recommendations"]["best_time_next_4h"]
        recommendations.append({
            "type": "timing",
            "message": f"Best availability expected in {best_time['hour']} hour(s) with {best_time['expected_free_slots']} free slots",
            "priority": "medium",
            "action": "plan_visit",
            "suggested_time": best_time["time"]
        })
        
        # Trend-based recommendation
        trend = insights["trend_analysis"]["direction"]
        if trend == "increasing":
            recommendations.append({
                "type": "trend",
                "message": "Occupancy is increasing - consider visiting soon",
                "priority": "medium",
                "action": "hurry"
            })
        elif trend == "decreasing":
            recommendations.append({
                "type": "trend",
                "message": "Occupancy is decreasing - more slots becoming available",
                "priority": "low",
                "action": "wait_a_bit"
            })
        
        # Peak time warning
        if insights["recommendations"]["avoid_peak"]:
            recommendations.append({
                "type": "peak_warning",
                "message": "Currently peak hours - consider visiting during off-peak times",
                "priority": "medium",
                "action": "avoid_peak"
            })
        
        return {
            "success": True,
            "data": {
                "current_status": current_status,
                "recommendations": recommendations,
                "ai_insights": insights,
                "ai_status": "Active and providing smart recommendations"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")
