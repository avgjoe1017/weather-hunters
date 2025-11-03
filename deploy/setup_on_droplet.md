# Setup Trading Bot on Droplet

You're now connected! Here's what to do next.

---

## Step 1: Clone Repository (or Upload Files)

### Option A: If Your Repo is on GitHub (Public)

```bash
# Install git if needed
apt update
apt install -y git

# Clone repository
git clone https://github.com/YOUR_USERNAME/weather-hunters.git /opt/weather-hunters

# Go to project directory
cd /opt/weather-hunters
```

### Option B: If Your Repo is Private or Local

You'll need to upload files via SCP from your local machine.

**From your local machine (Git Bash):**
```bash
# Upload entire project (excluding venv, cache, etc.)
rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '.git' \
    -e "ssh -i ~/.ssh/weather_bot_key_new" \
    ./ root@165.22.172.211:/opt/weather-hunters/
```

**OR using SCP:**
```bash
# Create directory on droplet first
ssh -i ~/.ssh/weather_bot_key_new root@165.22.172.211 "mkdir -p /opt/weather-hunters"

# Upload project files
scp -i ~/.ssh/weather_bot_key_new -r . root@165.22.172.211:/opt/weather-hunters/
```

---

## Step 2: Run Setup Script

```bash
# Navigate to project
cd /opt/weather-hunters

# Make setup script executable
chmod +x deploy/digitalocean_setup.sh

# Run setup script
./deploy/digitalocean_setup.sh
```

The setup script will:
- ✅ Install system dependencies
- ✅ Create Python virtual environment
- ✅ Install Python packages
- ✅ Setup cron jobs
- ✅ Configure log rotation
- ⚠️ **Prompt you to configure .env file**

---

## Step 3: Configure .env File

When the setup script prompts you:

1. **Edit .env file:**
   ```bash
   nano /opt/weather-hunters/.env
   ```

2. **Add your Kalshi credentials:**
   ```bash
   KALSHI_API_KEY_ID=your_key_id_here
   KALSHI_PRIVATE_KEY_FILE=/opt/weather-hunters/kalshi_private_key.pem
   # OR
   KALSHI_PRIVATE_KEY=your_full_private_key_here
   ```

3. **If using private key file, upload it:**
   
   **From your local machine:**
   ```bash
   scp -i ~/.ssh/weather_bot_key_new kalshi_private_key.pem root@165.22.172.211:/opt/weather-hunters/
   ```

4. **Save and exit** (Ctrl+X, then Y, then Enter)

5. **Set secure permissions:**
   ```bash
   chmod 600 /opt/weather-hunters/.env
   chmod 600 /opt/weather-hunters/kalshi_private_key.pem
   ```

---

## Step 4: Test Manually

Before relying on cron jobs, test the scripts manually:

```bash
cd /opt/weather-hunters
source venv/bin/activate

# Test morning script
python scripts/paper_trade_morning.py

# Test settlement script (if you have any pending predictions)
python scripts/settle_live_data.py

# Test health check
python scripts/health_check.py
```

**Expected output:**
- Morning script should log predictions to `logs/live_validation.csv`
- Health check should show system status
- No errors should occur

---

## Step 5: Verify Cron Jobs

```bash
# Check cron jobs are installed
crontab -l

# Should see:
# - Morning predictions at 14:00 UTC (9 AM EST)
# - Evening settlement at 01:00 UTC (8 PM EST)
# - Health check at 17:00 UTC (noon EST)
# - Weekly analysis on Monday at 07:00 UTC
```

---

## Step 6: Monitor First Run

### View Logs in Real-Time

```bash
# Morning predictions log
tail -f /opt/weather-hunters/logs/cron_morning.log

# Evening settlement log
tail -f /opt/weather-hunters/logs/cron_settle.log

# All logs
tail -f /opt/weather-hunters/logs/*.log
```

### Check Tomorrow Morning (9 AM EST)

Tomorrow at 9 AM EST (14:00 UTC), check:

```bash
# View today's predictions
cat /opt/weather-hunters/logs/live_validation.csv

# Check morning log
cat /opt/weather-hunters/logs/cron_morning.log
```

### Check Tomorrow Evening (8 PM EST)

Tomorrow at 8 PM EST (01:00 UTC next day), check:

```bash
# View updated outcomes (WIN/LOSS)
cat /opt/weather-hunters/logs/live_validation.csv

# Check settlement log
cat /opt/weather-hunters/logs/cron_settle.log
```

---

## Quick Reference Commands

```bash
# Connect to droplet
ssh -i ~/.ssh/weather_bot_key_new root@165.22.172.211

# View logs
tail -f /opt/weather-hunters/logs/cron_morning.log
tail -f /opt/weather-hunters/logs/cron_settle.log

# Manual execution
cd /opt/weather-hunters && source venv/bin/activate
python scripts/paper_trade_morning.py
python scripts/settle_live_data.py
python scripts/analyze_paper_trades.py

# Check cron
crontab -l

# Update code (if using git)
cd /opt/weather-hunters && git pull
source venv/bin/activate
pip install -r requirements.txt
```

---

## Troubleshooting

### Script Errors

```bash
# Check error logs
cat /opt/weather-hunters/logs/cron_morning.log
cat /opt/weather-hunters/logs/cron_settle.log

# Run manually to see full error
cd /opt/weather-hunters
source venv/bin/activate
python scripts/paper_trade_morning.py
```

### Cron Not Running

```bash
# Check cron service
systemctl status cron

# Restart if needed
systemctl restart cron

# Check cron logs
grep CRON /var/log/syslog
```

### Missing Dependencies

```bash
cd /opt/weather-hunters
source venv/bin/activate
pip install -r requirements.txt
```

### API Connection Issues

```bash
# Test API connection
cd /opt/weather-hunters
source venv/bin/activate
python -c "from src.api.kalshi_connector import create_connector_from_env; api = create_connector_from_env(); print(api.get_balance())"

# Verify .env file
cat .env
nano .env  # Check credentials are correct
```

---

## Next Steps

1. ✅ **Setup complete** - Bot will run automatically
2. ⏭️ **Wait for first run** - Check logs tomorrow morning (9 AM EST)
3. ⏭️ **Monitor for 1 week** - Verify everything works
4. ⏭️ **Run analysis** - After 14-30 days, run `analyze_paper_trades.py`
5. ⏭️ **Make decision** - Based on forward test results

---

**You're all set!** The bot will run automatically on schedule.
