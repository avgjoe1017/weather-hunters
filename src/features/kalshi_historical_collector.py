"""
Kalshi Historical Outcomes Collector

Collects historical Kalshi weather market data:
1. What markets existed
2. What prices were at different times
3. How markets resolved
4. Market microstructure (spreads, volume)

This lets us backtest: "What would we have traded? What would we have made?"
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class KalshiHistoricalCollector:
    """
    Collect historical Kalshi weather market outcomes.
    
    Note: Kalshi API may not provide full historical data via public API.
    For comprehensive backtesting, you may need to:
    1. Scrape historical data from Kalshi website archives
    2. Use Kalshi's institutional data feeds
    3. Reconstruct from your own trading records
    """
    
    def __init__(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
        data_dir: str = "data/kalshi_history"
    ):
        """
        Initialize Kalshi historical collector.
        
        Args:
            email: Kalshi account email (if using authenticated API)
            password: Kalshi account password
            data_dir: Directory to store collected data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.base_url = "https://api.kalshi.com/trade-api/v2"
        self.demo_url = "https://demo-api.kalshi.co/trade-api/v2"
        
        self.email = email
        self.password = password
        self.token = None
        
        logger.info(f"Initialized Kalshi historical collector, data dir: {self.data_dir}")
    
    def authenticate(self, use_demo: bool = True):
        """Authenticate with Kalshi API if credentials provided."""
        if not self.email or not self.password:
            logger.warning("No credentials provided, using unauthenticated API")
            return
        
        url = self.demo_url if use_demo else self.base_url
        endpoint = f"{url}/login"
        
        try:
            response = requests.post(endpoint, json={
                'email': self.email,
                'password': self.password
            })
            response.raise_for_status()
            self.token = response.json()['token']
            logger.info("Authenticated successfully")
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
    
    def get_series_history(
        self,
        series_ticker: str,
        limit: int = 1000
    ) -> List[Dict]:
        """
        Get historical markets for a series.
        
        Args:
            series_ticker: Series to query (e.g., 'HIGHNYC' for NYC temp)
            limit: Max markets to return
            
        Returns:
            List of market dictionaries
        """
        # Note: This returns current/recent markets
        # For true historical data, need different approach
        
        url = f"{self.base_url}/series/{series_ticker}/markets"
        params = {'limit': limit, 'status': 'settled'}
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            markets = response.json().get('markets', [])
            
            logger.info(f"Retrieved {len(markets)} markets for {series_ticker}")
            return markets
            
        except Exception as e:
            logger.error(f"Error getting series history: {e}")
            return []
    
    def collect_weather_outcomes(
        self,
        start_date: str,
        end_date: str,
        city: str = 'NYC'
    ) -> pd.DataFrame:
        """
        Collect historical weather market outcomes.
        
        This is a PLACEHOLDER - actual implementation depends on:
        1. Whether Kalshi provides historical API access
        2. Whether you have institutional data access
        3. Whether you need to scrape/reconstruct
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            city: City code
            
        Returns:
            DataFrame with historical market outcomes
        """
        logger.warning("="*60)
        logger.warning("CRITICAL: Historical Kalshi data collection")
        logger.warning("="*60)
        logger.warning("")
        logger.warning("Kalshi's public API may not provide full historical data.")
        logger.warning("")
        logger.warning("Options for getting this data:")
        logger.warning("")
        logger.warning("1. MANUAL RECONSTRUCTION:")
        logger.warning("   - Visit kalshi.com/markets/archive")
        logger.warning("   - Download settled market data")
        logger.warning("   - Save to CSV manually")
        logger.warning("")
        logger.warning("2. SCRAPING (if allowed by ToS):")
        logger.warning("   - Use Selenium/BeautifulSoup")
        logger.warning("   - Scrape historical market pages")
        logger.warning("   - Parse settlement data")
        logger.warning("")
        logger.warning("3. INSTITUTIONAL ACCESS:")
        logger.warning("   - Contact Kalshi for data partnership")
        logger.warning("   - May require commercial agreement")
        logger.warning("")
        logger.warning("4. SYNTHETIC BACKTESTING:")
        logger.warning("   - Use actual weather outcomes")
        logger.warning("   - Estimate market prices from forecast accuracy")
        logger.warning("   - Less accurate but better than nothing")
        logger.warning("")
        logger.warning("="*60)
        
        # Return placeholder structure
        dates = pd.date_range(start_date, end_date, freq='D')
        
        df = pd.DataFrame({
            'date': dates,
            'city': city,
            'market_ticker': None,  # Would be actual market ticker
            'bracket_low': None,     # e.g., 70 for 70-72° bracket
            'bracket_high': None,    # e.g., 72
            'opening_price': None,   # Price at 10 AM launch
            'closing_price': None,   # Price before resolution
            'settlement_value': None, # 0 or 100
            'actual_temp': None,     # Actual high temp
            'note': 'Historical Kalshi data requires manual collection or institutional access'
        })
        
        return df
    
    def reconstruct_from_actuals(
        self,
        actuals_df: pd.DataFrame,
        bracket_width: int = 2
    ) -> pd.DataFrame:
        """
        Reconstruct what Kalshi markets WOULD have been.
        
        This is for backtesting when you don't have actual historical Kalshi data.
        
        Args:
            actuals_df: DataFrame with actual temperatures
            bracket_width: Width of temperature brackets (default: 2°F)
            
        Returns:
            DataFrame with synthetic market structure
        """
        logger.info("Reconstructing synthetic Kalshi markets from actuals")
        
        records = []
        
        for _, row in actuals_df.iterrows():
            date = row['date']
            city = row['city']
            actual_temp = row['actual_high_temp']
            
            # Create 6 brackets centered around actual temp
            center = int(actual_temp / bracket_width) * bracket_width
            brackets = []
            
            for i in range(-2, 4):
                low = center + (i * bracket_width)
                high = low + bracket_width
                
                # Did this bracket win?
                won = (actual_temp >= low) and (actual_temp < high)
                
                brackets.append({
                    'date': date,
                    'city': city,
                    'bracket_low': low,
                    'bracket_high': high,
                    'actual_temp': actual_temp,
                    'won': won,
                    # Synthetic prices (would need forecast data to estimate real prices)
                    'est_opening_price': 16.67,  # 1/6 if no info
                    'est_closing_price': 95 if won else 5,  # Simplified
                })
            
            records.extend(brackets)
        
        df = pd.DataFrame(records)
        
        logger.info(f"Reconstructed {len(df)} synthetic market brackets")
        
        return df
    
    def save_historical_data(
        self,
        df: pd.DataFrame,
        filename: str
    ):
        """Save historical data to disk."""
        output_path = self.data_dir / filename
        df.to_csv(output_path, index=False)
        logger.info(f"Saved {len(df)} records to {output_path}")
    
    def load_historical_data(
        self,
        filename: str
    ) -> pd.DataFrame:
        """Load historical data from disk."""
        input_path = self.data_dir / filename
        
        if not input_path.exists():
            logger.warning(f"File not found: {input_path}")
            return pd.DataFrame()
        
        df = pd.read_csv(input_path, parse_dates=['date'])
        logger.info(f"Loaded {len(df)} records from {input_path}")
        
        return df


