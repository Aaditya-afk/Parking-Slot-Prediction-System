#!/usr/bin/env python3
"""
ML Model Training Script for SmartPark
"""

import sys
import os
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal
from ml_model import MLPredictor
import utils

def train_model(days=30, force=False):
    """Train the ML model"""
    print("🤖 SmartPark ML Model Training")
    print("=" * 40)
    
    db = SessionLocal()
    try:
        predictor = MLPredictor()
        
        # Check if model already exists
        if predictor.is_trained and not force:
            print("⚠️  Model already exists. Use --force to retrain.")
            model_info = predictor.get_model_info()
            if model_info.get('trained_at'):
                print(f"Last trained: {model_info['trained_at']}")
                print(f"Accuracy: {model_info.get('accuracy', 'N/A')}")
            return
        
        print(f"📊 Training with {days} days of historical data...")
        
        # Train the model
        success, message = predictor.train_model(db, days)
        
        if success:
            print(f"✅ {message}")
            
            # Get model info
            model_info = predictor.get_model_info()
            print("\n📈 Model Performance:")
            print(f"  Accuracy: {model_info.get('accuracy', 0):.3f}")
            print(f"  Precision: {model_info.get('precision', 0):.3f}")
            print(f"  Recall: {model_info.get('recall', 0):.3f}")
            print(f"  F1 Score: {model_info.get('f1_score', 0):.3f}")
            print(f"  Training Samples: {model_info.get('training_samples', 0)}")
            
            # Log training event
            utils.log_system_event(db, "INFO", f"ML model trained successfully: {message}", "ml_training")
            
        else:
            print(f"❌ {message}")
            utils.log_system_event(db, "ERROR", f"ML model training failed: {message}", "ml_training")
            
    except Exception as e:
        print(f"❌ Training failed with error: {e}")
        utils.log_system_event(db, "ERROR", f"ML training error: {e}", "ml_training")
        
    finally:
        db.close()

def evaluate_model(days=7):
    """Evaluate model performance"""
    print("📊 SmartPark ML Model Evaluation")
    print("=" * 40)
    
    db = SessionLocal()
    try:
        predictor = MLPredictor()
        
        if not predictor.is_trained:
            print("❌ No trained model found. Please train the model first.")
            return
        
        print(f"🔍 Evaluating model on last {days} days...")
        
        # Evaluate model
        metrics = predictor.evaluate_model(db, days)
        
        if 'error' in metrics:
            print(f"❌ Evaluation failed: {metrics['error']}")
        else:
            print("✅ Evaluation completed!")
            print(f"\n📈 Performance Metrics:")
            print(f"  Accuracy: {metrics.get('accuracy', 0):.3f}")
            print(f"  Correct Predictions: {metrics.get('correct_predictions', 0)}")
            print(f"  Total Predictions: {metrics.get('total_predictions', 0)}")
            
    except Exception as e:
        print(f"❌ Evaluation failed with error: {e}")
        
    finally:
        db.close()

def test_predictions():
    """Test model predictions"""
    print("🔮 SmartPark ML Prediction Test")
    print("=" * 40)
    
    db = SessionLocal()
    try:
        predictor = MLPredictor()
        
        if not predictor.is_trained:
            print("❌ No trained model found. Please train the model first.")
            return
        
        # Get all slots
        from models import Slot
        slots = db.query(Slot).all()
        
        if not slots:
            print("❌ No slots found in database.")
            return
        
        print("🔮 Generating test predictions...")
        
        for slot in slots[:3]:  # Test first 3 slots
            try:
                # Test different time horizons
                for minutes in [15, 30, 60, 120]:
                    probability = predictor.predict_availability(db, slot.id, minutes)
                    status = "FREE" if probability > 0.5 else "OCCUPIED"
                    confidence = "HIGH" if abs(probability - 0.5) > 0.3 else "LOW"
                    
                    print(f"  {slot.slot_label} in {minutes}min: {probability:.3f} ({status}, {confidence})")
                    
            except Exception as e:
                print(f"  ❌ Error predicting for {slot.slot_label}: {e}")
        
    except Exception as e:
        print(f"❌ Prediction test failed: {e}")
        
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(description="SmartPark ML Model Management")
    parser.add_argument('action', choices=['train', 'evaluate', 'test'], 
                       help='Action to perform')
    parser.add_argument('--days', type=int, default=30, 
                       help='Number of days for training/evaluation (default: 30)')
    parser.add_argument('--force', action='store_true', 
                       help='Force retrain even if model exists')
    
    args = parser.parse_args()
    
    if args.action == 'train':
        train_model(args.days, args.force)
    elif args.action == 'evaluate':
        evaluate_model(args.days)
    elif args.action == 'test':
        test_predictions()

if __name__ == "__main__":
    main()
