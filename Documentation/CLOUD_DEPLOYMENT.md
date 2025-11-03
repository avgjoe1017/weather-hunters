# Cloud Deployment Guide

This guide shows how to deploy the forward test (or full trading bot) to the cloud instead of running locally.

## Quick Comparison

| Option | Cost | Complexity | Best For |
|-------|------|------------|----------|
| **AWS Lambda** | Free tier, then ~$1/month | Medium | Forward test only (scheduled) |
| **DigitalOcean Droplet** | $6/month | Low | Simple, persistent |
| **Railway** | Free tier, then ~$5/month | Low | Easy, managed |
| **AWS EC2** | ~$10/month | Medium | Full trading bot |
| **GitHub Actions** | Free | Low | Scheduled tasks only |

---

## Option 1: AWS Lambda (Recommended for Forward Test)

**Best for:** Scheduled forward test (morning + evening scripts)

**Why:** Serverless, pay-per-execution, automatic scheduling, free tier generous

### Setup Steps

#### 1. Create AWS Account & Setup

```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure
# Enter your AWS Access Key ID, Secret Access Key, region (us-east-1)
```

#### 2. Create Deployment Package

Create `deploy/lambda_morning.py`:
```python
"""
Lambda handler for morning predictions
"""
import json
import sys
import os
from pathlib import Path

# Add project to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def lambda_handler(event, context):
    """AWS Lambda handler"""
    # Import after path setup
    from scripts.paper_trade_morning import main as morning_main
    
    try:
        morning_main()
        return {
            'statusCode': 200,
            'body': json.dumps('Morning predictions logged successfully')
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }
```

Create `deploy/lambda_settle.py`:
```python
"""
Lambda handler for evening settlement
"""
import json
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def lambda_handler(event, context):
    """AWS Lambda handler"""
    from scripts.settle_live_data import main as settle_main
    
    try:
        settle_main()
        return {
            'statusCode': 200,
            'body': json.dumps('Settlement data updated successfully')
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }
```

#### 3. Package Dependencies

Create `deploy/build_lambda.sh`:
```bash
#!/bin/bash
# Build Lambda deployment package

PROJECT_ROOT=$(pwd)
BUILD_DIR="$PROJECT_ROOT/deploy/lambda_package"
mkdir -p "$BUILD_DIR"

# Install dependencies to package
pip install -r requirements.txt -t "$BUILD_DIR" --no-cache-dir

# Copy project code
cp -r "$PROJECT_ROOT/src" "$BUILD_DIR/"
cp -r "$PROJECT_ROOT/scripts" "$BUILD_DIR/"
cp -r "$PROJECT_ROOT/models" "$BUILD_DIR/"
mkdir -p "$BUILD_DIR/logs"

# Copy Lambda handlers
cp "$PROJECT_ROOT/deploy/lambda_morning.py" "$BUILD_DIR/"
cp "$PROJECT_ROOT/deploy/lambda_settle.py" "$BUILD_DIR/"

# Create ZIP
cd "$BUILD_DIR"
zip -r "$PROJECT_ROOT/deploy/morning_function.zip" . -x "*.pyc" "__pycache__/*" "*.git*"
zip -r "$PROJECT_ROOT/deploy/settle_function.zip" . -x "*.pyc" "__pycache__/*" "*.git*"

echo "Packages created:"
echo "  - deploy/morning_function.zip"
echo "  - deploy/settle_function.zip"
```

#### 4. Deploy with AWS CLI

