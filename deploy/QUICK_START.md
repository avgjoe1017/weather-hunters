# Quick Start - Connect to Your Droplet

## Your Droplet Details

- **Name**: `ubuntu-s-1vcpu-1gb-sfo2-01`
- **IP Address**: `165.22.172.211`
- **Specs**: 1 GB RAM / 25 GB Disk / Ubuntu 25.04 x64
- **Location**: SFO2 (San Francisco)

---

## Connect via SSH

### Option 1: Git Bash (Recommended)

Open Git Bash and run:

```bash
ssh -i ~/.ssh/weather_bot_key root@165.22.172.211
```

### Option 2: PowerShell

```powershell
ssh -i C:/Users/joeba/.ssh/weather_bot_key root@165.22.172.211
```

### Option 3: Double-click script

Run `deploy/connect_droplet.bat` (opens Git Bash with command)

---

## First Connection

On first connection, you'll see:

```
The authenticity of host '165.22.172.211' can't be established.
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

Type `yes` and press Enter.

---

## After Connecting

Once you're connected to your droplet, run the setup script:

### If your repo is on GitHub:

```bash
# Clone and run setup
git clone https://github.com/YOUR_USERNAME/weather-hunters.git /opt/weather-hunters
cd /opt/weather-hunters
chmod +x deploy/digitalocean_setup.sh
./deploy/digitalocean_setup.sh
```

### If you need to upload files:

From your local machine (in PowerShell):

```powershell
# Upload setup script
scp -i C:/Users/joeba/.ssh/weather_bot_key deploy/digitalocean_setup.sh root@165.22.172.211:/tmp/

# Upload entire project (if not using git)
# Install rsync first or use SCP recursively
```

Then on the droplet:

```bash
chmod +x /tmp/digitalocean_setup.sh
/tmp/digitalocean_setup.sh
```

---

## Next Steps

1. ✅ **Connect to droplet** (you're here)
2. ⏭️ **Run setup script** (`deploy/digitalocean_setup.sh`)
3. ⏭️ **Configure .env** file with your Kalshi credentials
4. ⏭️ **Test scripts** manually
5. ⏭️ **Verify cron jobs** are installed
6. ⏭️ **Monitor first run** tomorrow morning

---

## Quick Reference Commands

```bash
# Connect
ssh -i ~/.ssh/weather_bot_key root@165.22.172.211

# After setup, check cron jobs
crontab -l

# View logs
tail -f /opt/weather-hunters/logs/cron_morning.log
tail -f /opt/weather-hunters/logs/cron_settle.log

# Manual test
cd /opt/weather-hunters && source venv/bin/activate
python scripts/paper_trade_morning.py
python scripts/settle_live_data.py
```

---

**Ready to connect?** Use the SSH command above!
