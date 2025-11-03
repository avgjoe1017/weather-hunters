# Add SSH Key via DigitalOcean Console

## Quick Steps

1. **Click "Launch Droplet Console"** (the blue button on the Access tab)

2. **When the console opens**, you'll see a terminal. Run these commands:

```bash
# Create .ssh directory if it doesn't exist
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Add your public key to authorized_keys
echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPFxzSoB1ppZumMTUwidUvCswr33FfhiDDW+/tvClk4l weather-bot-droplet-nopass" >> ~/.ssh/authorized_keys

# Set correct permissions (CRITICAL!)
chmod 600 ~/.ssh/authorized_keys

# Verify it was added
cat ~/.ssh/authorized_keys
```

3. **Close the console** and try SSH again from your local machine:

```bash
ssh -i ~/.ssh/weather_bot_key_new root@165.22.172.211
```

**It should connect without asking for a passphrase!**

---

## Full Commands to Copy-Paste

Copy this entire block into the Droplet Console:

```bash
mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPFxzSoB1ppZumMTUwidUvCswr33FfhiDDW+/tvClk4l weather-bot-droplet-nopass" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && cat ~/.ssh/authorized_keys
```

---

## After Adding Key

Once you can SSH in normally, you can run the setup script:

```bash
# Clone repo (if you haven't already)
git clone https://github.com/YOUR_USERNAME/weather-hunters.git /opt/weather-hunters

# OR if repo is private, upload files via SCP first

# Run setup
cd /opt/weather-hunters
chmod +x deploy/digitalocean_setup.sh
./deploy/digitalocean_setup.sh
```

---

## Troubleshooting

**If "mkdir" or "echo" commands don't work:**
- Make sure you're logged in as `root`
- The console should show `root@ubuntu-s-1vcpu-1gb-sfo2-01:~#`

**If permissions error:**
- Run: `chmod 600 ~/.ssh/authorized_keys` again
- Verify with: `ls -la ~/.ssh/`

**After adding key, SSH still doesn't work:**
- Check the key was added correctly: `cat ~/.ssh/authorized_keys`
- Make sure the entire key line is there (starting with `ssh-ed25519`)
- No extra spaces or line breaks

---

**Ready?** Click "Launch Droplet Console" and run the commands above!
