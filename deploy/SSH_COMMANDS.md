# SSH Connection Commands for Windows

## For Git Bash (Recommended)

Use forward slashes or `~` shorthand:

```bash
# Option 1: Using forward slashes
ssh -i C:/Users/joeba/.ssh/weather_bot_key root@YOUR_DROPLET_IP

# Option 2: Using ~ shorthand (if in home directory)
ssh -i ~/.ssh/weather_bot_key root@YOUR_DROPLET_IP

# Option 3: Using $HOME variable
ssh -i $HOME/.ssh/weather_bot_key root@YOUR_DROPLET_IP
```

## For PowerShell

```powershell
# Option 1: Using forward slashes (works in PowerShell too!)
ssh -i C:/Users/joeba/.ssh/weather_bot_key root@YOUR_DROPLET_IP

# Option 2: Using escaped backslashes
ssh -i "C:\Users\joeba\.ssh\weather_bot_key" root@YOUR_DROPLET_IP

# Option 3: Using $env:USERPROFILE
ssh -i "$env:USERPROFILE\.ssh\weather_bot_key" root@YOUR_DROPLET_IP
```

## Quick Reference

Replace `YOUR_DROPLET_IP` with your actual droplet IP address.

**Git Bash:**
```bash
ssh -i ~/.ssh/weather_bot_key root@YOUR_DROPLET_IP
```

**PowerShell:**
```powershell
ssh -i C:/Users/joeba/.ssh/weather_bot_key root@YOUR_DROPLET_IP
```

## First Time Connection

On first connection, you'll see:
```
The authenticity of host 'xxx.xxx.xxx.xxx' can't be established.
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

Type `yes` and press Enter.

## Troubleshooting

If you get "Permission denied", check:
1. Key file permissions (should be readable only by you)
2. Key was added to DigitalOcean correctly
3. Using the correct IP address
