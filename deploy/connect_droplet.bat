@echo off
REM Quick SSH connection script for your DigitalOcean droplet
REM IP: 165.22.172.211

echo.
echo ==============================================================================
echo Connecting to DigitalOcean Droplet
echo ==============================================================================
echo.
echo Droplet IP: 165.22.172.211
echo Droplet Name: ubuntu-s-1vcpu-1gb-sfo2-01
echo.
echo Opening Git Bash with SSH command...
echo.
pause

REM Open Git Bash with SSH command
start "" "%ProgramFiles%\Git\git-bash.exe" -c "ssh -i ~/.ssh/weather_bot_key root@165.22.172.211"
