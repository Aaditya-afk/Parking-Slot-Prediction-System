"""
Machine Learning Module for Parking Availability Prediction
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.preprocessing import StandardScaler
import joblib
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from models import SensorLog, Slot, Reservation
import utils

logger = logging.getLogger(__name__)

class MLPredictor:
    """Machine Learning predictor for parking availability"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = "ml_model.pkl"
        self.scaler_path = "ml_scaler.pkl"
        self.is_trained = False
        self.model_info = {
            "algorithm": "RandomForest",
            "trained_at": None,
            "accuracy": None,
            "features": [
                "hour_of_day",
                "day_of_week", 
                "is_weekend",
                "occupancy_rate_1h",
                "occupancy_rate_24h",
                "active_reservations",
                "recent_activity"
            ]
        }
        
        # Load existing model if available
        self._load_model()
    
    def _load_model(self):
        """Load trained model from disk"""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                self.is_trained = True
                logger.info("Loaded existing ML model")
            else:
                logger.info("No existing model found, will need to train")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self.model = None
            self.scaler = StandardScaler()
            self.is_trained = False
    
    def _save_model(self):
        """Save trained model to disk"""
        try:
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            logger.info("Model saved successfully")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def _extract_features(self, db: Session, slot_id: int, target_time: datetime) -> np.array:
        """Extract features for prediction"""
        try:
            # Time-based features
            hour_of_day = target_time.hour
            day_of_week = target_time.weekday()
            is_weekend = 1 if day_of_week >= 5 else 0
            
            # Historical occupancy features
            one_hour_ago = target_time - timedelta(hours=1)
            one_day_ago = target_time - timedelta(hours=24)
            
            # Get recent sensor logs for this slot
            recent_logs_1h = db.query(SensorLog).filter(
                SensorLog.slot_id == slot_id,
                SensorLog.timestamp >= one_hour_ago,
                SensorLog.timestamp <= target_time
            ).all()
            
            recent_logs_24h = db.query(SensorLog).filter(
                SensorLog.slot_id == slot_id,
                SensorLog.timestamp >= one_day_ago,
                SensorLog.timestamp <= target_time
            ).all()
            
            # Calculate occupancy rates
            occupancy_rate_1h = 0.0
            if recent_logs_1h:
                occupied_count_1h = sum(1 for log in recent_logs_1h if log.occupied)
                occupancy_rate_1h = occupied_count_1h / len(recent_logs_1h)
            
            occupancy_rate_24h = 0.0
            if recent_logs_24h:
                occupied_count_24h = sum(1 for log in recent_logs_24h if log.occupied)
                occupancy_rate_24h = occupied_count_24h / len(recent_logs_24h)
            
            # Active reservations at target time
            active_reservations = db.query(Reservation).filter(
                Reservation.slot_id == slot_id,
                Reservation.status == "active",
                Reservation.start_time <= target_time,
                Reservation.end_time > target_time
            ).count()
            
            # Recent activity (events in last 30 minutes)
            thirty_min_ago = target_time - timedelta(minutes=30)
            recent_activity = db.query(SensorLog).filter(
                SensorLog.slot_id == slot_id,
                SensorLog.timestamp >= thirty_min_ago,
                SensorLog.timestamp <= target_time
            ).count()
            
            features = np.array([
                hour_of_day,
                day_of_week,
                is_weekend,
                occupancy_rate_1h,
                occupancy_rate_24h,
                active_reservations,
                recent_activity
            ])
            
            return features.reshape(1, -1)
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            # Return default features
            return np.array([12, 1, 0, 0.5, 0.5, 0, 0]).reshape(1, -1)
    
    def _prepare_training_data(self, db: Session, days: int = 30) -> tuple:
        """Prepare training data from historical sensor logs"""
        try:
            end_time = utils.get_current_time()
            start_time = end_time - timedelta(days=days)
            
            # Get all sensor logs in the training period
            logs = db.query(SensorLog).filter(
                SensorLog.timestamp >= start_time,
                SensorLog.timestamp <= end_time
            ).order_by(SensorLog.timestamp).all()
            
            if len(logs) < 100:  # Need minimum data
                return None, None
            
            features_list = []
            labels_list = []
            
            # Create training samples
            for i, log in enumerate(logs):
                if i < 50:  # Skip first 50 to have enough history
                    continue
                
                # Extract features at this timestamp
                features = self._extract_features(db, log.slot_id, log.timestamp)
                
                # Label is whether the slot becomes free in the next hour
                future_time = log.timestamp + timedelta(hours=1)
                
                # Find the next log entry after future_time
                future_logs = [l for l in logs if l.slot_id == log.slot_id and l.timestamp > future_time]
                
                if future_logs:
                    # Use the first log after future_time
                    next_log = min(future_logs, key=lambda x: x.timestamp)
                    label = 1 if not next_log.occupied else 0  # 1 = free, 0 = occupied
                else:
                    # If no future data, skip this sample
                    continue
                
                features_list.append(features.flatten())
                labels_list.append(label)
            
            if len(features_list) < 50:
                return None, None
            
            X = np.array(features_list)
            y = np.array(labels_list)
            
            logger.info(f"Prepared {len(X)} training samples")
            return X, y
            
        except Exception as e:
            logger.error(f"Error preparing training data: {e}")
            return None, None
    
    def train_model(self, db: Session, days: int = 30) -> tuple[bool, str]:
        """Train the ML model"""
        try:
            logger.info("Starting ML model training...")
            
            # Prepare training data
            X, y = self._prepare_training_data(db, days)
            
            if X is None or len(X) < 50:
                return False, "Insufficient training data (need at least 50 samples)"
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train Random Forest model
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )
            
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = self.model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred, average='weighted')
            recall = recall_score(y_test, y_pred, average='weighted')
            f1 = f1_score(y_test, y_pred, average='weighted')
            
            # Update model info
            self.model_info.update({
                "trained_at": utils.get_current_time().isoformat(),
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1_score": f1,
                "training_samples": len(X),
                "test_samples": len(X_test)
            })
            
            self.is_trained = True
            
            # Save model
            self._save_model()
            
            message = f"Model trained successfully. Accuracy: {accuracy:.3f}, F1: {f1:.3f}"
            logger.info(message)
            
            return True, message
            
        except Exception as e:
            error_msg = f"Model training failed: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def predict_availability(self, db: Session, slot_id: int, horizon_minutes: int) -> float:
        """Predict probability that a slot will be free after horizon_minutes"""
        try:
            if not self.is_trained or self.model is None:
                # Use simple baseline prediction
                return self._baseline_prediction(db, slot_id, horizon_minutes)
            
            # Calculate target time
            current_time = utils.get_current_time()
            target_time = current_time + timedelta(minutes=horizon_minutes)
            
            # Extract features
            features = self._extract_features(db, slot_id, target_time)
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Get prediction probability
            probabilities = self.model.predict_proba(features_scaled)
            
            # Return probability of being free (class 1)
            if len(probabilities[0]) > 1:
                return float(probabilities[0][1])
            else:
                return 0.5  # Default if model has issues
            
        except Exception as e:
            logger.error(f"Error in ML prediction: {e}")
            return self._baseline_prediction(db, slot_id, horizon_minutes)
    
    def _baseline_prediction(self, db: Session, slot_id: int, horizon_minutes: int) -> float:
        """Simple baseline prediction based on historical averages"""
        try:
            current_time = utils.get_current_time()
            target_time = current_time + timedelta(minutes=horizon_minutes)
            
            # Get historical data for same hour and day of week
            target_hour = target_time.hour
            target_dow = target_time.weekday()
            
            # Look at past 30 days
            start_time = current_time - timedelta(days=30)
            
            similar_logs = db.query(SensorLog).filter(
                SensorLog.slot_id == slot_id,
                SensorLog.timestamp >= start_time
            ).all()
            
            # Filter for similar time periods
            matching_logs = []
            for log in similar_logs:
                if (log.timestamp.hour == target_hour and 
                    log.timestamp.weekday() == target_dow):
                    matching_logs.append(log)
            
            if not matching_logs:
                # No historical data, return neutral probability
                return 0.5
            
            # Calculate probability based on historical free rate
            free_count = sum(1 for log in matching_logs if not log.occupied)
            probability = free_count / len(matching_logs)
            
            return float(probability)
            
        except Exception as e:
            logger.error(f"Error in baseline prediction: {e}")
            return 0.5
    
    def evaluate_model(self, db: Session, days: int = 7) -> dict:
        """Evaluate model accuracy on recent data"""
        try:
            if not self.is_trained:
                return {"error": "Model not trained"}
            
            # Get recent data for evaluation
            end_time = utils.get_current_time()
            start_time = end_time - timedelta(days=days)
            
            logs = db.query(SensorLog).filter(
                SensorLog.timestamp >= start_time,
                SensorLog.timestamp <= end_time
            ).order_by(SensorLog.timestamp).all()
            
            if len(logs) < 20:
                return {"error": "Insufficient evaluation data"}
            
            correct_predictions = 0
            total_predictions = 0
            
            # Test predictions on historical data
            for i, log in enumerate(logs[:-10]):  # Leave some buffer
                try:
                    # Predict 30 minutes ahead
                    prediction_prob = self.predict_availability(db, log.slot_id, 30)
                    predicted_free = prediction_prob > 0.5
                    
                    # Find actual state 30 minutes later
                    future_time = log.timestamp + timedelta(minutes=30)
                    future_logs = [l for l in logs if 
                                 l.slot_id == log.slot_id and 
                                 l.timestamp >= future_time]
                    
                    if future_logs:
                        actual_free = not future_logs[0].occupied
                        
                        if predicted_free == actual_free:
                            correct_predictions += 1
                        total_predictions += 1
                        
                except Exception:
                    continue
            
            if total_predictions == 0:
                return {"error": "No valid predictions made"}
            
            accuracy = correct_predictions / total_predictions
            
            return {
                "accuracy": accuracy,
                "correct_predictions": correct_predictions,
                "total_predictions": total_predictions,
                "evaluation_period_days": days
            }
            
        except Exception as e:
            logger.error(f"Error evaluating model: {e}")
            return {"error": str(e)}
    
    def get_model_info(self) -> dict:
        """Get information about the current model"""
        info = self.model_info.copy()
        info["is_trained"] = self.is_trained
        info["model_exists"] = os.path.exists(self.model_path)
        return info

# Training script
def train_model_script():
    """Standalone script to train the model"""
    from database import SessionLocal
    
    db = SessionLocal()
    try:
        predictor = MLPredictor()
        success, message = predictor.train_model(db)
        
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
            
    finally:
        db.close()

if __name__ == "__main__":
    train_model_script()
