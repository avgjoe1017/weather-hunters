# DigitalOcean Droplet Setup Guide

Complete step-by-step guide to deploy the forward test on a DigitalOcean droplet.

---

## Prerequisites

- DigitalOcean account (sign up at https://www.digitalocean.com)
- $6/month for droplet
- SSH key pair (for secure access)

---

## Step 1: Create Droplet

### Via DigitalOcean Web UI

1. **Login to DigitalOcean**: https://cloud.digitalocean.com

2. **Create Droplet**:
   - Click "Create" → "Droplets"
   - **Choose an image**: Ubuntu 22.04 LTS
   - **Choose a plan**: Basic → Regular Intel with SSD → **$6/month** option
   - **Choose a datacenter**: Select closest to you (lower latency)
   - **Authentication**: 
     - ✅ SSH keys (recommended - add your public key)
     - OR Root password (less secure)
   - **Hostname**: `weather-bot` (optional)
   - Click **"Create Droplet"**

3. **Wait for creation** (~60 seconds)

4. **Note the IP address** - You'll need this to SSH

---

## Step 2: SSH Into Droplet

### On Windows (PowerShell)

```powershell
# Using SSH key (recommended)
ssh -i path\to\your\private_key root@YOUR_DROPLET_IP

# OR using password
ssh root@YOUR_DROPLET_IP
```

### On Mac/Linux

```bash
# Using SSH key
ssh -i ~/.ssh/id_rsa root@YOUR_DROPLET_IP

# OR using password
ssh root@YOUR_DROPLET_IP
```

**First time connection**: You'll see a security warning - type `yes` to continue.

---

## Step 3: Run Setup Script

### Option A: Automated Setup (Recommended)

#### If your repo is public on GitHub:

```bash
# Download and run setup script
curl -o /tmp/setup.sh https://raw.githubusercontent.com/YOUR_USERNAME/weather-hunters/main/deploy/digitalocean_setup.sh

# OR clone repo first, then run:
git clone https://github.com/YOUR_USERNAME/weather-hunters.git /opt/weather-hunters
cd /opt/weather-hunters
chmod +x deploy/digitalocean_setup.sh
./deploy/digitalocean_setup.sh
```

#### If your repo is private or local:

**1. Upload setup script:**

From your local machine:
```bash
# Windows PowerShell
scp -i your_key deploy/digitalocean_setup.sh root@YOUR_DROPLET_IP:/tmp/

# Mac/Linux
scp -i ~/.ssh/id_rsa deploy/digitalocean_setup.sh root@YOUR_DROPLET_IP:/tmp/
```

**2. Upload project files (if not using git):**

```bash
# From project root on local machine
rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '.git' \
    -e "ssh -i your_key" \
    ./ root@YOUR_DROPLET_IP:/opt/weather-hunters/
```

**3. Run setup on droplet:**

```bash
ssh root@YOUR_DROPLET_IP
chmod +x /tmp/digitalocean_setup.sh
/tmp/digitalocean_setup.sh https://github.com/YOUR_USERNAME/weather-hunters.git
```

### Option B: Manual Setup

If automated setup doesn't work, follow the manual steps below.

---

## Step 4: Manual Setup (If Automated Fails)

### 4.1 Update System

```bash
apt update
apt upgrade -y
```

### 4.2 Install Dependencies

```bash
apt install -y python3.10 python3-pip python3.10-venv git cron curl nano
```

### 4.3 Clone Repository

```bash
mkdir -p /opt
cd /opt
git clone https://github.com/YOUR_USERNAME/weather-hunters.git weather-hunters
cd weather-hunters
```

**OR** if repo is private, upload files via SCP/rsync (see Step 3).

### 4.4 Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4.5 Configure Environment

```bash
# Copy template
cp .env.template .env

# Edit with your credentials
nano .env
```

Add your Kalshi credentials:
```bash
KALSHI_API_KEY_ID=your_key_id_here
KALSHI_PRIVATE_KEY_FILE=/opt/weather-hunters/kalshi_private_key.pem
# OR
KALSHI_PRIVATE_KEY=your_full_private_key_here
```

**If using private key file**, upload it:
```bash
# From local machine
scp -i your_key kalshi_private_key.pem root@YOUR_DROPLET_IP:/opt/weather-hunters/
```

### 4.6 Create Directories

```bash
mkdir -p logs metrics data/weather
```

### 4.7 Setup Cron Jobs

```bash
crontab -e
```

Add these lines (times are UTC):
```cron
# Morning predictions at 9 AM EST (14:00 UTC)
0 14 * * * cd /opt/weather-hunters && /opt/weather-hunters/venv/bin/python scripts/paper_trade_morning.py >> /opt/weather-hunters/logs/cron_morning.log 2>&1

# Evening settlement at 8 PM EST (01:00 UTC next day)
0 1 * * * cd /opt/weather-hunters && /opt/weather-hunters/venv/bin/python scripts/settle_live_data.py >> /opt/weather-hunters/logs/cron_settle.log 2>&1

# Daily health check at noon EST (17:00 UTC)
0 17 * * * cd /opt/weather-hunters && /opt/weather-hunters/venv/bin/python scripts/health_check.py >> /opt/weather-hunters/logs/cron_health.log 2>&1
```

Save and exit (`Ctrl+X`, then `Y`, then `Enter`).

### 4.8 Setup Log Rotation

```bash
cat > /etc/logrotate.d/weather-hunters <<'EOF'
/opt/weather-hunters/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
EOF
```

---

## Step 5: Test Setup

### 5.1 Test Morning Script

```bash
cd /opt/weather-hunters
source venv/bin/activate
python scripts/paper_trade_morning.py
```

**Expected output:**
```
==============================================================================
PAPER TRADING - MORNING ROUTINE
==============================================================================
...
[OK] Predictions logged to logs/live_validation.csv
```

### 5.2 Test Settlement Script

```bash
python scripts/settle_live_data.py
```

**Expected output:**
```
==============================================================================
SETTLEMENT SCRIPT - The "Unblinding"
==============================================================================
...
[OK] Settlement data updated
```

### 5.3 Verify Cron Jobs

```bash
# List installed cron jobs
crontab -l

# Test cron manually (runs immediately)
cd /opt/weather-hunters && /opt/weather-hunters/venv/bin/python scripts/paper_trade_morning.py
```

### 5.4 Check Logs

```bash
# View logs
tail -f logs/cron_morning.log
tail -f logs/cron_settle.log

# Check if files are being created
ls -lh logs/
```

---

## Step 6: Verify Scheduled Runs

### Wait for Next Scheduled Time

- **Morning predictions**: 9 AM EST (14:00 UTC)
- **Evening settlement**: 8 PM EST (01:00 UTC)

### Check After First Run

```bash
# Morning after first run (check around 9:30 AM EST)
cat logs/cron_morning.log
cat logs/live_validation.csv

# Evening after first settlement (check around 8:30 PM EST)
cat logs/cron_settle.log
cat logs/live_validation.csv  # Should show WIN/LOSS outcomes
```

---

## Step 7: Monitoring & Maintenance

### View Logs

```bash
# Real-time log monitoring
tail -f logs/cron_morning.log
tail -f logs/cron_settle.log
tail -f logs/live_validation.csv

# Check all logs
ls -lh logs/
```

### View Cron Job Status

```bash
# List all cron jobs
crontab -l

# Check cron service status
systemctl status cron
```

### Check System Resources

```bash
# CPU and memory usage
htop

# Disk usage
df -h

# Check if Python processes are running
ps aux | grep python
```

### Manual Script Execution

```bash
cd /opt/weather-hunters
source venv/bin/activate

# Run morning predictions manually
python scripts/paper_trade_morning.py

# Run settlement manually
python scripts/settle_live_data.py

# Run analysis
python scripts/analyze_paper_trades.py

# Health check
python scripts/health_check.py
```

---

## Step 8: Update Code

### If Using Git

```bash
cd /opt/weather-hunters
git pull
source venv/bin/activate
pip install -r requirements.txt  # If dependencies changed
```

### If Not Using Git

Upload updated files via SCP/rsync (see Step 3).

---

## Troubleshooting

### Cron Jobs Not Running

```bash
# Check cron service
systemctl status cron
systemctl restart cron

# Check cron logs
grep CRON /var/log/syslog

# Verify cron jobs are installed
crontab -l
```

### Script Errors

```bash
# Check error logs
cat logs/cron_morning.log
cat logs/cron_settle.log

# Run manually to see full error
cd /opt/weather-hunters
source venv/bin/activate
python scripts/paper_trade_morning.py
```

### Permission Issues

```bash
# Ensure scripts are executable
chmod +x scripts/*.py

# Check file permissions
ls -la scripts/
ls -la logs/
```

### Missing Dependencies

```bash
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

### Timezone Issues

```bash
# Check server timezone
timedatectl

# Set timezone to UTC (recommended for cron)
timedatectl set-timezone UTC

# Verify cron times are correct
# Remember: cron uses server timezone, not EST
```

---

## Security Best Practices

### 1. Use SSH Keys (Not Passwords)

```bash
# On local machine, generate SSH key if needed
ssh-keygen -t ed25519 -C "your_email@example.com"

# Copy public key to droplet
ssh-copy-id root@YOUR_DROPLET_IP
```

### 2. Disable Root Password Login

After setting up SSH keys:

```bash
nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
systemctl restart sshd
```

### 3. Use Firewall

```bash
# Install UFW
apt install ufw

# Allow SSH (important!)
ufw allow 22/tcp

# Enable firewall
ufw enable

# Check status
ufw status
```

### 4. Keep System Updated

```bash
# Regular updates
apt update && apt upgrade -y
```

### 5. Secure .env File

```bash
# Restrict permissions
chmod 600 /opt/weather-hunters/.env
chmod 600 /opt/weather-hunters/kalshi_private_key.pem
```

---

## Cost Management

### Current Costs
- **Droplet**: $6/month (Basic plan)
- **Bandwidth**: Free (first 1TB)
- **Storage**: Included (25GB)

### Optional: Enable Backup ($1/month)
- In DigitalOcean dashboard
- Droplet → Settings → Backups
- Enable daily backups

### Optional: Enable Monitoring ($1/month)
- In DigitalOcean dashboard
- Droplet → Monitoring
- Get alerts and metrics

**Total: ~$6-8/month** for basic setup

---

## Next Steps

1. ✅ **Setup complete** - Bot will run automatically
2. ⏭️ **Wait for first run** - Check logs tomorrow morning
3. ⏭️ **Monitor for 1 week** - Verify everything works
4. ⏭️ **Run analysis** - After 14-30 days, run `analyze_paper_trades.py`
5. ⏭️ **Make decision** - Based on forward test results

---

## Useful Commands Cheat Sheet

```bash
# SSH into droplet
ssh root@YOUR_DROPLET_IP

# View logs
tail -f /opt/weather-hunters/logs/cron_morning.log
tail -f /opt/weather-hunters/logs/cron_settle.log

# Manual execution
cd /opt/weather-hunters && source venv/bin/activate
python scripts/paper_trade_morning.py
python scripts/settle_live_data.py
python scripts/analyze_paper_trades.py

# Update code
cd /opt/weather-hunters && git pull

# Check cron
crontab -l
systemctl status cron

# System monitoring
htop
df -h
```

---

## Support

- **DigitalOcean Docs**: https://docs.digitalocean.com
- **DigitalOcean Community**: https://www.digitalocean.com/community
- **Your project docs**: See `Documentation/` folder

---

**Last Updated**: 2025-11-03
