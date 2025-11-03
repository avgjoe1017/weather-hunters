# How to Get Kalshi Historical Market Data

## 🎯 **Goal**

Download REAL historical market prices from Kalshi to test if our strategy actually works.

---

## 📥 **Method 1: Bulk CSV Download (RECOMMENDED - Fastest)**

### **Step 1: Visit Kalshi Market Data Page**

Go to: **https://kalshi.com/market-data**

### **Step 2: Download Data**

Look for:
- "Historical Market Data"
- "Download CSV"
- "Market History"
- Or similar link

### **Step 3: Filter to Weather Markets**

You need data for these series:
- `KXHIGHNY` (NYC high temperature)
- `KXHIGHCHI` (Chicago high temperature)
- `KXHIGHMIA` (Miami high temperature)
- `KXHIGHHOU` (Houston high temperature)

### **Step 4: Required Columns**

The CSV should have:
- `date` - Trading date (YYYY-MM-DD format)
- `ticker` or `market_ticker` - Market identifier
- `close` or `close_price` - Closing price (0.00 to 1.00)
- `open` - Opening price (optional but helpful)
- `high` - High price (optional)
- `low` - Low price (optional)
- `volume` - Trading volume (optional)

### **Step 5: Process the Data**

Create a file: `data/weather/kalshi_historical_prices.csv`

**Required format:**
```csv
date,city,market_ticker,close_price,bracket_low,bracket_high
2024-01-15,NYC,KXHIGHNY-24-01-15-T60,0.42,60,62
2024-01-15,NYC,KXHIGHNY-24-01-15-T58,0.35,58,60
2024-01-15,CHI,KXHIGHCHI-24-01-15-T45,0.38,45,47
...
```

**Columns explained:**
- `date` - The date this market was for
- `city` - NYC, CHI, MIA, or HOU
- `market_ticker` - Full Kalshi market ticker
- `close_price` - Final market price (0.00 to 1.00, e.g., 0.42 = 42¢)
- `bracket_low` - Temperature bracket low (e.g., 60)
- `bracket_high` - Temperature bracket high (e.g., 62)

### **Step 6: Save File**

Save as: `C:\Users\joeba\Documents\weather-hunters\data\weather\kalshi_historical_prices.csv`

---

## 📊 **Method 2: API Collection (Automated)**

If bulk download isn't available, use our script:

```bash
python scripts/collect_historical_market_prices.py
```

**This will:**
- Connect to Kalshi API
- Fetch candlestick data for all weather markets
- Save to `data/weather/kalshi_historical_prices.csv`

**Limitations:**
- Slower (API rate limits)
- May not have all historical data
- Requires authentication

---

## 🔍 **Verifying Your Data**

Once you have the file, check it:

```bash
# View first few lines
head data/weather/kalshi_historical_prices.csv

# Count records
wc -l data/weather/kalshi_historical_prices.csv
```

**Good data should have:**
- At least 100+ records
- Multiple cities (NYC, CHI, MIA, HOU)
- Dates in 2024
- Prices between 0.00 and 1.00

---

## 🚀 **Running the Reality Check**

Once you have the data:

```bash
python scripts/quick_reality_check.py
```

**This will tell you:**
- Does the strategy work with REAL market prices?
- What's the actual win rate?
- What's the actual return?
- Should we proceed to live trading?

---

## ⚠️ **Troubleshooting**

### **Can't Find Market Data Page**

If https://kalshi.com/market-data doesn't exist:

1. Log in to Kalshi
2. Look for "Data" or "API" in menu
3. Try: https://kalshi.com/docs
4. Or email: support@kalshi.com asking for historical market data

### **CSV Format is Different**

If the CSV has different columns, create a mapping:

```python
# Example transformation
import pandas as pd

# Read their format
df = pd.read_csv('kalshi_download.csv')

# Transform to our format
df_transformed = pd.DataFrame({
    'date': df['settlement_date'],
    'city': df['series_ticker'].str.replace('KXHIGH', ''),
    'market_ticker': df['ticker'],
    'close_price': df['last_price'] / 100.0,  # Convert cents to dollars
    'bracket_low': df['strike_low'],
    'bracket_high': df['strike_high']
})

# Save
df_transformed.to_csv('data/weather/kalshi_historical_prices.csv', index=False)
```

### **No Historical Data Available**

If Kalshi doesn't provide historical data:

**Option 1:** Use our simulated prices (less ideal)
- The original backtest already does this

**Option 2:** 30-day forward test (better)
- Collect REAL data going forward
- Takes 30 days but guarantees real data

**Option 3:** Try the API script
```bash
python scripts/collect_historical_market_prices.py
```

---

## 📧 **Need Help?**

If you're stuck, here's what to share:
1. Screenshot of Kalshi market data page
2. Sample of the CSV format they provide
3. Error messages from the script

---

## 🎯 **Bottom Line**

**Goal:** Get REAL historical Kalshi market prices

**Best Path:** Bulk CSV download from kalshi.com/market-data

**Alternative:** Use our API collection script

**Next:** Run `python scripts/quick_reality_check.py` to test strategy with real data

**This is the moment of truth.** 🔍