def create_manual_collection_template():
    """
    Create a template CSV for manual Kalshi data entry.
    
    User can fill this in by:
    1. Going to Kalshi website
    2. Finding settled weather markets
    3. Copying settlement data
    """
    template = pd.DataFrame({
        'date': ['2024-11-01', '2024-11-02'],
        'city': ['NYC', 'NYC'],
        'market_ticker': ['HIGHNYC-241101', 'HIGHNYC-241102'],
        'bracket_low': [68, 66],
        'bracket_high': [70, 68],
        'opening_price_cents': [25, 30],
        'closing_price_cents': [92, 15],
        'won': [True, False],
        'actual_temp': [69.5, 65.2],
        'notes': ['Add your own data here', 'Copy from Kalshi website']
    })
    
    output_path = Path('data/kalshi_history/manual_entry_template.csv')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    template.to_csv(output_path, index=False)
    
    print(f"\n{'='*60}")
    print("MANUAL DATA COLLECTION TEMPLATE CREATED")
    print(f"{'='*60}")
    print(f"\nLocation: {output_path}")
    print("\nHow to use:")
    print("1. Open the template CSV")
    print("2. Go to kalshi.com and find settled weather markets")
    print("3. For each market, copy:")
    print("   - Date")
    print("   - City")
    print("   - Market ticker")
    print("   - Bracket range")
    print("   - Opening price (10 AM)")
    print("   - Closing price (before settlement)")
    print("   - Whether it won")
    print("   - Actual temperature")
    print("4. Save and use for backtesting")
    print(f"\n{'='*60}\n")
    
    return template


def main():
    """Example usage."""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    collector = KalshiHistoricalCollector()
    
    # Show the challenge
    print("\n" + "="*60)
    print("KALSHI HISTORICAL DATA COLLECTION")
    print("="*60 + "\n")
    
    # Attempt to collect (will show warnings)
    df = collector.collect_weather_outcomes(
        start_date='2024-01-01',
        end_date='2024-10-31',
        city='NYC'
    )
    
    # Create manual template
    create_manual_collection_template()
    
    # Example: Reconstruct from actuals (for synthetic backtesting)
    print("\n=== Synthetic Backtest Example ===\n")
    print("If you have actual weather data but no Kalshi data,")
    print("you can create synthetic markets for approximate backtesting:\n")
    
    # Load actual weather data (from previous collector)
    try:
        actuals = pd.read_csv('data/weather/actuals_NYC_2024-01-01_2024-10-31.csv',
                             parse_dates=['date'])
        
        synthetic = collector.reconstruct_from_actuals(actuals)
        collector.save_historical_data(synthetic, 'synthetic_markets_NYC_2024.csv')
        
        print(f"Created {len(synthetic)} synthetic market brackets")
        print("\nNote: This is for approximate backtesting only.")
        print("Real Kalshi prices would differ based on forecasts.")
        
    except FileNotFoundError:
        print("Run weather_data_collector.py first to get actual weather data")


if __name__ == "__main__":
    main()