Create `deploy/deploy_lambda.sh`:
```bash
#!/bin/bash
# Deploy Lambda functions

# Morning function (runs at 9 AM EST = 14:00 UTC)
aws lambda create-function \
    --function-name weather-forward-test-morning \
    --runtime python3.9 \
    --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
    --handler lambda_morning.lambda_handler \
    --zip-file fileb://morning_function.zip \
    --timeout 300 \
    --memory-size 512 \
    --environment Variables="{
        KALSHI_API_KEY_ID=${KALSHI_API_KEY_ID},
        KALSHI_PRIVATE_KEY_FILE=${KALSHI_PRIVATE_KEY},
        AWS_S3_BUCKET=${AWS_S3_BUCKET}
    }"

# Evening function (runs at 8 PM EST = 01:00 UTC next day)
aws lambda create-function \
    --function-name weather-forward-test-settle \
    --runtime python3.9 \
    --role arn:aws:iam::YOUR_ACCOUNT_ID:role/lambda-execution-role \
    --handler lambda_settle.lambda_handler \
    --zip-file fileb://settle_function.zip \
    --timeout 300 \
    --memory-size 512 \
    --environment Variables="{
        AWS_S3_BUCKET=${AWS_S3_BUCKET}
    }"

# Create EventBridge rules for scheduling
aws events put-rule \
    --name morning-predictions \
    --schedule-expression "cron(0 14 * * ? *)" \
    --description "Run morning predictions at 9 AM EST"

aws events put-rule \
    --name evening-settlement \
    --schedule-expression "cron(0 1 * * ? *)" \
    --description "Run settlement at 8 PM EST"

# Connect rules to functions
aws lambda add-permission \
    --function-name weather-forward-test-morning \
    --statement-id allow-eventbridge \
    --action 'lambda:InvokeFunction' \
    --principal events.amazonaws.com \
    --source-arn arn:aws:events:us-east-1:YOUR_ACCOUNT_ID:rule/morning-predictions

aws lambda add-permission \
    --function-name weather-forward-test-settle \
    --statement-id allow-eventbridge \
    --action 'lambda:InvokeFunction' \
    --principal events.amazonaws.com \
    --source-arn arn:aws:events:us-east-1:YOUR_ACCOUNT_ID:rule/evening-settlement

# Add targets
aws events put-targets \
    --rule morning-predictions \
    --targets "Id=1,Arn=arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:weather-forward-test-morning"

aws events put-targets \
    --rule evening-settlement \
    --targets "Id=1,Arn=arn:aws:lambda:us-east-1:YOUR_ACCOUNT_ID:function:weather-forward-test-settle"
```

#### 5. Store State in S3

Modify scripts to read/write from S3 instead of local files:
```python
import boto3
import pandas as pd

s3 = boto3.client('s3')
BUCKET = os.environ['AWS_S3_BUCKET']
LOG_FILE = 'live_validation.csv'

def load_log():
    """Load log from S3"""
    try:
        obj = s3.get_object(Bucket=BUCKET, Key=LOG_FILE)
        return pd.read_csv(obj['Body'])
    except:
        return pd.DataFrame()

def save_log(df):
    """Save log to S3"""
    s3.put_object(
        Bucket=BUCKET,
        Key=LOG_FILE,
        Body=df.to_csv(index=False)
    )
```

**Cost:** Free tier (1M requests/month), then ~$0.20 per 1M requests  
**Setup Time:** ~2 hours  
**Pros:** Serverless, auto-scaling, no server management  
**Cons:** 15-minute timeout limit, need to package dependencies

---

## Option 2: DigitalOcean Droplet (Simplest Persistent Option)

**Best for:** Full trading bot or forward test with persistent state

**Why:** $6/month, simple setup, full control, persistent storage

### Setup Steps

#### 1. Create Droplet

```bash
# Via web UI: https://cloud.digitalocean.com
# Choose: Ubuntu 22.04, Basic plan, $6/month, datacenter closest to you
```

#### 2. SSH & Initial Setup

```bash
ssh root@YOUR_DROPLET_IP

# Update system
apt update && apt upgrade -y

# Install Python 3.10+
apt install python3-pip python3-venv git -y

# Clone repo
cd /opt
git clone YOUR_REPO_URL weather-hunters
cd weather-hunters

# Create venv and install
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup .env
nano .env
# Add your Kalshi credentials
```

#### 3. Setup Cron Jobs

```bash
# Edit crontab
crontab -e

# Add these lines (adjust times for EST):
# Morning predictions at 9 AM EST = 14:00 UTC
0 14 * * * cd /opt/weather-hunters && /opt/weather-hunters/venv/bin/python scripts/paper_trade_morning.py >> logs/cron.log 2>&1

# Evening settlement at 8 PM EST = 01:00 UTC next day
0 1 * * * cd /opt/weather-hunters && /opt/weather-hunters/venv/bin/python scripts/settle_live_data.py >> logs/cron.log 2>&1

# Optional: Daily health check
0 12 * * * cd /opt/weather-hunters && /opt/weather-hunters/venv/bin/python scripts/health_check.py >> logs/health.log 2>&1
```

#### 4. Setup Log Rotation

```bash
# Install logrotate config
cat > /etc/logrotate.d/weather-hunters <<EOF
/opt/weather-hunters/logs/*.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
}
EOF
```

