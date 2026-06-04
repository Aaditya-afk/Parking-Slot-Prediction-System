"""
AI/ML Occupancy Prediction Module for SmartPark Entry/Exit System
Predicts parking occupancy trends based on historical data and time patterns
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import joblib
import logging
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session

from ..models.parking import CarEvent, OccupancyStats, ParkingSlot

logger = logging.getLogger(__name__)

class OccupancyPredictor:
    """ML model for predicting parking occupancy trends"""
    
    def __init__(self):
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.is_trained = False
        self.feature_columns = [
            'hour', 'day_of_week', 'minute', 'is_weekend',
            'current_occupancy', 'entry_events_hour', 'exit_events_hour',
            'occupancy_trend', 'time_since_last_event'
        ]
        self.model_path = "occupancy_model.pkl"
        self.total_slots = 3
        
    def prepare_features(self, timestamp: datetime, current_occupancy: int, 
                        recent_events: List[Dict]) -> np.ndarray:
        """Prepare features for prediction"""
        try:
            # Time-based features
            hour = timestamp.hour
            day_of_week = timestamp.weekday()  # 0=Monday, 6=Sunday
            minute = timestamp.minute
            is_weekend = 1 if day_of_week >= 5 else 0
            
            # Current state
            occupancy_rate = current_occupancy / self.total_slots
            
            # Event-based features
            entry_events_hour = len([e for e in recent_events if e['event_type'] == 'car_entered'])
            exit_events_hour = len([e for e in recent_events if e['event_type'] == 'car_exited'])
            
            # Trend calculation (simple)
            net_change = entry_events_hour - exit_events_hour
            occupancy_trend = 1 if net_change > 0 else (-1 if net_change < 0 else 0)
            
            # Time since last event
            if recent_events:
                last_event_time = max([e['timestamp'] for e in recent_events])
                time_since_last = (timestamp - last_event_time).total_seconds() / 60  # minutes
            else:
                time_since_last = 60  # Default 1 hour
            
            features = np.array([
                hour, day_of_week, minute, is_weekend,
                occupancy_rate, entry_events_hour, exit_events_hour,
                occupancy_trend, time_since_last
            ]).reshape(1, -1)
            
            return features
            
        except Exception as e:
            logger.error(f"❌ Error preparing features: {e}")
            return np.zeros((1, len(self.feature_columns)))
    
    def get_training_data(self, db: Session, days_back: int = 30) -> pd.DataFrame:
        """Extract training data from historical events and occupancy stats"""
        try:
            # Get cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Query occupancy stats if available
            occupancy_stats = db.query(OccupancyStats).filter(
                OccupancyStats.timestamp >= cutoff_date
            ).order_by(OccupancyStats.timestamp).all()
            
            if occupancy_stats:
                # Use existing occupancy stats
                data = []
                for stat in occupancy_stats:
                    data.append({
                        'timestamp': stat.timestamp,
                        'hour': stat.hour,
                        'day_of_week': stat.day_of_week,
                        'occupancy_rate': stat.occupancy_rate,
                        'occupied_slots': stat.occupied_slots,
                        'entry_events_hour': stat.entry_events_hour,
                        'exit_events_hour': stat.exit_events_hour
                    })
                
                df = pd.DataFrame(data)
            else:
                # Generate from car events
                events = db.query(CarEvent).filter(
                    CarEvent.timestamp >= cutoff_date
                ).order_by(CarEvent.timestamp).all()
                
                if not events:
                    logger.warning("⚠️ No training data found")
                    return pd.DataFrame()
                
                df = self._generate_occupancy_from_events(events)
            
            if df.empty:
                return df
            
            # Create training features
            training_data = self._create_training_features(df)
            
            logger.info(f"✅ Prepared {len(training_data)} training samples from {days_back} days of data")
            return training_data
            
        except Exception as e:
            logger.error(f"❌ Error getting training data: {e}")
            return pd.DataFrame()
    
    def _generate_occupancy_from_events(self, events: List) -> pd.DataFrame:
        """Generate occupancy data from car events"""
        try:
            # Create hourly occupancy data
            data = []
            current_occupancy = 0
            
            # Group events by hour
            events_by_hour = {}
            for event in events:
                hour_key = event.timestamp.replace(minute=0, second=0, microsecond=0)
                if hour_key not in events_by_hour:
                    events_by_hour[hour_key] = []
                events_by_hour[hour_key].append(event)
            
            # Process each hour
            for hour_timestamp, hour_events in sorted(events_by_hour.items()):
                entry_count = len([e for e in hour_events if e.event_type == 'car_entered'])
                exit_count = len([e for e in hour_events if e.event_type == 'car_exited'])
                
                # Update occupancy (simplified logic)
                current_occupancy += entry_count - exit_count
                current_occupancy = max(0, min(self.total_slots, current_occupancy))
                
                data.append({
                    'timestamp': hour_timestamp,
                    'hour': hour_timestamp.hour,
                    'day_of_week': hour_timestamp.weekday(),
                    'occupancy_rate': current_occupancy / self.total_slots * 100,
                    'occupied_slots': current_occupancy,
                    'entry_events_hour': entry_count,
                    'exit_events_hour': exit_count
                })
            
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"❌ Error generating occupancy from events: {e}")
            return pd.DataFrame()
    
    def _create_training_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create training features and targets"""
        try:
            training_samples = []
            
            for i in range(len(df) - 1):  # Exclude last row (no future to predict)
                current_row = df.iloc[i]
                future_row = df.iloc[i + 1]  # Next hour
                
                # Current features
                features = {
                    'hour': current_row['hour'],
                    'day_of_week': current_row['day_of_week'],
                    'minute': 0,  # Hourly data
                    'is_weekend': 1 if current_row['day_of_week'] >= 5 else 0,
                    'current_occupancy': current_row['occupancy_rate'] / 100,
                    'entry_events_hour': current_row['entry_events_hour'],
                    'exit_events_hour': current_row['exit_events_hour'],
                    'occupancy_trend': 1 if current_row['entry_events_hour'] > current_row['exit_events_hour'] else -1,
                    'time_since_last_event': 30  # Default 30 minutes for hourly data
                }
                
                # Target (future occupancy rate)
                features['target_occupancy'] = future_row['occupancy_rate'] / 100
                
                training_samples.append(features)
            
            return pd.DataFrame(training_samples)
            
        except Exception as e:
            logger.error(f"❌ Error creating training features: {e}")
            return pd.DataFrame()
    
    def train_model(self, db: Session, days_back: int = 30) -> Tuple[bool, str]:
        """Train the ML model with historical data"""
        try:
            # Get training data
            training_data = self.get_training_data(db, days_back)
            
            if training_data.empty:
                return False, "No training data available"
            
            if len(training_data) < 24:  # At least 24 hours of data
                return False, f"Insufficient training data: {len(training_data)} samples (minimum 24 required)"
            
            # Prepare features and targets
            X = training_data[self.feature_columns]
            y = training_data['target_occupancy']
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Train model
            self.model.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = self.model.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            # Save model
            joblib.dump(self.model, self.model_path)
            self.is_trained = True
            
            logger.info(f"✅ Model trained successfully - MAE: {mae:.3f}, R²: {r2:.3f}")
            
            return True, f"Model trained with {len(training_data)} samples, MAE: {mae:.3f}, R²: {r2:.3f}"
            
        except Exception as e:
            logger.error(f"❌ Error training model: {e}")
            return False, f"Training failed: {str(e)}"
    
    def load_model(self) -> bool:
        """Load pre-trained model"""
        try:
            import os
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                self.is_trained = True
                logger.info("✅ Model loaded successfully")
                return True
            else:
                logger.warning("⚠️ No pre-trained model found")
                return False
        except Exception as e:
            logger.error(f"❌ Error loading model: {e}")
            return False
    
    def predict_occupancy(
        self, 
        db: Session, 
        hours_ahead: int = 1
    ) -> Dict[str, any]:
        """Predict occupancy for the next X hours"""
        try:
            if not self.is_trained:
                if not self.load_model():
                    return {
                        "prediction": "unknown",
                        "confidence": "low",
                        "error": "Model not trained"
                    }
            
            # Get current state
            current_occupancy = self._get_current_occupancy(db)
            recent_events = self._get_recent_events(db, hours=1)
            
            predictions = []
            
            for hour in range(1, hours_ahead + 1):
                # Prepare features for prediction time
                prediction_time = datetime.utcnow() + timedelta(hours=hour)
                features = self.prepare_features(prediction_time, current_occupancy, recent_events)
                
                # Make prediction
                predicted_occupancy_rate = self.model.predict(features)[0]
                predicted_occupancy_rate = max(0, min(1, predicted_occupancy_rate))  # Clamp to [0,1]
                
                predicted_slots = round(predicted_occupancy_rate * self.total_slots)
                
                # Determine confidence based on model certainty
                confidence = "high" if abs(predicted_occupancy_rate - 0.5) > 0.3 else "medium" if abs(predicted_occupancy_rate - 0.5) > 0.15 else "low"
                
                predictions.append({
                    "hour": hour,
                    "prediction_time": prediction_time.isoformat(),
                    "predicted_occupancy_rate": round(predicted_occupancy_rate * 100, 1),
                    "predicted_occupied_slots": predicted_slots,
                    "predicted_free_slots": self.total_slots - predicted_slots,
                    "confidence": confidence
                })
            
            return {
                "success": True,
                "current_occupancy": current_occupancy,
                "total_slots": self.total_slots,
                "predictions": predictions,
                "model_info": {
                    "is_trained": self.is_trained,
                    "prediction_horizon": f"{hours_ahead} hours"
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error predicting occupancy: {e}")
            return {
                "success": False,
                "error": str(e),
                "prediction": "unknown",
                "confidence": "low"
            }
    
    def get_occupancy_insights(self, db: Session) -> Dict[str, any]:
        """Get AI-powered occupancy insights"""
        try:
            # Get predictions for next few hours
            predictions = self.predict_occupancy(db, hours_ahead=4)
            
            if not predictions.get("success"):
                return {"error": "Unable to generate insights"}
            
            current_hour = datetime.utcnow().hour
            
            # Analyze trends
            pred_data = predictions["predictions"]
            current_occupancy = predictions["current_occupancy"]
            
            # Find best time to visit
            best_hour_idx = min(range(len(pred_data)), key=lambda i: pred_data[i]["predicted_occupied_slots"])
            best_time = pred_data[best_hour_idx]
            
            # Determine trend
            if len(pred_data) >= 2:
                trend_direction = "increasing" if pred_data[1]["predicted_occupied_slots"] > pred_data[0]["predicted_occupied_slots"] else "decreasing"
            else:
                trend_direction = "stable"
            
            # Peak time analysis
            peak_hours = [8, 9, 12, 13, 17, 18]  # Typical peak hours
            is_peak_time = current_hour in peak_hours
            
            # Generate insights
            insights = {
                "current_status": {
                    "occupied_slots": current_occupancy,
                    "free_slots": self.total_slots - current_occupancy,
                    "occupancy_rate": round((current_occupancy / self.total_slots) * 100, 1),
                    "is_peak_time": is_peak_time
                },
                "trend_analysis": {
                    "direction": trend_direction,
                    "confidence": "medium"  # Could be improved with more sophisticated analysis
                },
                "recommendations": {
                    "best_time_next_4h": {
                        "hour": best_time["hour"],
                        "time": best_time["prediction_time"],
                        "expected_free_slots": best_time["predicted_free_slots"]
                    },
                    "avoid_peak": is_peak_time,
                    "message": self._generate_recommendation_message(current_occupancy, trend_direction, is_peak_time)
                },
                "predictions": pred_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"❌ Error generating insights: {e}")
            return {"error": str(e)}
    
    def _get_current_occupancy(self, db: Session) -> int:
        """Get current number of occupied slots"""
        try:
            occupied_count = db.query(ParkingSlot).filter(
                ParkingSlot.status == "occupied"
            ).count()
            return occupied_count
        except Exception as e:
            logger.error(f"❌ Error getting current occupancy: {e}")
            return 0
    
    def _get_recent_events(self, db: Session, hours: int = 1) -> List[Dict]:
        """Get recent car events"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            events = db.query(CarEvent).filter(
                CarEvent.timestamp >= cutoff_time
            ).all()
            
            return [
                {
                    "event_type": event.event_type,
                    "timestamp": event.timestamp
                }
                for event in events
            ]
        except Exception as e:
            logger.error(f"❌ Error getting recent events: {e}")
            return []
    
    def _generate_recommendation_message(self, current_occupancy: int, trend: str, is_peak: bool) -> str:
        """Generate human-readable recommendation message"""
        if current_occupancy == 0:
            return "Great time to visit! All slots are currently free."
        elif current_occupancy == self.total_slots:
            if trend == "decreasing":
                return "Parking is full now, but occupancy is expected to decrease soon."
            else:
                return "Parking is currently full. Consider visiting during off-peak hours."
        else:
            if trend == "increasing" and is_peak:
                return f"{self.total_slots - current_occupancy} slots available, but filling up quickly during peak hours."
            elif trend == "decreasing":
                return f"{self.total_slots - current_occupancy} slots available and more expected to free up soon."
            else:
                return f"{self.total_slots - current_occupancy} slots currently available."
    
    def update_occupancy_stats(self, db: Session):
        """Update hourly occupancy statistics for ML training"""
        try:
            current_time = datetime.utcnow()
            current_hour = current_time.replace(minute=0, second=0, microsecond=0)
            
            # Check if stats already exist for this hour
            existing_stat = db.query(OccupancyStats).filter(
                OccupancyStats.timestamp == current_hour
            ).first()
            
            if existing_stat:
                return  # Already recorded
            
            # Get current slot stats
            total_slots = db.query(ParkingSlot).count()
            occupied_slots = db.query(ParkingSlot).filter(ParkingSlot.status == "occupied").count()
            free_slots = db.query(ParkingSlot).filter(ParkingSlot.status == "free").count()
            reserved_slots = db.query(ParkingSlot).filter(ParkingSlot.status == "reserved").count()
            
            occupancy_rate = (occupied_slots / total_slots * 100) if total_slots > 0 else 0
            
            # Get events for this hour
            hour_start = current_hour
            hour_end = current_hour + timedelta(hours=1)
            
            entry_events = db.query(CarEvent).filter(
                CarEvent.timestamp >= hour_start,
                CarEvent.timestamp < hour_end,
                CarEvent.event_type == "car_entered"
            ).count()
            
            exit_events = db.query(CarEvent).filter(
                CarEvent.timestamp >= hour_start,
                CarEvent.timestamp < hour_end,
                CarEvent.event_type == "car_exited"
            ).count()
            
            # Create occupancy stat
            stat = OccupancyStats(
                timestamp=current_hour,
                hour=current_hour.hour,
                day_of_week=current_hour.weekday(),
                total_slots=total_slots,
                occupied_slots=occupied_slots,
                free_slots=free_slots,
                reserved_slots=reserved_slots,
                occupancy_rate=occupancy_rate,
                entry_events_hour=entry_events,
                exit_events_hour=exit_events
            )
            
            db.add(stat)
            db.commit()
            
            logger.info(f"📊 Updated occupancy stats for {current_hour}")
            
        except Exception as e:
            logger.error(f"❌ Error updating occupancy stats: {e}")
            db.rollback()

# Global predictor instance
predictor = OccupancyPredictor()
