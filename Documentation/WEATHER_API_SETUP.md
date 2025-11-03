# Weather API Setup Guide

## 🌦️ Setting Up Real Weather APIs for Validation

**Goal:** Get historical and forecast weather data to properly validate the trading strategy before risking money.

---

## 📋 Recommended APIs (All Free Tier)

### **1. Open-Meteo** ⭐ RECOMMENDED
**Best for:** Historical data + forecasts, no API key needed

**Pros:**
- ✅ Completely free, no API key required
- ✅ Historical data back to 1940
- ✅ Hourly forecasts 16 days out
- ✅ Ensemble forecasts (GFS, ECMWF models)
- ✅ No rate limits on free tier
- ✅ Easy to use

**Cons:**
- Sometimes slower than paid APIs
- Less detailed documentation

**Signup:** None needed!
**Docs:** https://open-meteo.com/en/docs

---

### **2. Visual Crossing Weather** 
**Best for:** Historical data with good quality

**Free Tier:**
- 1,000 API calls/day
- Historical data back to 1970
- Good for backtesting

**Signup:** https://www.visualcrossing.com/weather-api
**Cost:** Free tier, $0 (1000 calls/day)

---

### **3. Weather.gov (NWS)** 
**Best for:** US cities, official data (what Kalshi uses!)

**Pros:**
- ✅ Free, no API key
- ✅ Official NOAA data
- ✅ This is what Kalshi uses for settlement
- ✅ Highly accurate for US cities

**Cons:**
- Only US locations
- Limited historical data (recent only)
- Rate limited to 5 calls/second

**No signup needed**
**Docs:** https://www.weather.gov/documentation/services-web-api

---

### **4. OpenWeatherMap** (Backup)
**Best for:** Current weather + forecasts

**Free Tier:**
- 1,000 API calls/day
- 5-day forecast
- Current conditions

**Historical data:** Costs money (not free)

**Signup:** https://openweathermap.org/api
**Cost:** Free tier for forecasts, $$ for historical

---

## 🎯 **Recommended Setup**

For backtesting + live trading, use **TWO APIs**:

### **For Historical Data (Backtesting):**
**Open-Meteo** - Free, no key needed

```python
# Get 4 years of historical data for NYC
import requests

url = "https://archive-api.open-meteo.com/v1/archive"
params = {
    "latitude": 40.7128,
    "longitude": -74.0060,
    "start_date": "2020-01-01",
    "end_date": "2024-10-31",
    "daily": "temperature_2m_max,temperature_2m_min",
    "temperature_unit": "fahrenheit",
    "timezone": "America/New_York"
}

response = requests.get(url, params=params)
data = response.json()
```

### **For Live Forecasts (Trading):**
**Weather.gov** - Free, official Kalshi source

```python
# Get forecast for NYC (Central Park)
import requests

# Step 1: Get grid coordinates
lat, lon = 40.7829, -73.9654  # Central Park
response = requests.get(f"https://api.weather.gov/points/{lat},{lon}")
grid_data = response.json()

# Step 2: Get forecast
forecast_url = grid_data['properties']['forecast']
forecast_response = requests.get(forecast_url)
forecast = forecast_response.json()
```

---

## ⚡ Quick Setup (5 Minutes)

### **Step 1: No API Keys Needed!**

Both Open-Meteo and Weather.gov are free without keys. Just start using them.

### **Step 2: Test Connection**

```bash
cd C:\Users\joeba\Documents\weather-hunters
python scripts/test_weather_apis.py
```

This will verify you can connect to both APIs.

### **Step 3: Collect Historical Data**

```bash
python scripts/collect_historical_weather.py
```

This will download 4 years of data for all cities (takes ~5 minutes).

### **Step 4: Run Real Validation**

```bash
# Train models on real data
python scripts/train_weather_models.py

# Backtest on real data
python scripts/backtest_weather_models.py
```

Now you'll see REAL expected returns!

---

## 📍 City Coordinates

For Kalshi weather markets:

```python
CITY_COORDS = {
    'NYC': (40.7829, -73.9654),    # Central Park (Kalshi uses this)
    'CHI': (41.7754, -87.7512),    # Midway Airport
    'MIA': (25.7959, -80.2871),    # Miami Intl Airport
    'HOU': (29.6455, -95.2789),    # Houston Hobby
    'AUS': (30.1944, -97.6700),    # Austin-Bergstrom
    'LAX': (33.9425, -118.4081),   # LAX Airport
    'PHI': (39.8729, -75.2437),    # Philadelphia Intl
    'DEN': (39.8561, -104.6737),   # Denver Intl
}
```

**Important:** Use the EXACT coordinates that Kalshi uses for settlement. These are typically official weather stations.

---

## 🔧 Implementation Updates Needed

I'll create these scripts for you:

### **1. `scripts/test_weather_apis.py`**
Tests connection to Open-Meteo and Weather.gov

### **2. `scripts/collect_historical_weather.py`**
Downloads 4 years of data for all cities (~10 min)

### **3. Update `src/features/weather_data_collector.py`**
Integrate Open-Meteo and Weather.gov APIs

---

## ⚙️ No .env Changes Needed

Since both recommended APIs are free without keys:

```bash
# .env - NO changes needed!
# Open-Meteo: No key required
# Weather.gov: No key required
```

---

## 📊 What You'll Get

After setup, you'll have:

```
data/weather/
├── NYC_2020-2024.csv       (1,460 days)
├── CHI_2020-2024.csv       (1,460 days)
├── MIA_2020-2024.csv       (1,460 days)
├── HOU_2020-2024.csv       (1,460 days)
├── AUS_2020-2024.csv       (1,460 days)
└── ...

Total: ~7,300 observations
```

Each row contains:
- Date
- Actual high temperature (from historical data)
- Forecast high temperature (simulated from historical)
- Actual low temperature
- Humidity, wind, precipitation
- Day of year, month (seasonality)

---

## 🎯 Expected Timeline

**Tonight (30 minutes):**
1. Run test script (verify APIs work) - 2 min
2. Collect historical data - 10 min
3. Train models on real data - 10 min
4. Run backtest - 5 min
5. Review results - 5 min

**If backtest >15% return:**
- ✅ Strategy validated
- ✅ Ready to trade tomorrow morning

**If backtest <15% return:**
- ⚠️ Strategy needs improvement
- ⚠️ Don't trade yet

---

## 🚀 Next Steps

I'm creating the scripts now:
1. `test_weather_apis.py` - Test connections
2. `collect_historical_weather.py` - Download 4 years data
3. Updated `weather_data_collector.py` - Real API integration

Run them in order and you'll have real validation in 30 minutes!

---

## 💡 Pro Tips

**1. Rate Limiting:**
- Open-Meteo: No limits
- Weather.gov: 5 requests/second max
- Add `time.sleep(0.2)` between Weather.gov calls

**2. Data Quality:**
- Open-Meteo uses ERA5 reanalysis (very accurate)
- Weather.gov is what Kalshi uses (perfect match!)
- Always verify coordinates match Kalshi's stations

**3. Caching:**
- Save all historical data locally
- Don't re-download every time
- Historical data doesn't change!

**4. Ensemble Forecasts:**
- Open-Meteo provides GFS, ECMWF ensemble
- Use ensemble spread for confidence
- Low spread = high confidence = bigger position

---

**Ready to set up real APIs?** I'll create the scripts now!

