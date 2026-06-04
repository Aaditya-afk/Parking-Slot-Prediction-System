"""
ML Prediction Module for SmartPark
Forecasts parking occupancy based on historical data and time patterns
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import logging
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session

from ..models.slots import SlotLog, ParkingSlot

logger = logging.getLogger(__name__)

class ParkingPredictor:
    """ML model for predicting parking slot availability"""
    
    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.is_trained = False
        self.feature_columns = [
            'hour', 'day_of_week', 'minute', 'is_weekend',
            'slot1_current', 'slot2_current', 'slot3_current',
            'total_occupied', 'occupancy_rate'
        ]
        self.model_path = "parking_model.pkl"
        
    def prepare_features(self, timestamp: datetime, current_slots: Dict[str, bool]) -> np.ndarray:
        """Prepare features for prediction"""
        try:
            # Time-based features
            hour = timestamp.hour
            day_of_week = timestamp.weekday()  # 0=Monday, 6=Sunday
            minute = timestamp.minute
            is_weekend = 1 if day_of_week >= 5 else 0
            
            # Current slot states (1=occupied, 0=free)
            slot1_current = 1 if current_slots.get('slot1', False) else 0
            slot2_current = 1 if current_slots.get('slot2', False) else 0
            slot3_current = 1 if current_slots.get('slot3', False) else 0
            
            # Occupancy metrics
            total_occupied = slot1_current + slot2_current + slot3_current
            occupancy_rate = total_occupied / 3.0
            
            features = np.array([
                hour, day_of_week, minute, is_weekend,
                slot1_current, slot2_current, slot3_current,
                total_occupied, occupancy_rate
            ]).reshape(1, -1)
            
            return features
            
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            return np.zeros((1, len(self.feature_columns)))
    
    def get_training_data(self, db: Session, days_back: int = 30) -> pd.DataFrame:
        """Extract training data from slot logs"""
        try:
            # Get cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Query slot logs
            logs = db.query(SlotLog).filter(
                SlotLog.change_timestamp >= cutoff_date
            ).order_by(SlotLog.change_timestamp).all()
            
            if not logs:
                logger.warning("No training data found")
                return pd.DataFrame()
            
            # Convert to DataFrame
            data = []
            for log in logs:
                data.append({
                    'timestamp': log.change_timestamp,
                    'slot_number': log.slot_number,
                    'new_state': log.new_state,
                    'previous_state': log.previous_state
                })
            
            df = pd.DataFrame(data)
            
            if df.empty:
                return df
            
            # Create time-series data with features
            training_data = self._create_time_series_features(df)
            
            logger.info(f"Prepared {len(training_data)} training samples from {days_back} days of data")
            return training_data
            
        except Exception as e:
            logger.error(f"Error getting training data: {e}")
            return pd.DataFrame()
    
    def _create_time_series_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create time-series features for training"""
        try:
            # Sort by timestamp
            df = df.sort_values('timestamp')
            
            # Create time-based features
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            df['minute'] = df['timestamp'].dt.minute
            df['is_weekend'] = (df['timestamp'].dt.dayofweek >= 5).astype(int)
            
            # Group by timestamp to get slot states at each time point
            time_points = df['timestamp'].unique()
            training_samples = []
            
            for i, timestamp in enumerate(time_points[:-1]):  # Exclude last point (no future to predict)
                # Get current state at this timestamp
                current_logs = df[df['timestamp'] == timestamp]
                
                # Initialize slot states (assume all free initially)
                slot_states = {'slot1': False, 'slot2': False, 'slot3': False}
                
                # Update with actual states from logs
                for _, log in current_logs.iterrows():
                    slot_states[log['slot_number']] = log['new_state']
                
                # Get future state (target) - look ahead 15 minutes
                future_timestamp = timestamp + timedelta(minutes=15)
                future_logs = df[
                    (df['timestamp'] > timestamp) & 
                    (df['timestamp'] <= future_timestamp)
                ]
                
                # Predict each slot's future state
                for slot_num in ['slot1', 'slot2', 'slot3']:
                    # Get current features
                    features = self._extract_features_for_timestamp(timestamp, slot_states)
                    
                    # Get target (future state)
                    slot_future_logs = future_logs[future_logs['slot_number'] == slot_num]
                    if not slot_future_logs.empty:
                        # Use the latest state change within the prediction window
                        target = slot_future_logs.iloc[-1]['new_state']
                    else:
                        # No change, assume current state continues
                        target = slot_states[slot_num]
                    
                    # Add to training data
                    sample = features.copy()
                    sample['target_slot'] = slot_num
                    sample['target_occupied'] = target
                    training_samples.append(sample)
            
            return pd.DataFrame(training_samples)
            
        except Exception as e:
            logger.error(f"Error creating time-series features: {e}")
            return pd.DataFrame()
    
    def _extract_features_for_timestamp(self, timestamp: datetime, slot_states: Dict[str, bool]) -> Dict:
        """Extract features for a specific timestamp"""
        return {
            'hour': timestamp.hour,
            'day_of_week': timestamp.weekday(),
            'minute': timestamp.minute,
            'is_weekend': 1 if timestamp.weekday() >= 5 else 0,
            'slot1_current': 1 if slot_states['slot1'] else 0,
            'slot2_current': 1 if slot_states['slot2'] else 0,
            'slot3_current': 1 if slot_states['slot3'] else 0,
            'total_occupied': sum(1 for occupied in slot_states.values() if occupied),
            'occupancy_rate': sum(1 for occupied in slot_states.values() if occupied) / 3.0
        }
    
    def train_model(self, db: Session, days_back: int = 30) -> Tuple[bool, str]:
        """Train the ML model with historical data"""
        try:
            # Get training data
            training_data = self.get_training_data(db, days_back)
            
            if training_data.empty:
                return False, "No training data available"
            
            if len(training_data) < 50:
                return False, f"Insufficient training data: {len(training_data)} samples (minimum 50 required)"
            
            # Prepare features and targets
            X = training_data[self.feature_columns]
            y = training_data['target_occupied'].astype(int)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Train model
            self.model.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = self.model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Save model
            joblib.dump(self.model, self.model_path)
            self.is_trained = True
            
            logger.info(f"Model trained successfully with accuracy: {accuracy:.3f}")
            
            return True, f"Model trained with {len(training_data)} samples, accuracy: {accuracy:.3f}"
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            return False, f"Training failed: {str(e)}"
    
    def load_model(self) -> bool:
        """Load pre-trained model"""
        try:
            import os
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                self.is_trained = True
                logger.info("Model loaded successfully")
                return True
            else:
                logger.warning("No pre-trained model found")
                return False
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def predict_slot_availability(
        self, 
        db: Session, 
        slot_number: str, 
        minutes_ahead: int = 15
    ) -> Dict[str, any]:
        """Predict if a specific slot will be available in X minutes"""
        try:
            if not self.is_trained:
                if not self.load_model():
                    return {
                        "slot_number": slot_number,
                        "prediction": "unknown",
                        "probability": 0.5,
                        "confidence": "low",
                        "error": "Model not trained"
                    }
            
            # Get current slot states
            current_slots = self._get_current_slot_states(db)
            
            # Prepare features for prediction time
            prediction_time = datetime.utcnow() + timedelta(minutes=minutes_ahead)
            features = self.prepare_features(prediction_time, current_slots)
            
            # Make prediction
            probability_occupied = self.model.predict_proba(features)[0][1]  # Probability of being occupied
            probability_free = 1 - probability_occupied
            
            # Determine confidence level
            confidence = "high" if abs(probability_free - 0.5) > 0.3 else "medium" if abs(probability_free - 0.5) > 0.15 else "low"
            
            # Prediction result
            prediction = "free" if probability_free > 0.5 else "occupied"
            
            return {
                "slot_number": slot_number,
                "prediction": prediction,
                "probability_free": round(probability_free, 3),
                "probability_occupied": round(probability_occupied, 3),
                "confidence": confidence,
                "minutes_ahead": minutes_ahead,
                "prediction_time": prediction_time.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error predicting slot availability: {e}")
            return {
                "slot_number": slot_number,
                "prediction": "unknown",
                "probability": 0.5,
                "confidence": "low",
                "error": str(e)
            }
    
    def predict_all_slots(self, db: Session, minutes_ahead: int = 15) -> List[Dict]:
        """Predict availability for all slots"""
        predictions = []
        for slot_num in ['slot1', 'slot2', 'slot3']:
            prediction = self.predict_slot_availability(db, slot_num, minutes_ahead)
            predictions.append(prediction)
        return predictions
    
    def _get_current_slot_states(self, db: Session) -> Dict[str, bool]:
        """Get current state of all slots"""
        try:
            slots = db.query(ParkingSlot).all()
            current_states = {}
            
            for slot in slots:
                current_states[slot.slot_number] = slot.is_occupied
            
            # Ensure all slots are represented
            for slot_num in ['slot1', 'slot2', 'slot3']:
                if slot_num not in current_states:
                    current_states[slot_num] = False
            
            return current_states
            
        except Exception as e:
            logger.error(f"Error getting current slot states: {e}")
            return {'slot1': False, 'slot2': False, 'slot3': False}
    
    def get_occupancy_forecast(self, db: Session, hours_ahead: int = 2) -> Dict[str, any]:
        """Get occupancy forecast for the next few hours"""
        try:
            forecasts = []
            current_time = datetime.utcnow()
            
            # Generate predictions for every 15 minutes for the next X hours
            for minutes in range(15, hours_ahead * 60 + 1, 15):
                predictions = self.predict_all_slots(db, minutes)
                
                # Calculate overall occupancy
                total_occupied = sum(1 for p in predictions if p['prediction'] == 'occupied')
                occupancy_rate = total_occupied / 3.0
                
                forecasts.append({
                    "time": (current_time + timedelta(minutes=minutes)).isoformat(),
                    "minutes_ahead": minutes,
                    "predicted_occupied_slots": total_occupied,
                    "predicted_free_slots": 3 - total_occupied,
                    "predicted_occupancy_rate": round(occupancy_rate * 100, 1),
                    "slot_predictions": predictions
                })
            
            return {
                "forecast_generated_at": current_time.isoformat(),
                "forecast_horizon_hours": hours_ahead,
                "forecasts": forecasts
            }
            
        except Exception as e:
            logger.error(f"Error generating occupancy forecast: {e}")
            return {"error": str(e)}

# Global predictor instance
predictor = ParkingPredictor()
