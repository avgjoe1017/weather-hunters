# Deployment Scripts

This directory contains deployment scripts and guides for various cloud platforms.

## Available Deployments

### DigitalOcean Droplet
- **Setup Script**: `digitalocean_setup.sh`
- **Setup Guide**: `DIGITALOCEAN_SETUP.md`
- **Cost**: $6/month
- **Best For**: Forward test or full trading bot

### AWS Lambda
- **Guide**: See `Documentation/CLOUD_DEPLOYMENT.md`
- **Cost**: Free tier, then ~$1/month
- **Best For**: Scheduled forward test only

### GitHub Actions
- **Guide**: See `Documentation/CLOUD_DEPLOYMENT.md`
- **Cost**: Free
- **Best For**: Scheduled tasks, no infrastructure

## Quick Start (DigitalOcean)

1. **Create droplet** on DigitalOcean (Ubuntu 22.04, $6/month)
2. **SSH into droplet**: `ssh root@YOUR_DROPLET_IP`
3. **Run setup script**:
   ```bash
   curl -o /tmp/setup.sh https://raw.githubusercontent.com/YOUR_USERNAME/weather-hunters/main/deploy/digitalocean_setup.sh
   chmod +x /tmp/setup.sh
   /tmp/setup.sh https://github.com/YOUR_USERNAME/weather-hunters.git
   ```
4. **Follow prompts** to configure `.env` file
5. **Test manually** before enabling scheduling

See `DIGITALOCEAN_SETUP.md` for detailed instructions.

## Files in This Directory

- `digitalocean_setup.sh` - Automated setup script for DigitalOcean
- `DIGITALOCEAN_SETUP.md` - Complete DigitalOcean setup guide
- `README.md` - This file

## Notes

- All scripts assume Ubuntu 22.04 LTS
- Run setup scripts as `root` user
- Test manually before enabling cron scheduling
- Keep credentials secure (use `.env` file, never commit)
