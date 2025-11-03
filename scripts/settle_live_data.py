"""
Settlement Script - The "Unblinding"

This script runs every evening to:
1. Scrape REAL NWS Daily Climate Reports
2. Update the live_validation.csv with actual outcomes
3. Calculate if predictions were correct

This completes the "sealed envelope" test.
"""

import os
import sys
import csv
import logging
from datetime import datetime, timedelta
from pathlib import Path
import requests
from bs4 import BeautifulSoup

# Setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Logging
log_file = PROJECT_ROOT / "logs" / "settle_live_data.log"
log_file.parent.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
)

# Constants
LIVE_VALIDATION_LOG = PROJECT_ROOT / "logs" / "live_validation.csv"

# NWS CLI Report URLs
NWS_CLI_URLS = {
    'NYC': 'https://forecast.weather.gov/product.php?site=OKX&product=CLI&issuedby=NYC',
    'CHI': 'https://forecast.weather.gov/product.php?site=LOT&product=CLI&issuedby=ORD',
    'MIA': 'https://forecast.weather.gov/product.php?site=MFL&product=CLI&issuedby=MIA',
    'HOU': 'https://forecast.weather.gov/product.php?site=HGX&product=CLI&issuedby=IAH',
}

def scrape_nws_settlement(city):
    """
    Scrape the NWS Daily Climate Report for actual high temperature.
    This is the REAL settlement data that Kalshi uses.
    """
    url = NWS_CLI_URLS.get(city)
    if not url:
        logging.error(f"No CLI URL for {city}")
        return None
    
    try:
        headers = {'User-Agent': '(WeatherTrading, contact@example.com)'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse the text report
        text = response.text
        
        # The report format is usually:
        # "MAXIMUM TEMPERATURE FOR TODAY:        75 AT  3:45 PM"
        # or similar
        
        # Look for "MAXIMUM TEMPERATURE" or "HIGH TEMPERATURE"
        for line in text.split('\n'):
            line_upper = line.upper()
            if 'MAXIMUM TEMPERATURE' in line_upper or 'HIGH TEMPERATURE' in line_upper:
                # Extract the number
                import re
                matches = re.findall(r'\b(\d{2,3})\b', line)
                if matches:
                    temp = int(matches[0])
                    logging.info(f"  {city}: {temp}F")
                    return temp
        
        # If not found, try alternative parsing
        # Some reports use "OBSERVED DATA" section
        soup = BeautifulSoup(text, 'html.parser')
        pre = soup.find('pre')
        if pre:
            text = pre.get_text()
            # Look for temperature patterns
            import re
            # Pattern: "TEMPERATURE (F)"
            # Then find the max temp value
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if 'MAXIMUM' in line.upper() or 'MAX' in line.upper():
                    # Next few lines might have the value
                    for j in range(i, min(i+5, len(lines))):
                        matches = re.findall(r'\b(\d{2,3})\b', lines[j])
                        if matches:
                            temp = int(matches[0])
                            if 40 <= temp <= 120:  # Sanity check
                                logging.info(f"  {city}: {temp}F")
                                return temp
        
        logging.warning(f"Could not parse temperature for {city}")
        return None
        
    except Exception as e:
        logging.error(f"Error scraping {city}: {e}")
        return None

def update_settlements():
    """
    Main settlement routine.
    
    Reads PENDING predictions from yesterday,
    fetches REAL NWS settlement,
    calculates outcome (WIN/LOSS),
    updates CSV.
    """
    logging.info("=" * 70)
    logging.info("SETTLEMENT - UNBLINDING YESTERDAY'S PREDICTIONS")
    logging.info("=" * 70)
    logging.info("")
    
    if not LIVE_VALIDATION_LOG.exists():
        logging.error("No validation log found. Run live_data_collector.py first.")
        return
    
    # Read all predictions
    rows = []
    with open(LIVE_VALIDATION_LOG, 'r', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Find yesterday's PENDING predictions
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    updated = 0
    for row in rows:
        if row['date'] == yesterday and row['outcome'] == 'PENDING':
            city = row['city']
            logging.info(f"--- Settling {city} from {yesterday} ---")
            
            # Get REAL settlement temperature
            actual_temp = scrape_nws_settlement(city)
            
            if actual_temp is None:
                logging.warning(f"  Could not get settlement - keeping PENDING")
                continue
            
            # Determine actual bracket
            actual_bracket_low = int(actual_temp // 2) * 2
            actual_bracket_high = actual_bracket_low + 2
            
            # Check if prediction was correct
            predicted_low = int(row['predicted_bracket_low'])
            predicted_high = int(row['predicted_bracket_high'])
            
            is_win = (predicted_low == actual_bracket_low)
            
            # Calculate P&L
            if is_win:
                # Won: Get $10 per contract - cost - 7% fee
                num_contracts = 10  # Example
                cost = num_contracts * float(row['market_prob'])
                gross_win = num_contracts * 1.0
                fee = gross_win * 0.07
                pnl = gross_win - cost - fee
                outcome = 'WIN'
            else:
                # Lost: Lose the cost
                num_contracts = 10
                cost = num_contracts * float(row['market_prob'])
                pnl = -cost
                outcome = 'LOSS'
            
            # Update row
            row['actual_temp'] = str(actual_temp)
            row['outcome'] = outcome
            row['pnl'] = f"{pnl:.2f}"
            
            logging.info(f"  Predicted: {predicted_low}-{predicted_high}F")
            logging.info(f"  Actual: {actual_temp}F ({actual_bracket_low}-{actual_bracket_high}F)")
            logging.info(f"  Outcome: {outcome} (P&L: ${pnl:.2f})")
            logging.info("")
            
            updated += 1
    
    # Write back to CSV
    if updated > 0:
        with open(LIVE_VALIDATION_LOG, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        
        logging.info(f"Updated {updated} settlements")
    else:
        logging.info("No PENDING predictions from yesterday")
    
    logging.info("=" * 70)

if __name__ == "__main__":
    update_settlements()

