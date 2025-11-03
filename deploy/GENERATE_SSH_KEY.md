# Generate SSH Key for DigitalOcean

This guide shows how to generate an SSH key pair for secure access to your DigitalOcean droplet.

---

## Windows: Generate SSH Key

### Option 1: Using Git Bash (Recommended)

If you have Git for Windows installed, use Git Bash:

1. **Open Git Bash** (search "Git Bash" in Start menu)

2. **Generate SSH key:**
   ```bash
   ssh-keygen -t ed25519 -C "weather-bot-droplet" -f ~/.ssh/weather_bot_key
   ```

3. **When prompted for passphrase:**
   - Press Enter for no passphrase (easier for automated access)
   - OR enter a passphrase for extra security

4. **Your keys are created:**
   - Private key: `C:\Users\YourUsername\.ssh\weather_bot_key`
   - Public key: `C:\Users\YourUsername\.ssh\weather_bot_key.pub`

5. **Display public key** (copy this to DigitalOcean):
   ```bash
   cat ~/.ssh/weather_bot_key.pub
   ```

---

### Option 2: Install OpenSSH for Windows

If you don't have Git Bash:

1. **Open PowerShell as Administrator**

2. **Install OpenSSH Client:**
   ```powershell
   # Check if OpenSSH is available
   Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH*'

   # Install OpenSSH Client
   Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
   ```

3. **Generate SSH key:**
   ```powershell
   # Create .ssh directory if it doesn't exist
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.ssh"

   # Generate key
   ssh-keygen -t ed25519 -C "weather-bot-droplet" -f "$env:USERPROFILE\.ssh\weather_bot_key"
   ```

4. **Display public key:**
   ```powershell
   Get-Content "$env:USERPROFILE\.ssh\weather_bot_key.pub"
   ```

---

### Option 3: Using Windows Terminal / WSL

If you have Windows Subsystem for Linux (WSL):

1. **Open WSL terminal**

2. **Generate SSH key:**
   ```bash
   ssh-keygen -t ed25519 -C "weather-bot-droplet" -f ~/.ssh/weather_bot_key
   ```

3. **Display public key:**
   ```bash
   cat ~/.ssh/weather_bot_key.pub
   ```

---

## Mac/Linux: Generate SSH Key

1. **Open Terminal**

2. **Generate SSH key:**
   ```bash
   ssh-keygen -t ed25519 -C "weather-bot-droplet" -f ~/.ssh/weather_bot_key
   ```

3. **When prompted:**
   - Enter passphrase (or press Enter for none)
   - Press Enter to accept default location

4. **Display public key:**
   ```bash
   cat ~/.ssh/weather_bot_key.pub
   ```

---

## What You'll Get

After generating, you'll have two files:

1. **Private Key** (`weather_bot_key`):
   - Keep this SECRET and safe
   - Never share this file
   - Used to authenticate to your droplet
   - Location: `~/.ssh/weather_bot_key` (or `C:\Users\YourUsername\.ssh\weather_bot_key` on Windows)

2. **Public Key** (`weather_bot_key.pub`):
   - Safe to share
   - Add this to DigitalOcean
   - Location: `~/.ssh/weather_bot_key.pub` (or `C:\Users\YourUsername\.ssh\weather_bot_key.pub` on Windows)

---

## Add Public Key to DigitalOcean

### Via Web UI

1. **Login to DigitalOcean**: https://cloud.digitalocean.com

2. **Go to Settings → Security → SSH Keys**

3. **Click "Add SSH Key"**

4. **Paste your public key** (contents of `weather_bot_key.pub`)

5. **Name it**: "weather-bot-key" (or any name you prefer)

6. **Click "Add SSH Key"**

### Via API (Advanced)

```bash
# Get your public key content
cat ~/.ssh/weather_bot_key.pub

# Use DigitalOcean API to add key
# (See DigitalOcean API docs for details)
```

---

## Use SSH Key to Connect

After adding the key to DigitalOcean, you can SSH into your droplet:

### Windows (Git Bash or PowerShell)

```bash
# Using the key file
ssh -i ~/.ssh/weather_bot_key root@YOUR_DROPLET_IP

# OR if key is in default location (~/.ssh/id_rsa), just:
ssh root@YOUR_DROPLET_IP
```

### Mac/Linux

```bash
# Using the key file
ssh -i ~/.ssh/weather_bot_key root@YOUR_DROPLET_IP

# OR add to ssh-agent for easier access
ssh-add ~/.ssh/weather_bot_key
ssh root@YOUR_DROPLET_IP
```

---

## Security Best Practices

### 1. Protect Your Private Key

```bash
# Set proper permissions (Mac/Linux)
chmod 600 ~/.ssh/weather_bot_key

# Windows: Right-click file → Properties → Security → Advanced
# Remove all users except yourself, give yourself "Full Control" only
```

### 2. Use a Passphrase (Optional but Recommended)

- When generating key, enter a passphrase
- Key will be encrypted with passphrase
- Required each time you use the key
- More secure but less convenient

### 3. Don't Commit Private Keys

```bash
# Add to .gitignore
echo "*.key" >> .gitignore
echo ".ssh/" >> .gitignore
echo "weather_bot_key" >> .gitignore
```

### 4. Backup Your Private Key

- Store private key securely (encrypted backup)
- Losing private key = can't access droplet (unless you have recovery method)

---

## Troubleshooting

### "Permission denied (publickey)"

**Problem:** SSH can't authenticate with your key

**Solutions:**
1. Check you're using the correct key file:
   ```bash
   ssh -i ~/.ssh/weather_bot_key root@YOUR_DROPLET_IP
   ```

2. Verify key was added to DigitalOcean correctly:
   - Check key fingerprint matches
   - Ensure public key was added correctly (no extra spaces)

3. Check file permissions (Mac/Linux):
   ```bash
   chmod 600 ~/.ssh/weather_bot_key
   chmod 644 ~/.ssh/weather_bot_key.pub
   ```

### "Could not resolve hostname"

**Problem:** Can't connect to droplet

**Solutions:**
1. Check droplet IP address is correct
2. Check droplet is running (in DigitalOcean dashboard)
3. Check firewall isn't blocking SSH (port 22)

### "WARNING: UNPROTECTED PRIVATE KEY FILE!"

**Problem:** Key file permissions are too open

**Solutions (Mac/Linux):**
```bash
chmod 600 ~/.ssh/weather_bot_key
```

**Solutions (Windows):**
- Right-click file → Properties → Security
- Remove all users except yourself
- Give yourself "Full Control" only

---

## Quick Reference

```bash
# Generate key
ssh-keygen -t ed25519 -C "weather-bot-droplet" -f ~/.ssh/weather_bot_key

# Display public key (copy this to DigitalOcean)
cat ~/.ssh/weather_bot_key.pub

# Connect to droplet
ssh -i ~/.ssh/weather_bot_key root@YOUR_DROPLET_IP

# Test connection
ssh -i ~/.ssh/weather_bot_key root@YOUR_DROPLET_IP "echo 'Connection successful!'"
```

---

## Next Steps

1. ✅ **Generate SSH key** (you're here)
2. ⏭️ **Add public key to DigitalOcean** (Settings → Security → SSH Keys)
3. ⏭️ **Create droplet** with your SSH key
4. ⏭️ **SSH into droplet** using your private key
5. ⏭️ **Run setup script** from `deploy/DIGITALOCEAN_SETUP.md`

---

**Last Updated**: 2025-11-03
