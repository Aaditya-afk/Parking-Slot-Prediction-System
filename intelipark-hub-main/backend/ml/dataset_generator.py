"""
Synthetic Dataset Generator for Parking Slot Occupancy Prediction
Generates realistic parking data with temporal and spatial patterns
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

class ParkingDatasetGenerator:
    """Generate synthetic parking occupancy dataset"""
    
    def __init__(self, num_slots=70, days=30):
        self.num_slots = num_slots
        self.days = days
        self.zones = ['A', 'B', 'C']
        
    def generate_dataset(self) -> pd.DataFrame:
        """Generate complete dataset with temporal patterns"""
        data = []
        start_date = datetime.now() - timedelta(days=self.days)
        
        for day in range(self.days):
            current_date = start_date + timedelta(days=day)
            day_of_week = current_date.weekday()  # 0=Monday, 6=Sunday
            
            # Generate data for each hour
            for hour in range(24):
                for minute in [0, 15, 30, 45]:  # 15-minute intervals
                    timestamp = current_date.replace(hour=hour, minute=minute, second=0)
                    
                    for slot_id in range(1, self.num_slots + 1):
                        zone = self.zones[(slot_id - 1) // 24]
                        
                        # Calculate occupancy probability based on patterns
                        occupancy_prob = self._calculate_occupancy_probability(
                            hour, day_of_week, zone, slot_id
                        )
                        
                        occupied = 1 if random.random() < occupancy_prob else 0
                        
                        # Duration if occupied (15-60 minutes)
                        duration = random.randint(15, 60) if occupied else 0
                        
                        data.append({
                            'timestamp': timestamp,
                            'slot_id': slot_id,
                            'zone': zone,
                            'occupied': occupied,
                            'duration_minutes': duration,
                            'hour': hour,
                            'day_of_week': day_of_week,
                            'is_weekend': 1 if day_of_week >= 5 else 0,
                            'is_peak_hour': 1 if (9 <= hour <= 11) or (17 <= hour <= 19) else 0
                        })
        
        df = pd.DataFrame(data)
        return df
    
    def _calculate_occupancy_probability(self, hour, day_of_week, zone, slot_id):
        """Calculate realistic occupancy probability"""
        base_prob = 0.3
        
        # Time of day patterns
        if 9 <= hour <= 11:  # Morning peak
            base_prob += 0.4
        elif 12 <= hour <= 14:  # Lunch
            base_prob += 0.3
        elif 17 <= hour <= 19:  # Evening peak
            base_prob += 0.5
        elif 0 <= hour <= 6:  # Night
            base_prob -= 0.2
        
        # Day of week patterns
        if day_of_week >= 5:  # Weekend
            base_prob -= 0.15
        
        # Zone patterns (A closest to entrance, most popular)
        if zone == 'A':
            base_prob += 0.1
        elif zone == 'C':
            base_prob -= 0.05
        
        # Add randomness
        base_prob += random.uniform(-0.1, 0.1)
        
        # Clamp between 0 and 1
        return max(0.05, min(0.95, base_prob))
    
    def add_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add engineered features for ML model"""
        # Lag features (previous occupancy)
        df = df.sort_values(['slot_id', 'timestamp'])
        df['occupied_lag_1'] = df.groupby('slot_id')['occupied'].shift(1).fillna(0)
        df['occupied_lag_2'] = df.groupby('slot_id')['occupied'].shift(2).fillna(0)
        
        # Rolling averages
        df['occupied_rolling_mean_4'] = df.groupby('slot_id')['occupied'].transform(
            lambda x: x.rolling(4, min_periods=1).mean()
        )
        
        # Time-based features
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        
        # Zone encoding
        df['zone_A'] = (df['zone'] == 'A').astype(int)
        df['zone_B'] = (df['zone'] == 'B').astype(int)
        df['zone_C'] = (df['zone'] == 'C').astype(int)
        
        return df
    
    def save_dataset(self, filename='parking_dataset.csv'):
        """Generate and save dataset"""
        print(f"🔄 Generating dataset for {self.num_slots} slots over {self.days} days...")
        df = self.generate_dataset()
        df = self.add_features(df)
        
        df.to_csv(filename, index=False)
        print(f"✅ Dataset saved: {filename}")
        print(f"📊 Total records: {len(df)}")
        print(f"📈 Occupancy rate: {df['occupied'].mean():.2%}")
        
        return df

if __name__ == "__main__":
    # Generate dataset
    generator = ParkingDatasetGenerator(num_slots=70, days=30)
    df = generator.save_dataset('parking_dataset.csv')
    
    # Show sample
    print("\n📋 Sample data:")
    print(df.head(10))
    
    # Statistics
    print("\n📊 Dataset Statistics:")
    print(df.describe())
