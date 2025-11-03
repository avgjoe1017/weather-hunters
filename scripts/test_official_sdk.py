"""Test using official Kalshi Python SDK."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import os
from dotenv import load_dotenv
from kalshi_python import Configuration, KalshiClient

load_dotenv()

print("Testing with Official Kalshi Python SDK...")
print()

api_key_id = os.getenv('KALSHI_API_KEY_ID')
private_key = os.getenv('KALSHI_PRIVATE_KEY')

if not api_key_id or not private_key:
    print("[X] Missing API credentials in .env")
    exit(1)

print("Creating client with official SDK...")
print()

try:
    # Configure per Kalshi documentation
    config = Configuration(
        host="https://api.elections.kalshi.com/trade-api/v2"
    )
    
    # Set API key authentication properties
    config.api_key_id = api_key_id
    config.private_key_pem = private_key
    
    print(f"Config host: {config.host}")
    print(f"Config has api_key_id: {hasattr(config, 'api_key_id')}")
    print(f"Config has private_key_pem: {hasattr(config, 'private_key_pem')}")
    print()
    
    # Initialize the client
    client = KalshiClient(config)
    
    print("[OK] Client created successfully")
    print()
    
    print("Testing balance endpoint...")
    balance = client.get_balance()
    
    print(f"[OK] Success! Balance: ${balance.balance / 100:.2f}")
    print()
    print("=" * 60)
    print("SUCCESS! Official SDK works!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Update our connector to use the official SDK")
    print("2. Or fix our custom signature implementation")
    
except AttributeError as e:
    print(f"[X] Configuration error: {e}")
    print()
    print("The Configuration object might not support these attributes.")
    print("Checking Configuration object structure...")
    print(f"Available attributes: {[attr for attr in dir(config) if not attr.startswith('_')]}")
    
except Exception as e:
    print(f"[X] Error: {e}")
    print()
    import traceback
    traceback.print_exc()
    print()
    print("Possible issues:")
    print("1. API keys might not be activated")
    print("2. Private key format might be incorrect")
    print("3. SDK version might be outdated")
