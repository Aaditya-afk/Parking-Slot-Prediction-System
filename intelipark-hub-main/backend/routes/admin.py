"""
Admin API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from database import get_db
from models import Slot, Reservation, SensorLog, SystemLog
from schemas import AdminAnalytics
import utils

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/analytics", response_model=AdminAnalytics)
async def get_analytics(db: Session = Depends(get_db)):
    """Get comprehensive analytics for admin dashboard"""
    try:
        current_time = utils.get_current_time()
        today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Basic slot statistics
        total_slots = db.query(Slot).count()
        occupied_slots = db.query(Slot).filter(Slot.status == "OCCUPIED").count()
        current_occupancy_rate = (occupied_slots / total_slots * 100) if total_slots > 0 else 0
        
        # Daily occupancy average
        avg_daily_occupancy = utils.calculate_occupancy_rate(db, 24)
        
        # Today's reservations
        total_reservations_today = db.query(Reservation).filter(
            Reservation.created_at >= today_start
        ).count()
        
        # Calculate revenue (assuming $5 per hour)
        completed_reservations_today = db.query(Reservation).filter(
            Reservation.created_at >= today_start,
            Reservation.status == "completed"
        ).all()
        
        revenue_today = 0.0
        for reservation in completed_reservations_today:
            duration_hours = (reservation.end_time - reservation.start_time).total_seconds() / 3600
            revenue_today += duration_hours * 5.0  # $5 per hour
        
        # Peak hours
        peak_hours = utils.get_peak_hours(db, 7)
        
        # Recent events
        recent_logs = db.query(SystemLog).order_by(desc(SystemLog.timestamp)).limit(10).all()
        recent_events = []
        for log in recent_logs:
            recent_events.append({
                "timestamp": log.timestamp.isoformat(),
                "level": log.level,
                "message": log.message,
                "component": log.component
            })
        
        return AdminAnalytics(
            total_slots=total_slots,
            current_occupancy_rate=current_occupancy_rate,
            avg_daily_occupancy=avg_daily_occupancy,
            total_reservations_today=total_reservations_today,
            revenue_today=revenue_today,
            peak_hours=peak_hours,
            recent_events=recent_events
        )
        
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/logs")
async def get_system_logs(
    level: Optional[str] = Query(None, description="Filter by log level"),
    component: Optional[str] = Query(None, description="Filter by component"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get system logs with filtering"""
    try:
        query = db.query(SystemLog)
        
        if level:
            valid_levels = ["INFO", "WARNING", "ERROR"]
            if level.upper() not in valid_levels:
                raise HTTPException(status_code=400, detail=f"Invalid level. Must be one of: {valid_levels}")
            query = query.filter(SystemLog.level == level.upper())
        
        if component:
            query = query.filter(SystemLog.component == component)
        
        logs = query.order_by(desc(SystemLog.timestamp)).limit(limit).all()
        
        log_entries = []
        for log in logs:
            log_entries.append({
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "level": log.level,
                "message": log.message,
                "component": log.component
            })
        
        return {
            "total_logs": len(log_entries),
            "filters": {
                "level": level,
                "component": component,
                "limit": limit
            },
            "logs": log_entries
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching logs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/sensor-logs")
async def get_sensor_logs(
    slot_id: Optional[int] = Query(None, description="Filter by slot ID"),
    hours: int = Query(24, ge=1, le=168, description="Hours of history to fetch"),
    db: Session = Depends(get_db)
):
    """Get sensor event logs"""
    try:
        end_time = utils.get_current_time()
        start_time = end_time - timedelta(hours=hours)
        
        query = db.query(SensorLog).filter(
            SensorLog.timestamp >= start_time
        )
        
        if slot_id:
            # Verify slot exists
            slot = db.query(Slot).filter(Slot.id == slot_id).first()
            if not slot:
                raise HTTPException(status_code=404, detail="Slot not found")
            query = query.filter(SensorLog.slot_id == slot_id)
        
        logs = query.order_by(desc(SensorLog.timestamp)).limit(1000).all()
        
        sensor_events = []
        for log in logs:
            sensor_events.append({
                "id": log.id,
                "slot_id": log.slot_id,
                "slot_label": log.slot.slot_label if log.slot else None,
                "timestamp": log.timestamp.isoformat(),
                "occupied": log.occupied,
                "event_type": "OCCUPIED" if log.occupied else "FREE"
            })
        
        return {
            "total_events": len(sensor_events),
            "period_hours": hours,
            "slot_filter": slot_id,
            "events": sensor_events
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching sensor logs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/occupancy-trends")
async def get_occupancy_trends(
    days: int = Query(7, ge=1, le=30, description="Number of days for trend analysis"),
    db: Session = Depends(get_db)
):
    """Get occupancy trends over time"""
    try:
        end_time = utils.get_current_time()
        start_time = end_time - timedelta(days=days)
        
        # Get hourly occupancy data
        hourly_data = {}
        
        # Query sensor logs grouped by hour
        logs = db.query(SensorLog).filter(
            SensorLog.timestamp >= start_time
        ).all()
        
        for log in logs:
            hour_key = log.timestamp.replace(minute=0, second=0, microsecond=0)
            if hour_key not in hourly_data:
                hourly_data[hour_key] = {"total": 0, "occupied": 0}
            
            hourly_data[hour_key]["total"] += 1
            if log.occupied:
                hourly_data[hour_key]["occupied"] += 1
        
        # Calculate occupancy rates
        trends = []
        for hour, data in sorted(hourly_data.items()):
            occupancy_rate = (data["occupied"] / data["total"] * 100) if data["total"] > 0 else 0
            trends.append({
                "timestamp": hour.isoformat(),
                "occupancy_rate": occupancy_rate,
                "total_events": data["total"],
                "occupied_events": data["occupied"]
            })
        
        # Calculate daily averages
        daily_averages = {}
        for trend in trends:
            date_key = trend["timestamp"][:10]  # YYYY-MM-DD
            if date_key not in daily_averages:
                daily_averages[date_key] = {"rates": [], "total_events": 0}
            
            daily_averages[date_key]["rates"].append(trend["occupancy_rate"])
            daily_averages[date_key]["total_events"] += trend["total_events"]
        
        daily_summary = []
        for date, data in sorted(daily_averages.items()):
            avg_rate = sum(data["rates"]) / len(data["rates"]) if data["rates"] else 0
            daily_summary.append({
                "date": date,
                "avg_occupancy_rate": avg_rate,
                "total_events": data["total_events"]
            })
        
        return {
            "analysis_period_days": days,
            "hourly_trends": trends,
            "daily_summary": daily_summary,
            "generated_at": end_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating occupancy trends: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/revenue-report")
async def get_revenue_report(
    days: int = Query(30, ge=1, le=365, description="Number of days for revenue report"),
    db: Session = Depends(get_db)
):
    """Generate revenue report"""
    try:
        end_time = utils.get_current_time()
        start_time = end_time - timedelta(days=days)
        
        # Get completed reservations in the period
        reservations = db.query(Reservation).filter(
            Reservation.created_at >= start_time,
            Reservation.status == "completed"
        ).all()
        
        total_revenue = 0.0
        daily_revenue = {}
        hourly_breakdown = {}
        
        for reservation in reservations:
            # Calculate duration and revenue
            duration_hours = (reservation.end_time - reservation.start_time).total_seconds() / 3600
            revenue = duration_hours * 5.0  # $5 per hour
            total_revenue += revenue
            
            # Daily breakdown
            date_key = reservation.created_at.date().isoformat()
            if date_key not in daily_revenue:
                daily_revenue[date_key] = {"revenue": 0.0, "reservations": 0, "total_hours": 0.0}
            
            daily_revenue[date_key]["revenue"] += revenue
            daily_revenue[date_key]["reservations"] += 1
            daily_revenue[date_key]["total_hours"] += duration_hours
            
            # Hourly breakdown
            hour = reservation.created_at.hour
            if hour not in hourly_breakdown:
                hourly_breakdown[hour] = {"revenue": 0.0, "reservations": 0}
            
            hourly_breakdown[hour]["revenue"] += revenue
            hourly_breakdown[hour]["reservations"] += 1
        
        # Format daily data
        daily_data = []
        for date, data in sorted(daily_revenue.items()):
            daily_data.append({
                "date": date,
                "revenue": data["revenue"],
                "reservations": data["reservations"],
                "total_hours": data["total_hours"],
                "avg_revenue_per_reservation": data["revenue"] / data["reservations"] if data["reservations"] > 0 else 0
            })
        
        # Format hourly data
        hourly_data = []
        for hour in range(24):
            data = hourly_breakdown.get(hour, {"revenue": 0.0, "reservations": 0})
            hourly_data.append({
                "hour": hour,
                "revenue": data["revenue"],
                "reservations": data["reservations"]
            })
        
        return {
            "report_period_days": days,
            "summary": {
                "total_revenue": total_revenue,
                "total_reservations": len(reservations),
                "avg_revenue_per_day": total_revenue / days if days > 0 else 0,
                "avg_revenue_per_reservation": total_revenue / len(reservations) if reservations else 0
            },
            "daily_breakdown": daily_data,
            "hourly_breakdown": hourly_data,
            "generated_at": end_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating revenue report: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/maintenance-mode")
async def toggle_maintenance_mode(
    enabled: bool,
    message: str = "System maintenance in progress",
    db: Session = Depends(get_db)
):
    """Toggle maintenance mode for the parking system"""
    try:
        # Log maintenance mode change
        status = "enabled" if enabled else "disabled"
        utils.log_system_event(db, "INFO", f"Maintenance mode {status}: {message}", "admin")
        
        # In a real system, you might update a configuration table
        # For now, we'll just log the event
        
        return {
            "maintenance_mode": enabled,
            "message": message,
            "timestamp": utils.get_current_time().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error toggling maintenance mode: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/system-status")
async def get_system_status(db: Session = Depends(get_db)):
    """Get overall system health status"""
    try:
        current_time = utils.get_current_time()
        
        # Check database connectivity
        try:
            db.execute("SELECT 1")
            db_status = "healthy"
        except:
            db_status = "error"
        
        # Check recent sensor activity
        recent_sensor_logs = db.query(SensorLog).filter(
            SensorLog.timestamp >= current_time - timedelta(minutes=5)
        ).count()
        
        sensor_status = "healthy" if recent_sensor_logs > 0 else "warning"
        
        # Check for recent errors
        recent_errors = db.query(SystemLog).filter(
            SystemLog.level == "ERROR",
            SystemLog.timestamp >= current_time - timedelta(hours=1)
        ).count()
        
        error_status = "healthy" if recent_errors == 0 else "warning"
        
        # Overall status
        if db_status == "error":
            overall_status = "critical"
        elif sensor_status == "warning" or error_status == "warning":
            overall_status = "warning"
        else:
            overall_status = "healthy"
        
        return {
            "overall_status": overall_status,
            "components": {
                "database": db_status,
                "sensors": sensor_status,
                "error_rate": error_status
            },
            "metrics": {
                "recent_sensor_events": recent_sensor_logs,
                "recent_errors": recent_errors,
                "uptime_hours": 24  # Placeholder - would track actual uptime
            },
            "checked_at": current_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error checking system status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
