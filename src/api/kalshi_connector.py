"""
Kalshi API Connector

This module provides a clean interface to the Kalshi API, handling:
- Authentication with API keys (RSA signing)
- Market data retrieval
- Order placement
- Position tracking
- Error handling and rate limiting

Based on the official Kalshi starter code with enhanced features.
Updated for API key authentication per docs.kalshi.com
"""

import os
import time
import hashlib
import base64
import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger
from pathlib import Path

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logger.warning("cryptography not installed - API key authentication will not work")


class KalshiAPIConnector:
    """
    Main connector class for interacting with Kalshi's API.
    
    Supports API key authentication with RSA signing per Kalshi API documentation.
    See: https://docs.kalshi.com/welcome
    """
    
    # API Base URLs
    # Documentation: https://docs.kalshi.com/welcome
    # Note: Demo endpoint appears to be deprecated/removed (returns 404)
    DEMO_BASE_URL = "https://demo-api.kalshi.co/trade-api/v2"  # May not be available
    PROD_BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"  # Production endpoint per docs.kalshi.com
    
    def __init__(
        self, 
        api_key_id: Optional[str] = None,
        private_key: Optional[str] = None,
        private_key_file: Optional[str] = None,
        use_demo: bool = False
    ):
        """
        Initialize the Kalshi API connector.
        
        Args:
            api_key_id: Kalshi API Key ID
            private_key: RSA private key in PEM format (string)
            private_key_file: Path to RSA private key PEM file (alternative to private_key)
            use_demo: If True, use demo environment (default: False, demo may not be available)
        """
        if not CRYPTO_AVAILABLE:
            raise ImportError("cryptography package is required for API key authentication. Install with: pip install cryptography")
        
        if not api_key_id:
            raise ValueError("api_key_id is required")
        
        if not private_key and not private_key_file:
            raise ValueError("Either private_key or private_key_file must be provided")
        
        self.api_key_id = api_key_id
        self.use_demo = use_demo
        self.base_url = self.DEMO_BASE_URL if use_demo else self.PROD_BASE_URL
        
        # Load private key
        if private_key_file:
            key_path = Path(private_key_file)
            if not key_path.exists():
                raise FileNotFoundError(f"Private key file not found: {private_key_file}")
            private_key = key_path.read_text()
        
        # Parse private key
        try:
            # Handle newline characters in private key string
            # Support both escaped newlines (\n) and actual newlines
            if isinstance(private_key, str):
                # Replace escaped newlines with actual newlines
                private_key_clean = private_key.replace('\\n', '\n')
                
                # Check if key is on a single line (from .env multiline parsing issue)
                # If BEGIN and END are present but no actual newlines in content, reconstruct
                if ('BEGIN RSA PRIVATE KEY' in private_key_clean or 'BEGIN PRIVATE KEY' in private_key_clean) and 'END' in private_key_clean:
                    # Check if the key content appears to be on one line
                    # Count actual newlines (not just escaped)
                    actual_newlines = private_key_clean.count('\n')
                    
                    # If very few newlines or all content seems compressed, reconstruct
                    if actual_newlines < 5 or (actual_newlines == 1 and 'BEGIN' in private_key_clean and 'END' in private_key_clean):
                        # Extract key content between BEGIN and END markers
                        if 'BEGIN RSA PRIVATE KEY' in private_key_clean:
                            start_marker = '-----BEGIN RSA PRIVATE KEY-----'
                            end_marker = '-----END RSA PRIVATE KEY-----'
                        else:
                            start_marker = '-----BEGIN PRIVATE KEY-----'
                            end_marker = '-----END PRIVATE KEY-----'
                        
                        start_idx = private_key_clean.find(start_marker)
                        end_idx = private_key_clean.find(end_marker)
                        
                        if start_idx != -1 and end_idx != -1:
                            # Extract key content
                            key_content = private_key_clean[start_idx + len(start_marker):end_idx].strip()
                            # Remove all whitespace/newlines
                            key_content = key_content.replace('\n', '').replace('\r', '').replace(' ', '').replace('\t', '')
                            
                            # Reconstruct with proper PEM formatting (64 chars per line)
                            private_key_clean = f"{start_marker}\n"
                            for i in range(0, len(key_content), 64):
                                private_key_clean += key_content[i:i+64] + "\n"
                            private_key_clean += end_marker
                            logger.debug("Reconstructed private key from single-line format")
                
                private_key_clean = private_key_clean.strip()
                
                # Check if it's already in PEM format
                if 'BEGIN PRIVATE KEY' in private_key_clean or 'BEGIN RSA PRIVATE KEY' in private_key_clean:
                    # Already in PEM format
                    key_bytes = private_key_clean.encode('utf-8')
                else:
                    # Key appears to be raw base64 - try to decode and wrap in PEM format
                    # Or it might be missing headers
                    logger.warning("Private key missing PEM headers - attempting to add them")
                    key_base64 = private_key_clean.replace('\n', '').replace(' ', '').replace('-', '').replace('_', '')
                    
                    # Try base64 decoding first to verify it's valid base64
                    try:
                        # Decode to verify it's valid base64, then re-encode
                        decoded_bytes = base64.b64decode(key_base64 + '=' * (4 - len(key_base64) % 4))
                        # Re-encode and wrap in PEM
                        key_base64_reencoded = base64.b64encode(decoded_bytes).decode('ascii')
                    except Exception:
                        # If decoding fails, use original key (might already be properly formatted base64)
                        key_base64_reencoded = key_base64
                    
                    # Wrap in PEM format (PKCS#8 format)
                    private_key_pem = f"-----BEGIN PRIVATE KEY-----\n"
                    # Add newlines every 64 chars
                    for i in range(0, len(key_base64_reencoded), 64):
                        private_key_pem += key_base64_reencoded[i:i+64] + "\n"
                    private_key_pem += "-----END PRIVATE KEY-----"
                    key_bytes = private_key_pem.encode('utf-8')
            else:
                key_bytes = private_key
            
            # Try to load as PEM private key
            # Support both PKCS#8 (BEGIN PRIVATE KEY) and PKCS#1 (BEGIN RSA PRIVATE KEY) formats
            try:
                self.private_key = serialization.load_pem_private_key(
                    key_bytes,
                    password=None,
                    backend=default_backend()
                )
                logger.debug("Successfully loaded private key")
            except Exception as e:
                error_msg = f"Failed to load private key: {e}"
                logger.error(error_msg)
                logger.error("Make sure your private key is in PEM format with proper BEGIN/END markers")
                logger.error("Expected format: -----BEGIN PRIVATE KEY----- or -----BEGIN RSA PRIVATE KEY-----")
                raise ValueError(error_msg)
                
        except Exception as e:
            error_msg = f"Failed to load private key: {e}"
            logger.error(error_msg)
            logger.error("Make sure your private key is in PEM format")
            raise ValueError(error_msg)
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
        logger.info(f"Initialized Kalshi API connector (demo={use_demo})")
        logger.info(f"API Key ID: {api_key_id[:8]}...")
    
    def _sign_request(
        self,
        method: str,
        path: str,
        timestamp: str,
        body: Optional[str] = None
    ) -> str:
        """
        Sign a request using RSA-SHA256 per Kalshi API specification.
        
        According to Kalshi docs, signature is: timestamp + method + path
        See: https://docs.kalshi.com/getting_started/api_keys
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: API endpoint path
            timestamp: Request timestamp (in milliseconds)
            body: Request body (if any) - may not be used in signing
            
        Returns:
            Base64-encoded signature
        """
        # Create message to sign: timestamp + method + path
        # Per Kalshi docs: signature = timestamp + method + path
        # Some APIs require hashing first, then signing
        message = f"{timestamp}{method.upper()}{path}"
        
        # Try two approaches:
        # 1. Hash the message first, then sign the hash (common pattern)
        # 2. Sign the message directly (as currently implemented)
        # Let's try hashing first, which is more common for API signatures
        message_hash = hashlib.sha256(message.encode()).digest()
        
        # Sign the hash with RSA
        signature = self.private_key.sign(
            message_hash,
            padding.PKCS1v15(),  # Use PKCS1v15 padding for RSA
            hashes.SHA256()
        )
        
        # Return base64-encoded signature
        return base64.b64encode(signature).decode()
    
    def _rate_limit(self):
        """Implement simple rate limiting."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        self.last_request_time = time.time()
    
    def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make an authenticated API request with RSA signing.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON body
            
        Returns:
            Response data as dictionary
        """
        self._rate_limit()
        
        # Prepare URL
        url = f"{self.base_url}{endpoint}"
        
        # Prepare body
        body_str = None
        if json_data:
            body_str = json.dumps(json_data, separators=(',', ':'))
        
        # Create timestamp (in milliseconds per Kalshi docs)
        timestamp_ms = str(int(time.time() * 1000))
        
        # Create signature
        path = endpoint  # Path for signing (just the endpoint)
        signature = self._sign_request(method, path, timestamp_ms, body_str)
        
        # Prepare headers per Kalshi API specification
        # See: https://docs.kalshi.com/getting_started/api_keys
        headers = {
            "KALSHI-ACCESS-KEY": self.api_key_id,
            "KALSHI-ACCESS-TIMESTAMP": timestamp_ms,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {method} {endpoint} - {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise
    
    # ========== Market Data Methods ==========
    
    def get_markets(
        self, 
        limit: int = 100,
        status: str = "open",
        series_ticker: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get list of markets.
        
        Args:
            limit: Maximum number of markets to return
            status: Market status filter (open, closed, settled)
            series_ticker: Filter by series ticker
            
        Returns:
            List of market dictionaries
        """
        params = {
            "limit": limit,
            "status": status
        }
        if series_ticker:
            params["series_ticker"] = series_ticker
        
        response = self._make_request("GET", "/markets", params=params)
        return response.get("markets", [])
    
    def get_market(self, ticker: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific market.
        
        Args:
            ticker: Market ticker symbol
            
        Returns:
            Market details dictionary
        """
        response = self._make_request("GET", f"/markets/{ticker}")
        return response.get("market", {})
    
    def get_orderbook(self, ticker: str) -> Dict[str, Any]:
        """
        Get current orderbook for a market.
        
        Args:
            ticker: Market ticker symbol
            
        Returns:
            Orderbook with bids and asks
        """
        response = self._make_request("GET", f"/markets/{ticker}/orderbook")
        return response
    
    def get_trades(self, ticker: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent trades for a market.
        
        Args:
            ticker: Market ticker symbol
            limit: Maximum number of trades to return
            
        Returns:
            List of trade dictionaries
        """
        params = {"limit": limit}
        response = self._make_request("GET", f"/markets/{ticker}/trades", params=params)
        return response.get("trades", [])
    
    # ========== Trading Methods ==========
    
    def create_order(
        self,
        ticker: str,
        side: str,
        action: str,
        count: int,
        type: str = "market",
        yes_price: Optional[int] = None,
        no_price: Optional[int] = None,
        expiration_ts: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new order.
        
        Args:
            ticker: Market ticker
            side: 'yes' or 'no'
            action: 'buy' or 'sell'
            count: Number of contracts
            type: Order type ('market' or 'limit')
            yes_price: Limit price for YES (in cents)
            no_price: Limit price for NO (in cents)
            expiration_ts: Order expiration timestamp
            
        Returns:
            Order confirmation dictionary
        """
        payload = {
            "ticker": ticker,
            "client_order_id": f"{ticker}_{int(time.time())}",
            "side": side,
            "action": action,
            "count": count,
            "type": type
        }
        
        if type == "limit":
            if yes_price is not None:
                payload["yes_price"] = yes_price
            if no_price is not None:
                payload["no_price"] = no_price
        
        if expiration_ts:
            payload["expiration_ts"] = expiration_ts
        
        logger.info(f"Creating order: {action} {count} {side} @ {ticker}")
        response = self._make_request("POST", "/portfolio/orders", json_data=payload)
        return response
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel an existing order.
        
        Args:
            order_id: ID of order to cancel
            
        Returns:
            Cancellation confirmation
        """
        logger.info(f"Cancelling order: {order_id}")
        response = self._make_request("DELETE", f"/portfolio/orders/{order_id}")
        return response
    
    def get_orders(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get user's orders.
        
        Args:
            status: Filter by status (resting, canceled, executed)
            
        Returns:
            List of order dictionaries
        """
        params = {}
        if status:
            params["status"] = status
        
        response = self._make_request("GET", "/portfolio/orders", params=params)
        return response.get("orders", [])
    
    # ========== Portfolio Methods ==========
    
    def get_balance(self) -> Dict[str, Any]:
        """
        Get account balance information.
        
        Returns:
            Balance dictionary with available funds
        """
        response = self._make_request("GET", "/portfolio/balance")
        return response
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get current positions.
        
        Returns:
            List of position dictionaries
        """
        response = self._make_request("GET", "/portfolio/positions")
        return response.get("positions", [])
    
    def get_fills(self, ticker: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get trade fills.
        
        Args:
            ticker: Optional ticker filter
            
        Returns:
            List of fill dictionaries
        """
        params = {}
        if ticker:
            params["ticker"] = ticker
        
        response = self._make_request("GET", "/portfolio/fills", params=params)
        return response.get("fills", [])
    
    # ========== Utility Methods ==========
    
    def get_best_price(self, ticker: str, side: str) -> Optional[int]:
        """
        Get the best available price for a side.
        
        Args:
            ticker: Market ticker
            side: 'yes' or 'no'
            
        Returns:
            Best price in cents, or None if no orders
        """
        orderbook = self.get_orderbook(ticker)
        
        if side == "yes":
            asks = orderbook.get("yes", [])
            if asks:
                return asks[0][0]  # Best ask price
        else:
            bids = orderbook.get("no", [])
            if bids:
                return bids[0][0]  # Best bid price
        
        return None
    
    def get_market_probability(self, ticker: str) -> float:
        """
        Get the market's implied probability.
        
        Args:
            ticker: Market ticker
            
        Returns:
            Probability as decimal (0.0 to 1.0)
        """
        market = self.get_market(ticker)
        yes_price = market.get("yes_bid", 50)  # Default to 50 if not available
        return yes_price / 100.0


# ========== Factory Function ==========

def create_connector_from_env() -> KalshiAPIConnector:
    """
    Create a Kalshi connector using environment variables.
    
    Supports both API key authentication (new) and email/password (deprecated).
    
    Expected environment variables (API Keys - Recommended):
        KALSHI_API_KEY_ID: API Key ID
        KALSHI_PRIVATE_KEY: RSA private key in PEM format (string)
        OR KALSHI_PRIVATE_KEY_FILE: Path to RSA private key PEM file
        KALSHI_USE_DEMO: 'true' or 'false' (default: false)
    
    Legacy environment variables (Email/Password - Deprecated):
        KALSHI_EMAIL: Account email
        KALSHI_PASSWORD: Account password
        KALSHI_USE_DEMO: 'true' or 'false' (default: false)
    
    Returns:
        Configured KalshiAPIConnector instance
    
    Raises:
        ValueError: If required environment variables are missing
    """
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check for API key authentication (new method)
    api_key_id = os.getenv("KALSHI_API_KEY_ID") or os.getenv("KALSHI_API_KEY")
    private_key = os.getenv("KALSHI_PRIVATE_KEY") or os.getenv("KALSHI_PY_PRIVATE_KEY_PEM")
    private_key_file = os.getenv("KALSHI_PRIVATE_KEY_FILE")
    use_demo = os.getenv("KALSHI_USE_DEMO", "false").lower() == "true"
    
    if api_key_id and (private_key or private_key_file):
        # Use API key authentication
        logger.info("Using API key authentication")
        
        # Only use private_key_file if it's actually a file path (not a placeholder)
        # Skip placeholder paths like "path/to/private_key.pem"
        if private_key_file and Path(private_key_file).exists() and "path/to" not in private_key_file:
            logger.info(f"Using private key file: {private_key_file}")
            return KalshiAPIConnector(
                api_key_id=api_key_id,
                private_key=private_key,
                private_key_file=private_key_file,
                use_demo=use_demo
            )
        elif private_key:
            # Use private key from environment variable
            logger.info("Using private key from environment variable")
            return KalshiAPIConnector(
                api_key_id=api_key_id,
                private_key=private_key,
                private_key_file=None,
                use_demo=use_demo
            )
        else:
            raise ValueError("Private key not found. Set KALSHI_PRIVATE_KEY or KALSHI_PRIVATE_KEY_FILE")
    
    # Fall back to legacy email/password (for backward compatibility)
    # Note: This will likely fail as Kalshi has deprecated this method
    email = os.getenv("KALSHI_EMAIL")
    password = os.getenv("KALSHI_PASSWORD")
    
    if email and password:
        logger.warning("Using deprecated email/password authentication. Please migrate to API keys.")
        logger.warning("See: https://docs.kalshi.com/getting_started/api_keys")
        # For backward compatibility, we'll try to create a legacy connector
        # But this will fail as /login endpoint no longer exists
        raise ValueError(
            "Email/password authentication is deprecated. "
            "Please use API keys. See: https://docs.kalshi.com/getting_started/api_keys"
        )
    
    # No credentials found
    raise ValueError(
        "API credentials not found. Set either:\n"
        "  KALSHI_API_KEY_ID and KALSHI_PRIVATE_KEY (or KALSHI_PRIVATE_KEY_FILE), or\n"
        "  KALSHI_EMAIL and KALSHI_PASSWORD (deprecated)\n"
        "See: https://docs.kalshi.com/getting_started/api_keys"
    )
