# Kalshi API Authentication Update

## Current Status (2025-11-02)

Based on [Kalshi's official documentation](https://docs.kalshi.com/welcome), the API authentication has changed:

### Key Changes

1. **API Keys Required**: Kalshi now uses API key authentication with RSA private keys instead of email/password
   - See: [API Keys Documentation](https://docs.kalshi.com/getting_started/api_keys)

2. **Production Endpoint Updated**: 
   - Old: `https://trading-api.kalshi.com/trade-api/v2`
   - New: `https://api.elections.kalshi.com/trade-api/v2`

3. **Demo Environment**: 
   - Demo endpoint may be deprecated or moved
   - Current: `https://demo-api.kalshi.co/trade-api/v2` (returns 404)
   - May require API keys instead of email/password

### Current Codebase Status

**This codebase currently uses email/password authentication**, which may be:
- Still supported for production (needs testing)
- Deprecated in favor of API keys

### Next Steps

#### Option A: Test Email/Password Authentication (Current Method)

The codebase is configured for email/password authentication. Test it with production:

1. Set `KALSHI_USE_DEMO=false` in your `.env` file
2. Test connection: `python scripts/verify_setup.py`
3. If it works, you're good to go!

#### Option B: Migrate to API Keys (Recommended by Kalshi)

According to [Kalshi's documentation](https://docs.kalshi.com/getting_started/api_keys):

1. **Generate API Keys**:
   - Log in to [Kalshi Account Settings](https://kalshi.com/account/profile)
   - Navigate to "API Keys" section
   - Click "Create New API Key"
   - Save the API Key ID and private key securely

2. **Update Environment Variables**:
   
   **Option A: Private key as string (recommended for .env file)**
   ```bash
   KALSHI_API_KEY_ID=your-api-key-id
   KALSHI_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----
   MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC...
   ...
   -----END PRIVATE KEY-----
   ```
   
   **Important**: The private key must include the `-----BEGIN PRIVATE KEY-----` and `-----END PRIVATE KEY-----` markers. If your key doesn't have these, wrap it like this:
   ```bash
   KALSHI_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYOUR_BASE64_KEY_HERE\n-----END PRIVATE KEY-----"
   ```
   
   Or use a file:
   ```bash
   KALSHI_API_KEY_ID=your-api-key-id
   KALSHI_PRIVATE_KEY_FILE=path/to/private_key.pem
   ```

3. **Update Connector Code**:
   - Modify `src/api/kalshi_connector.py` to use API key authentication
   - Use RSA private key signing instead of email/password
   - Follow examples in [Kalshi Python SDK](https://docs.kalshi.com/python-sdk)

### Resources

- [Kalshi API Documentation](https://docs.kalshi.com/welcome)
- [API Keys Guide](https://docs.kalshi.com/getting_started/api_keys)
- [Python SDK](https://docs.kalshi.com/python-sdk)
- [API Reference](https://docs.kalshi.com/api-reference)
- [Demo Environment](https://docs.kalshi.com/getting_started/demo_env) (if available)

### Testing

To test your current setup:

```bash
# Test with production (real credentials)
python scripts/verify_setup.py

# Or test connection directly
python -c "from src.api.kalshi_connector import create_connector_from_env; api = create_connector_from_env(); print(f'Balance: ${api.get_balance()[\"balance\"]/100:.2f}')"
```

---

**Last Updated**: 2025-11-02  
**Status**: Production endpoint updated, demo endpoint needs verification

