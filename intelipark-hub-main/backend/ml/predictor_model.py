"""
ML Model for Parking Slot Availability Prediction
Uses Random Forest and LSTM for spatio-temporal predictions
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class ParkingPredictor:
    """ML model for predicting parking slot availability"""
    
    def __init__(self):
        self.model = None
        self.feature_columns = None
        
    def prepare_features(self, df: pd.DataFrame) -> tuple:
        """Prepare features and target for training"""
        # Feature columns
        feature_cols = [
            'slot_id', 'hour', 'day_of_week', 'is_weekend', 'is_peak_hour',
            'occupied_lag_1', 'occupied_lag_2', 'occupied_rolling_mean_4',
            'hour_sin', 'hour_cos', 'zone_A', 'zone_B', 'zone_C'
        ]
        
        # Remove rows with NaN (from lag features)
        df_clean = df.dropna()
        
        X = df_clean[feature_cols]
        y = df_clean['occupied']
        
        self.feature_columns = feature_cols
        
        return X, y
    
    def train(self, df: pd.DataFrame):
        """Train Random Forest model"""
        print("🧠 Training ML model...")
        
        X, y = self.prepare_features(df)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train Random Forest
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"✅ Model trained successfully!")
        print(f"📊 Accuracy: {accuracy:.2%}")
        print(f"📈 Training samples: {len(X_train)}")
        print(f"🧪 Test samples: {len(X_test)}")
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\n🔍 Top 5 Important Features:")
        print(feature_importance.head())
        
        return accuracy
    
    def predict_slot(self, slot_id: int, minutes_ahead: int = 15) -> dict:
        """Predict if a slot will be available in X minutes"""
        if self.model is None:
            raise ValueError("Model not trained yet!")
        
        # Create feature vector for prediction
        future_time = datetime.now() + timedelta(minutes=minutes_ahead)
        hour = future_time.hour
        day_of_week = future_time.weekday()
        
        # Simulate recent occupancy (in real system, fetch from database)
        occupied_lag_1 = np.random.randint(0, 2)
        occupied_lag_2 = np.random.randint(0, 2)
        occupied_rolling_mean = np.random.uniform(0, 1)
        
        # Determine zone
        zone = 'A' if slot_id <= 24 else 'B' if slot_id <= 48 else 'C'
        
        features = {
            'slot_id': slot_id,
            'hour': hour,
            'day_of_week': day_of_week,
            'is_weekend': 1 if day_of_week >= 5 else 0,
            'is_peak_hour': 1 if (9 <= hour <= 11) or (17 <= hour <= 19) else 0,
            'occupied_lag_1': occupied_lag_1,
            'occupied_lag_2': occupied_lag_2,
            'occupied_rolling_mean_4': occupied_rolling_mean,
            'hour_sin': np.sin(2 * np.pi * hour / 24),
            'hour_cos': np.cos(2 * np.pi * hour / 24),
            'zone_A': 1 if zone == 'A' else 0,
            'zone_B': 1 if zone == 'B' else 0,
            'zone_C': 1 if zone == 'C' else 0
        }
        
        # Create DataFrame
        X = pd.DataFrame([features])[self.feature_columns]
        
        # Predict
        prediction = self.model.predict(X)[0]
        probability = self.model.predict_proba(X)[0]
        
        return {
            'slot_id': slot_id,
            'minutes_ahead': minutes_ahead,
            'predicted_occupied': int(prediction),
            'predicted_available': int(1 - prediction),
            'probability_occupied': round(float(probability[1]), 3),
            'probability_available': round(float(probability[0]), 3),
            'confidence': 'high' if max(probability) > 0.75 else 'medium' if max(probability) > 0.6 else 'low',
            'timestamp': datetime.now().isoformat()
        }
    
    def predict_all_slots(self, num_slots=70, minutes_ahead=15) -> list:
        """Predict availability for all slots"""
        predictions = []
        for slot_id in range(1, num_slots + 1):
            pred = self.predict_slot(slot_id, minutes_ahead)
            predictions.append(pred)
        return predictions
    
    def save_model(self, filename='parking_model.pkl'):
        """Save trained model"""
        if self.model is None:
            raise ValueError("No model to save!")
        
        joblib.dump({
            'model': self.model,
            'feature_columns': self.feature_columns
        }, filename)
        print(f"💾 Model saved: {filename}")
    
    def load_model(self, filename='parking_model.pkl'):
        """Load trained model"""
        data = joblib.load(filename)
        self.model = data['model']
        self.feature_columns = data['feature_columns']
        print(f"📂 Model loaded: {filename}")

# ==================== TRAINING SCRIPT ====================

def train_and_save_model():
    """Complete training pipeline"""
    from dataset_generator import ParkingDatasetGenerator
    
    # Generate dataset
    print("=" * 60)
    print("🚀 Starting ML Model Training Pipeline")
    print("=" * 60)
    
    generator = ParkingDatasetGenerator(num_slots=70, days=30)
    df = generator.generate_dataset()
    df = generator.add_features(df)
    
    # Train model
    predictor = ParkingPredictor()
    accuracy = predictor.train(df)
    
    # Save model
    predictor.save_model('parking_model.pkl')
    
    # Test predictions
    print("\n" + "=" * 60)
    print("🧪 Testing Predictions")
    print("=" * 60)
    
    for slot_id in [1, 25, 50, 70]:
        pred = predictor.predict_slot(slot_id, minutes_ahead=15)
        print(f"\n📍 Slot {slot_id}:")
        print(f"   Predicted: {'OCCUPIED' if pred['predicted_occupied'] else 'AVAILABLE'}")
        print(f"   Confidence: {pred['probability_available']:.1%} available")
        print(f"   Level: {pred['confidence']}")
    
    print("\n" + "=" * 60)
    print("✅ Training Complete!")
    print("=" * 60)
    
    return predictor

if __name__ == "__main__":
    predictor = train_and_save_model()
