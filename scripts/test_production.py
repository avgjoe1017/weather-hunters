"""Test production endpoint connection."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import os
from src.api.kalshi_connector import create_connector_from_env

# Force production mode
os.environ['KALSHI_USE_DEMO'] = 'false'

print("Testing production endpoint...")
print()

try:
    api = create_connector_from_env()
    print("API connector created successfully")
    print()
    
    print("Testing balance endpoint...")
    balance = api.get_balance()
    print(f"Success! Balance: ${balance.get('balance', 0)/100:.2f}")
    print()
    print("Production connection works!")
except Exception as e:
    print(f"Error: {e}")
    print()
    print("Note: Demo endpoint returned 401 Unauthorized.")
    print("This could mean:")
    print("1. Demo endpoint might not be available")
    print("2. Your API keys might be for production only")
    print("3. Signature format might need adjustment")

