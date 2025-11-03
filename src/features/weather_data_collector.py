"""
Historical Weather Data Collector

Collects historical weather data from multiple sources:
1. NWS (National Weather Service) - Official settlement source
2. Open-Meteo - ECMWF, GFS, and other model access
3. Historical reforecasts and actual outcomes

This is the foundation for Strategy B backtesting.
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class HistoricalWeatherCollector:
    """
    Collect historical weather data for backtesting.
    
    Kalshi cities:
    - New York City (Central Park): 40.7829, -73.9654
    - Chicago (Midway Airport): 41.7868, -87.7522
    - Miami (Intl Airport): 25.7959, -80.2871
    - Austin (Bergstrom Airport): 30.1945, -97.6699
    """
    
    # Kalshi settlement locations
    LOCATIONS = {
        'NYC': {
            'name': 'New York City',
            'lat': 40.7829,
            'lon': -73.9654,
            'station': 'KNYC',  # Central Park station
            'timezone': 'America/New_York'
        },
        'CHI': {
            'name': 'Chicago',
            'lat': 41.7868,
            'lon': -87.7522,
            'station': 'KMDW',  # Midway Airport
            'timezone': 'America/Chicago'
        },
        'MIA': {
            'name': 'Miami',
            'lat': 25.7959,
            'lon': -80.2871,
            'station': 'KMIA',  # Miami Intl
            'timezone': 'America/New_York'
        },
        'AUS': {
            'name': 'Austin',
            'lat': 30.1945,
            'lon': -97.6699,
            'station': 'KAUS',  # Austin-Bergstrom
            'timezone': 'America/Chicago'
        }
    }
    
    def __init__(self, data_dir: str = "data/weather"):
        """
        Initialize weather data collector.
        
        Args:
            data_dir: Directory to store collected data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # API endpoints
        self.open_meteo_url = "https://archive-api.open-meteo.com/v1/archive"
        self.open_meteo_forecast_url = "https://api.open-meteo.com/v1/forecast"
        
        logger.info(f"Initialized weather collector, data dir: {self.data_dir}")
    
    def collect_historical_actuals(
        self,
        start_date: str,
        end_date: str,
        city: str = 'NYC'
    ) -> pd.DataFrame:
        """
        Collect actual historical temperatures (what actually happened).
        This is what Kalshi markets settle on.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            city: City code (NYC, CHI, MIA, AUS)
            
        Returns:
            DataFrame with actual daily high temperatures
        """
        logger.info(f"Collecting historical actuals for {city}: {start_date} to {end_date}")
        
        location = self.LOCATIONS[city]
        
        params = {
            'latitude': location['lat'],
            'longitude': location['lon'],
            'start_date': start_date,
            'end_date': end_date,
            'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum',
            'temperature_unit': 'fahrenheit',
            'timezone': location['timezone']
        }
        
        try:
            response = requests.get(self.open_meteo_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            df = pd.DataFrame({
                'date': pd.to_datetime(data['daily']['time']),
                'city': city,
                'actual_high_temp': data['daily']['temperature_2m_max'],
                'actual_low_temp': data['daily']['temperature_2m_min'],
                'actual_precip': data['daily']['precipitation_sum']
            })
            
            # Save to disk
            output_file = self.data_dir / f"actuals_{city}_{start_date}_{end_date}.csv"
            df.to_csv(output_file, index=False)
            logger.info(f"Saved {len(df)} days of actual data to {output_file}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error collecting actuals for {city}: {e}")
            return pd.DataFrame()
    
    def collect_historical_forecasts(
        self,
        target_date: str,
        forecast_date: str,
        city: str = 'NYC',
        models: List[str] = None
    ) -> Dict[str, float]:
        """
        Collect what the forecast WAS on forecast_date for target_date.
        
        This requires historical reforecast data, which is tricky.
        Open-Meteo doesn't provide this directly, so we use current
        forecast as a proxy for backtesting.
        
        Args:
            target_date: Date being forecasted
            forecast_date: Date when forecast was made
            city: City code
            models: Which models to include
            
        Returns:
            Dictionary of model forecasts
        """
        # Note: True historical reforecasts require paid APIs or archives
        # For backtesting, we can use:
        # 1. Historical NWS forecast archives (if available)
        # 2. Assume forecast accuracy similar to current forecasts
        # 3. Use climatology + perturbations
        
        logger.warning("Historical reforecasts not available via free API")
        logger.warning("For production backtesting, use:")
        logger.warning("1. NOAA NOMADS archives")
        logger.warning("2. ECMWF MARS archives (requires account)")
        logger.warning("3. Paid historical forecast APIs")
        
        # Return placeholder structure
        return {
            'forecast_date': forecast_date,
            'target_date': target_date,
            'city': city,
            'nws_forecast': None,  # Would need NWS archives
            'ecmwf_forecast': None,  # Would need ECMWF archives
            'gfs_forecast': None,  # Would need GFS archives
            'note': 'Historical reforecasts require specialized data sources'
        }
    
    def collect_current_forecast(
        self,
        target_date: str,
        city: str = 'NYC'
    ) -> Dict[str, any]:
        """
        Collect CURRENT forecast for a future date.
        Use this for live trading, not backtesting.
        
        Args:
            target_date: Date to forecast (YYYY-MM-DD)
            city: City code
            
        Returns:
            Dictionary with all model forecasts
        """
        logger.info(f"Collecting current forecast for {city} on {target_date}")
        
        location = self.LOCATIONS[city]
        
        # Open-Meteo provides multiple models
        params = {
            'latitude': location['lat'],
            'longitude': location['lon'],
            'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum',
            'temperature_unit': 'fahrenheit',
            'timezone': location['timezone'],
            'forecast_days': 7,
            'models': 'best_match'  # Uses best available models
        }
        
        try:
            response = requests.get(self.open_meteo_forecast_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Find the target date in forecast
            dates = data['daily']['time']
            if target_date not in dates:
                logger.warning(f"Target date {target_date} not in forecast range")
                return {}
            
            idx = dates.index(target_date)
            
            forecast = {
                'forecast_date': datetime.now().strftime('%Y-%m-%d'),
                'target_date': target_date,
                'city': city,
                'forecast_high_temp': data['daily']['temperature_2m_max'][idx],
                'forecast_low_temp': data['daily']['temperature_2m_min'][idx],
                'forecast_precip': data['daily']['precipitation_sum'][idx],
            }
            
            return forecast
            
        except Exception as e:
            logger.error(f"Error collecting forecast for {city}: {e}")
            return {}
    
    def collect_ensemble_forecast(
        self,
        target_date: str,
        city: str = 'NYC'
    ) -> Dict[str, any]:
        """
        Collect ensemble forecast data (multiple model runs).
        This gives us uncertainty/disagreement metrics.
        
        Args:
            target_date: Date to forecast
            city: City code
            
        Returns:
            Dictionary with ensemble statistics
        """
        logger.info(f"Collecting ensemble forecast for {city} on {target_date}")
        
        location = self.LOCATIONS[city]
        
        # Open-Meteo ensemble endpoint
        params = {
            'latitude': location['lat'],
            'longitude': location['lon'],
            'daily': 'temperature_2m_max',
            'temperature_unit': 'fahrenheit',
            'timezone': location['timezone'],
            'forecast_days': 7,
            'models': 'ecmwf_ifs025,gfs_seamless,icon_seamless'  # Multiple models
        }
        
        # Note: Free tier may not include all ensemble members
        # For production, use ECMWF ensemble (51 members) or GEFS (31 members)
        
        try:
            # Collect from multiple models
            models_data = {}
            
            for model in ['ecmwf_ifs025', 'gfs_seamless', 'icon_seamless']:
                params['models'] = model
                response = requests.get(self.open_meteo_forecast_url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    dates = data['daily']['time']
                    
                    if target_date in dates:
                        idx = dates.index(target_date)
                        models_data[model] = data['daily']['temperature_2m_max'][idx]
                
                time.sleep(0.5)  # Rate limiting
            
            if not models_data:
                return {}
            
            # Calculate ensemble statistics
            values = list(models_data.values())
            
            ensemble = {
                'forecast_date': datetime.now().strftime('%Y-%m-%d'),
                'target_date': target_date,
                'city': city,
                'ensemble_mean': np.mean(values),
                'ensemble_std': np.std(values),
                'ensemble_min': np.min(values),
                'ensemble_max': np.max(values),
                'model_disagreement': np.std(values),  # KEY FEATURE!
                'num_models': len(values),
                'models': models_data
            }
            
            return ensemble
            
        except Exception as e:
            logger.error(f"Error collecting ensemble for {city}: {e}")
            return {}
    
    def collect_climatology(
        self,
        city: str = 'NYC',
        years: int = 30
    ) -> pd.DataFrame:
        """
        Collect historical climatology (day-of-year averages).
        
        Args:
            city: City code
            years: Number of years of history
            
        Returns:
            DataFrame with climatological normals by day-of-year
        """
        logger.info(f"Collecting {years}-year climatology for {city}")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years*365)
        
        # Get all historical data
        df = self.collect_historical_actuals(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d'),
            city
        )
        
        if df.empty:
            return df
        
        # Calculate day-of-year statistics
        df['day_of_year'] = df['date'].dt.dayofyear
        
        climatology = df.groupby('day_of_year').agg({
            'actual_high_temp': ['mean', 'std', 'min', 'max'],
            'actual_precip': ['mean', 'sum']
        }).reset_index()
        
        climatology.columns = [
            'day_of_year',
            'climo_high_mean',
            'climo_high_std',
            'climo_high_min',
            'climo_high_max',
            'climo_precip_mean',
            'climo_precip_sum'
        ]
        
        # Save
        output_file = self.data_dir / f"climatology_{city}_{years}yr.csv"
        climatology.to_csv(output_file, index=False)
        logger.info(f"Saved climatology to {output_file}")
        
        return climatology
    
    def collect_all_cities(
        self,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        Collect historical actuals for all Kalshi cities.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Combined DataFrame for all cities
        """
        logger.info(f"Collecting data for all cities: {start_date} to {end_date}")
        
        all_data = []
        
        for city in self.LOCATIONS.keys():
            df = self.collect_historical_actuals(start_date, end_date, city)
            if not df.empty:
                all_data.append(df)
            time.sleep(1)  # Rate limiting
        
        if not all_data:
            return pd.DataFrame()
        
        combined = pd.concat(all_data, ignore_index=True)
        
        # Save combined
        output_file = self.data_dir / f"all_cities_{start_date}_{end_date}.csv"
        combined.to_csv(output_file, index=False)
        logger.info(f"Saved combined data: {len(combined)} records to {output_file}")
        
        return combined


def main():
    """Example usage for collecting historical data."""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    collector = HistoricalWeatherCollector()
    
    # Collect 4 years of historical actuals (2020-2024)
    print("\n=== Collecting Historical Actuals (2020-2024) ===\n")
    
    df_all = collector.collect_all_cities(
        start_date='2020-01-01',
        end_date='2024-10-31'
    )
    
    print(f"\nCollected {len(df_all)} total records")
    print(f"Cities: {df_all['city'].unique()}")
    print(f"Date range: {df_all['date'].min()} to {df_all['date'].max()}")
    
    # Collect climatology for each city
    print("\n=== Collecting 30-Year Climatology ===\n")
    
    for city in ['NYC', 'CHI', 'MIA', 'AUS']:
        climo = collector.collect_climatology(city, years=10)  # Use 10 for faster demo
        print(f"{city}: {len(climo)} days of climatology")
    
    # Example: Collect current forecast
    print("\n=== Example Current Forecast ===\n")
    
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    forecast = collector.collect_current_forecast(tomorrow, 'NYC')
    print(json.dumps(forecast, indent=2))
    
    # Example: Collect ensemble
    print("\n=== Example Ensemble Forecast ===\n")
    
    ensemble = collector.collect_ensemble_forecast(tomorrow, 'NYC')
    if ensemble:
        print(f"Ensemble mean: {ensemble['ensemble_mean']:.1f}°F")
        print(f"Model disagreement: {ensemble['model_disagreement']:.2f}°F")
        print(f"Models: {ensemble['models']}")


if __name__ == "__main__":
    main()