#### 5. Optional: Systemd Service (for full trading bot)

Create `/etc/systemd/system/weather-bot.service`:
```ini
[Unit]
Description=Weather Trading Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/weather-hunters
Environment="PATH=/opt/weather-hunters/venv/bin"
ExecStart=/opt/weather-hunters/venv/bin/python -m src.main --live --demo
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
systemctl enable weather-bot
systemctl start weather-bot

# Check status
systemctl status weather-bot
```

**Cost:** $6/month  
**Setup Time:** ~30 minutes  
**Pros:** Simple, full control, persistent storage, can run continuously  
**Cons:** You manage the server, need to keep it updated

---

## Option 3: Railway (Easiest Managed Option)

**Best for:** Quick deployment, managed infrastructure

**Why:** Simple setup, automatic deployments, free tier

### Setup Steps

#### 1. Create Railway Account

```bash
# Visit: https://railway.app
# Sign up with GitHub
```

#### 2. Create New Project

```bash
# Via web UI:
# 1. Click "New Project"
# 2. Select "Deploy from GitHub repo"
# 3. Connect your weather-hunters repo
```

#### 3. Configure Environment Variables

In Railway dashboard:
- Go to your service
- Click "Variables" tab
- Add:
  - `KALSHI_API_KEY_ID`
  - `KALSHI_PRIVATE_KEY_FILE` (or path to file)
  - Any other `.env` variables

#### 4. Setup Scheduled Tasks

Create `railway.json`:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python scripts/paper_trade_morning.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**Note:** Railway doesn't have built-in cron. Use GitHub Actions to trigger Railway deployments.

**Cost:** Free tier (500 hours/month), then $5/month  
**Setup Time:** ~15 minutes  
**Pros:** Very easy, managed, automatic deployments  
**Cons:** Free tier limited, need external scheduler for cron

---

## Option 4: GitHub Actions (Free Scheduled Tasks)

**Best for:** Forward test with scheduled runs, no infrastructure cost

**Why:** Free, reliable, integrated with your repo

### Setup Steps

#### 1. Create GitHub Actions Workflow

Create `.github/workflows/forward-test.yml`:
```yaml
name: Forward Test Daily

on:
  schedule:
    # Morning predictions: 9 AM EST (14:00 UTC)
    - cron: '0 14 * * *'
    # Evening settlement: 8 PM EST (01:00 UTC next day)
    - cron: '0 1 * * *'
  workflow_dispatch:  # Allow manual trigger

jobs:
  morning:
    if: github.event.schedule == '0 14 * * *' || github.event_name == 'workflow_dispatch'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Setup environment
        env:
          KALSHI_API_KEY_ID: ${{ secrets.KALSHI_API_KEY_ID }}
          KALSHI_PRIVATE_KEY: ${{ secrets.KALSHI_PRIVATE_KEY }}
        run: |
          echo "$KALSHI_PRIVATE_KEY" > kalshi_private_key.pem
      
      - name: Run morning predictions
        run: |
          python scripts/paper_trade_morning.py
      
      - name: Upload logs
        uses: actions/upload-artifact@v3
        with:
          name: predictions-${{ github.run_number }}
          path: logs/live_validation.csv
          retention-days: 30

  settle:
    if: github.event.schedule == '0 1 * * *' || github.event_name == 'workflow_dispatch'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Download previous logs
        uses: actions/download-artifact@v3
        with:
          pattern: predictions-*
      
      - name: Run settlement
        run: |
          python scripts/settle_live_data.py
      
      - name: Upload updated logs
        uses: actions/upload-artifact@v3
        with:
          name: predictions-${{ github.run_number }}
          path: logs/live_validation.csv
          retention-days: 30
      
      - name: Analyze results
        run: |
          python scripts/analyze_paper_trades.py
```

#### 2. Add Secrets

In GitHub repo:
1. Go to Settings → Secrets and variables → Actions
2. Add secrets:
   - `KALSHI_API_KEY_ID`
   - `KALSHI_PRIVATE_KEY` (full key content)

#### 3. Store State Externally

**Option A: GitHub Releases** (simple, public)
```yaml
- name: Create release with logs
  uses: softprops/action-gh-release@v1
  with:
    tag_name: forward-test-${{ github.run_number }}
    files: logs/live_validation.csv
```

