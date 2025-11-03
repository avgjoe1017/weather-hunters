# Fix SSH Connection Issue

## Problem: "Permission denied (publickey)"

This means your SSH key isn't recognized by the droplet. Here's how to fix it:

---

## Step 1: Check if Key Was Added to DigitalOcean

1. **Go to DigitalOcean Dashboard**
   - Login: https://cloud.digitalocean.com
   - Settings → Security → SSH Keys

2. **Verify your key is there**
   - Look for `weather-bot-key` or `weather-bot-droplet`
   - If NOT there → Add it (see below)

3. **If key is there:**
   - Make sure it's selected in your droplet settings
   - Go to Droplets → Your droplet → Settings → SSH Keys

---

## Step 2: Regenerate Key Without Passphrase

The passphrase prompt suggests the key was created with a passphrase. Let's create a new one without a passphrase:

### In Git Bash:

```bash
# Remove old key (backup first if you want)
mv ~/.ssh/weather_bot_key ~/.ssh/weather_bot_key.old
mv ~/.ssh/weather_bot_key.pub ~/.ssh/weather_bot_key.pub.old

# Generate new key WITHOUT passphrase
ssh-keygen -t ed25519 -C "weather-bot-droplet" -f ~/.ssh/weather_bot_key -N ""

# Display new public key
cat ~/.ssh/weather_bot_key.pub
```

**The `-N ""` flag sets an empty passphrase (no passphrase required).**

---

## Step 3: Add Public Key to DigitalOcean

1. **Copy your NEW public key** (from `cat ~/.ssh/weather_bot_key.pub`)

2. **Go to DigitalOcean:**
   - Settings → Security → SSH Keys
   - Click "Add SSH Key"
   - Paste the public key
   - Name: `weather-bot-key`
   - Click "Add SSH Key"

---

## Step 4: Add Key to Existing Droplet

If your droplet already exists, you need to add the key:

### Option A: Via DigitalOcean Console

1. **Go to your droplet** in DigitalOcean dashboard
2. **Click "Access" → "Launch Droplet Console"**
3. **In the console, run:**
   ```bash
   mkdir -p ~/.ssh
   nano ~/.ssh/authorized_keys
   ```
4. **Paste your public key** (entire line starting with `ssh-ed25519`)
5. **Save and exit** (Ctrl+X, Y, Enter)
6. **Set permissions:**
   ```bash
   chmod 700 ~/.ssh
   chmod 600 ~/.ssh/authorized_keys
   ```

### Option B: Destroy and Recreate Droplet (Easier)

1. **Destroy current droplet:**
   - Go to droplet → Settings → Destroy
   - (Note: You'll lose any data on it)

2. **Create new droplet:**
   - When creating, select your SSH key
   - This time it should work!

---

## Step 5: Try Connecting Again

```bash
ssh -i ~/.ssh/weather_bot_key root@165.22.172.211
```

**You should connect WITHOUT a passphrase prompt.**

---

## Alternative: Use DigitalOcean Console

If SSH still doesn't work:

1. **Go to your droplet** in dashboard
2. **Click "Access" → "Launch Droplet Console"**
3. **Use the web-based console** to set everything up
4. **You can then add the SSH key manually** (Option A above)

---

## Quick Fix Summary

```bash
# 1. Generate new key without passphrase
ssh-keygen -t ed25519 -C "weather-bot-droplet" -f ~/.ssh/weather_bot_key -N ""

# 2. Display public key
cat ~/.ssh/weather_bot_key.pub

# 3. Copy output and add to DigitalOcean → Settings → Security → SSH Keys

# 4. If droplet already exists, add key manually via console
# OR recreate droplet with key selected

# 5. Try connecting
ssh -i ~/.ssh/weather_bot_key root@165.22.172.211
```

---

## Why This Happens

"Permission denied (publickey)" means:
- ❌ Your public key isn't in `~/.ssh/authorized_keys` on the droplet
- ❌ DigitalOcean didn't add the key automatically
- ❌ The key wasn't selected when creating the droplet

**Solution:** Either add key manually via console, or recreate droplet with key selected.

---

## Next Steps After Fixing

Once you can SSH in:
1. Run the setup script: `./deploy/digitalocean_setup.sh`
2. Configure `.env` file
3. Test scripts manually
4. Monitor first scheduled run
