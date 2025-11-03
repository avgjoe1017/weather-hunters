"""
Get today's weather forecasts for all trading cities.

This script fetches forecasts for tomorrow and displays them in a trading-ready format.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.features.weather_data_collector import HistoricalWeatherCollector
from datetime import datetime, timedelta

print("=" * 70)
print("TOMORROW'S WEATHER FORECASTS")
print("=" * 70)
print()

# Initialize collector
collector = HistoricalWeatherCollector()

# Get tomorrow's date
tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
print(f"Date: {tomorrow}")
print()

# Cities to trade
cities = {
    'NYC': 'New York City',
    'CHI': 'Chicago',
    'MIA': 'Miami',
    'HOU': 'Houston',
    'AUS': 'Austin',
    'LAX': 'Los Angeles',
    'PHI': 'Philadelphia',
    'DEN': 'Denver'
}

forecasts = {}

for code, name in cities.items():
    try:
        # Get basic forecast
        forecast = collector.collect_current_forecast(tomorrow, code)
        
        # Try to get ensemble (multiple models)
        try:
            ensemble = collector.collect_ensemble_forecast(tomorrow, code)
            has_ensemble = True
        except:
            ensemble = None
            has_ensemble = False
        
        # Store results
        forecasts[code] = {
            'name': name,
            'forecast_high': forecast.get('forecast_high_temp', None),
            'ensemble_mean': ensemble.get('ensemble_mean', None) if ensemble else None,
            'model_disagreement': ensemble.get('model_disagreement', None) if ensemble else None,
            'confidence': 'HIGH' if (ensemble and ensemble.get('model_disagreement', 999) < 3) else 'MEDIUM'
        }
        
        print(f"{name} ({code}):")
        print(f"  Forecast High: {forecasts[code]['forecast_high']:.1f}F")
        
        if has_ensemble:
            print(f"  Ensemble Mean: {forecasts[code]['ensemble_mean']:.1f}F")
            print(f"  Model Disagreement: {forecasts[code]['model_disagreement']:.2f}F")
            print(f"  Confidence: {forecasts[code]['confidence']}")
        
        print()
        
    except Exception as e:
        print(f"{name} ({code}): ERROR - {e}")
        print()

print("=" * 70)
print()
print("TRADING RECOMMENDATIONS:")
print()

for code, data in forecasts.items():
    if data.get('forecast_high'):
        high = data['forecast_high']
        
        # Calculate likely brackets (2F wide)
        lower_bracket = int(high // 2) * 2  # Round down to even number
        upper_bracket = lower_bracket + 2
        
        print(f"{data['name']}:")
        print(f"  Forecast: {high:.1f}F")
        print(f"  Likely brackets: {lower_bracket-2}-{lower_bracket}F, {lower_bracket}-{upper_bracket}F, {upper_bracket}-{upper_bracket+2}F")
        print(f"  Best bracket: {lower_bracket}-{upper_bracket}F (centered on forecast)")
        print(f"  Confidence: {data.get('confidence', 'UNKNOWN')}")
        print()

print("=" * 70)
print()
print("NEXT STEPS:")
print("1. Run: python scripts/deep_market_search.py")
print("2. Find active markets for these cities")
print("3. Compare Kalshi prices to forecasts above")
print("4. Buy brackets where Kalshi underprices (your edge)")
print()
print("Example: If NYC forecast is 72F and Kalshi has 70-72F at 25 cents,")
print("         that's 25% implied probability but true probability is ~40-50%")
print("         Edge = 15-25 percentage points = GOOD TRADE")