**Option B: AWS S3** (private, persistent)
```yaml
- name: Upload to S3
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
  run: |
    pip install awscli
    aws s3 cp logs/live_validation.csv s3://your-bucket/logs/
```

**Cost:** Free (2,000 minutes/month)  
**Setup Time:** ~30 minutes  
**Pros:** Free, reliable, integrated with repo  
**Cons:** Limited to 6 hours runtime, need external storage for state

---

## Option 5: AWS EC2 (Full Trading Bot)

**Best for:** Running full trading bot 24/7

**Why:** Persistent, can run continuously, full control

### Setup Steps

#### 1. Launch EC2 Instance

```bash
# Via AWS Console:
# 1. Launch EC2 → Ubuntu 22.04 LTS
# 2. Instance type: t3.micro (free tier) or t3.small ($10/month)
# 3. Storage: 20 GB
# 4. Security group: Allow SSH (port 22) from your IP
```

#### 2. SSH & Setup

```bash
ssh -i your-key.pem ubuntu@YOUR_EC2_IP

# Follow DigitalOcean steps above (same commands)
```

#### 3. Setup Auto-Restart on Reboot

```bash
# Use systemd service (see DigitalOcean section)
```

**Cost:** Free tier (t3.micro), then ~$10/month  
**Setup Time:** ~30 minutes  
**Pros:** Full AWS integration, scalable, persistent  
**Cons:** More complex than DigitalOcean

---

## Comparison Matrix

| Feature | AWS Lambda | DigitalOcean | Railway | GitHub Actions | AWS EC2 |
|---------|-----------|--------------|---------|----------------|---------|
| **Cost** | Free/cheap | $6/month | Free/$5 | Free | Free/$10 |
| **Setup Time** | 2 hours | 30 min | 15 min | 30 min | 30 min |
| **Persistent State** | S3 | Local disk | Ephemeral | External | Local disk |
| **Max Runtime** | 15 min | Unlimited | Unlimited | 6 hours | Unlimited |
| **Scheduling** | EventBridge | Cron | External | Built-in | Cron |
| **Best For** | Forward test | Simple bot | Quick deploy | Scheduled only | Full bot |

---

## Recommended Approach

### For Forward Test Only:
**Option: AWS Lambda** or **GitHub Actions**
- Low/no cost
- Perfect for scheduled daily runs
- No server management

### For Full Trading Bot:
**Option: DigitalOcean Droplet** or **AWS EC2**
- Persistent storage
- Can run continuously
- Full control

### Quick Start (Easiest):
**Option: GitHub Actions**
- Free
- 15-minute setup
- No infrastructure needed

---

## Security Best Practices

### 1. Never Commit Credentials
```bash
# Add to .gitignore
.env
kalshi_private_key.pem
*.key
secrets/
```

### 2. Use Environment Variables
```python
# In scripts
import os
api_key = os.environ['KALSHI_API_KEY_ID']
```

### 3. Use Cloud Secrets Management
- **AWS:** AWS Secrets Manager or Parameter Store
- **DigitalOcean:** Environment variables or Secrets
- **GitHub:** Repository Secrets (encrypted)

---

## Monitoring Setup

### CloudWatch (AWS)
```python
import boto3
cloudwatch = boto3.client('cloudwatch')

cloudwatch.put_metric_data(
    Namespace='WeatherTrading',
    MetricData=[{
        'MetricName': 'PredictionsMade',
        'Value': 1,
        'Timestamp': datetime.now()
    }]
)
```

### Simple Log Monitoring
```bash
# On DigitalOcean/EC2
tail -f logs/cron.log
tail -f logs/settle_live_data.log
```

---

## Next Steps

1. **Choose your option** based on needs
2. **Follow setup steps** for chosen option
3. **Test manually** before enabling scheduling
4. **Monitor first few runs** closely
5. **Set up alerts** for failures

---

## Troubleshooting

### Common Issues

**Lambda timeout:**
- Increase timeout in function config
- Optimize script (cache models, etc.)

**Missing dependencies:**
- Ensure all deps in `requirements.txt`
- Test locally first

**Timezone issues:**
- Always use UTC in cron/EventBridge
- Convert to EST in scripts if needed

**State persistence:**
- Use S3/cloud storage, not local files
- Initialize from last known state

---

## Questions?

See the main documentation or check:
- `Documentation/PAPER_TRADING_PROTOCOL.md` - Forward test protocol
- `Documentation/LIVE_VALIDATION_PROTOCOL.md` - Validation guide
