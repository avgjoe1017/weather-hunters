"""
Weather Feature Pipeline - Creates ML-ready features from raw weather data
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class WeatherFeaturePipeline:
    """Transform raw weather data into ML features."""
    
    def __init__(self, actuals_dir: str = "data/weather"):
        self.actuals_dir = Path(actuals_dir)
        self.climatology = {}
        
        # Load climatology
        for city in ['NYC', 'CHI', 'MIA', 'AUS']:
            climo_file = self.actuals_dir / f"climatology_{city}_10yr.csv"
            if climo_file.exists():
                self.climatology[city] = pd.read_csv(climo_file)
        
        logger.info("Initialized weather feature pipeline")
    
    def create_features(self, target_date: str, city: str, 
                       forecast_data: dict = None) -> dict:
        """Create feature vector for a single date."""
        
        target_dt = pd.to_datetime(target_date)
        day_of_year = target_dt.dayofyear
        
        features = {
            'day_of_year': day_of_year,
            'month': target_dt.month,
            'is_weekend': 1 if target_dt.dayofweek >= 5 else 0,
        }
        
        # Climatology
        if city in self.climatology:
            climo = self.climatology[city]
            climo_row = climo[climo['day_of_year'] == day_of_year]
            
            if not climo_row.empty:
                features['climo_mean'] = climo_row['climo_high_mean'].values[0]
                features['climo_std'] = climo_row['climo_high_std'].values[0]
        
        # Forecast features
        if forecast_data:
            features['forecast_high'] = forecast_data.get('forecast_high_temp', 0)
            features['ensemble_std'] = forecast_data.get('ensemble_std', 0)
            features['model_disagreement'] = forecast_data.get('model_disagreement', 0)
        
        return features
    
    def create_training_dataset(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Create complete training dataset from historical data."""
        
        logger.info(f"Creating training dataset: {start_date} to {end_date}")
        
        all_records = []
        
        for city in ['NYC', 'CHI', 'MIA', 'AUS']:
            actuals_file = self.actuals_dir / f"actuals_{city}_{start_date}_{end_date}.csv"
            
            if not actuals_file.exists():
                continue
            
            actuals = pd.read_csv(actuals_file, parse_dates=['date'])
            
            for _, row in actuals.iterrows():
                date_str = row['date'].strftime('%Y-%m-%d')
                
                # Simulate forecast (in production, use real forecasts)
                forecast_data = {
                    'forecast_high_temp': row['actual_high_temp'] + np.random.normal(0, 2),
                    'ensemble_std': np.random.uniform(1, 4),
                    'model_disagreement': np.random.uniform(1, 4)
                }
                
                features = self.create_features(date_str, city, forecast_data)
                features['target'] = row['actual_high_temp']
                features['date'] = row['date']
                features['city'] = city
                
                all_records.append(features)
        
        df = pd.DataFrame(all_records)
        logger.info(f"Created dataset with {len(df)} samples")
        
        return df
