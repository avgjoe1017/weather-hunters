"""
Collect Kalshi's Internal Forecast History

This uses Kalshi's new forecast percentile history endpoint to collect
their internal model's predictions over time.

This is REAL historical data - not simulated.

Endpoint: /series/{series_ticker}/events/{ticker}/forecast_percentile_history
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd
import time
from kalshi_python import Configuration, KalshiClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

print("=" * 70)
print("KALSHI FORECAST HISTORY COLLECTOR")
print("=" * 70)
print()
print("Collecting Kalshi's internal forecast predictions (REAL DATA)")
print()

# Setup Kalshi client
private_key_file = PROJECT_ROOT / os.environ["KALSHI_PRIVATE_KEY_FILE"]

config = Configuration(
    host="https://api.elections.kalshi.com/trade-api/v2"
)
config.api_key_id = os.environ["KALSHI_API_KEY_ID"]
config.private_key_pem = private_key_file.read_text()

client = KalshiClient(config)

print("[1/5] Connected to Kalshi API")
print()

# Load official NOAA data to know what events to query
noaa_file = PROJECT_ROOT / "data" / "weather" / "nws_settlement_ground_truth_OFFICIAL.csv"

if not noaa_file.exists():
    print("[X] NOAA ground truth not found. Run collect_noaa_ground_truth.py first.")
    sys.exit(1)

df = pd.read_csv(noaa_file)
df['date'] = pd.to_datetime(df['date'])

print(f"[2/5] Loaded {len(df)} NOAA settlement records")
print(f"      Date range: {df['date'].min()} to {df['date'].max()}")
print(f"      Cities: {df['city'].unique().tolist()}")
print()

# Series ticker mapping
SERIES_MAP = {
    'NYC': 'KXHIGHNY',  # High temp NYC
    'CHI': 'KXHIGHCHI',  # High temp Chicago
    'MIA': 'KXHIGHMIA',  # High temp Miami
    'HOU': 'KXHIGHHOU',  # High temp Houston
}

print("[3/5] Fetching Kalshi forecast history...")
print()
print("NOTE: This may take several minutes due to API rate limits")
print()

forecast_data = []
errors = []

for idx, row in df.iterrows():
    city = row['city']
    date = row['date']
    
    series_ticker = SERIES_MAP.get(city)
    if not series_ticker:
        continue
    
    # Construct event ticker (example: KXHIGHNY-25-01-15)
    # Format: {SERIES}-{YY}-{MM}-{DD}
    date_str = date.strftime('%y-%m-%d')
    event_ticker = f"{series_ticker}-{date_str}"
    
    print(f"[{idx+1}/{len(df)}] {event_ticker} ({city}, {date.strftime('%Y-%m-%d')})")
    
    try:
        # Get forecast history for this event
        # We want the forecast from the day BEFORE settlement
        # This is what models predicted before the outcome was known
        
        # Define time range (day before event)
        event_date = datetime.combine(date.date(), datetime.min.time())
        start_ts = int((event_date - timedelta(days=1)).timestamp() * 1000)
        end_ts = int(event_date.timestamp() * 1000)
        
        # Request specific percentiles (50th = median forecast)
        percentiles = [5000]  # 50th percentile (median)
        period_interval = 1440  # Daily intervals
        
        # Call the API
        from kalshi_python.events_api import EventsApi
        events_api = EventsApi(client)
        
        response = events_api.get_event_forecast_percentile_history(
            series_ticker=series_ticker,
            ticker=event_ticker,
            percentiles=percentiles,
            start_ts=start_ts,
            end_ts=end_ts,
            period_interval=period_interval
        )
        
        # Extract forecast data
        if response and hasattr(response, 'forecast_history') and response.forecast_history:
            for history_point in response.forecast_history:
                if hasattr(history_point, 'percentile_points') and history_point.percentile_points:
                    for percentile_point in history_point.percentile_points:
                        # Get the numerical forecast (temperature in F)
                        kalshi_forecast = percentile_point.numerical_forecast
                        
                        forecast_data.append({
                            'date': date.strftime('%Y-%m-%d'),
                            'city': city,
                            'event_ticker': event_ticker,
                            'kalshi_forecast_temp': kalshi_forecast,
                            'kalshi_forecast_source': 'API_forecast_percentile_history'
                        })
                        
                        print(f"      Kalshi forecast: {kalshi_forecast}F")
                        break
        else:
            print(f"      No forecast history available")
            errors.append({
                'event_ticker': event_ticker,
                'reason': 'No forecast history returned'
            })
        
        # Rate limiting - be respectful to Kalshi API
        time.sleep(0.5)
        
    except Exception as e:
        print(f"      ERROR: {e}")
        errors.append({
            'event_ticker': event_ticker,
            'reason': str(e)
        })
        continue

print()
print(f"[4/5] Collection complete")
print(f"      Collected: {len(forecast_data)} forecasts")
print(f"      Errors: {len(errors)} events")
print()

if len(forecast_data) == 0:
    print("[!] No forecast data collected.")
    print()
    print("Possible reasons:")
    print("  - Kalshi may not have forecast history for events this far back")
    print("  - This endpoint may be for future events only")
    print("  - Event tickers may be formatted incorrectly")
    print()
    print("Next steps:")
    print("  1. Check Kalshi docs for available date ranges")
    print("  2. Test with a recent event ticker")
    print("  3. Consider forward test as primary data collection method")
    sys.exit(0)

# Save to CSV
output_file = PROJECT_ROOT / "data" / "weather" / "kalshi_forecast_history.csv"
output_file.parent.mkdir(parents=True, exist_ok=True)

df_forecasts = pd.DataFrame(forecast_data)
df_forecasts.to_csv(output_file, index=False)

print(f"[5/5] Saved to {output_file}")
print()

# Save errors log
if errors:
    error_file = PROJECT_ROOT / "logs" / "kalshi_forecast_errors.csv"
    pd.DataFrame(errors).to_csv(error_file, index=False)
    print(f"      Saved {len(errors)} errors to {error_file}")
    print()

# Summary
print("=" * 70)
print("KALSHI FORECAST HISTORY SUMMARY")
print("=" * 70)
print()
print(f"Total events checked: {len(df)}")
print(f"Forecasts collected: {len(forecast_data)}")
print(f"Success rate: {len(forecast_data)/len(df)*100:.1f}%")
print()

if len(forecast_data) > 0:
    print("Sample forecasts:")
    print(df_forecasts.head(10).to_string(index=False))
    print()
    
    print("Next steps:")
    print("  1. Merge with NOAA ground truth")
    print("  2. Collect Open-Meteo historical forecasts")
    print("  3. Compare Kalshi vs. Open-Meteo accuracy")
    print("  4. Rebuild ensemble strategy with REAL data")
else:
    print("No forecasts collected. See above for next steps.")

print()
print("=" * 70)

