@echo off
REM Windows batch script to help generate SSH key for DigitalOcean
REM This opens Git Bash with the ssh-keygen command

echo.
echo ==============================================================================
echo SSH Key Generation for DigitalOcean
echo ==============================================================================
echo.
echo Git for Windows is installed.
echo.
echo To generate your SSH key, open Git Bash and run:
echo.
echo   ssh-keygen -t ed25519 -C "weather-bot-droplet" -f ~/.ssh/weather_bot_key
echo.
echo Then display your public key with:
echo.
echo   cat ~/.ssh/weather_bot_key.pub
echo.
echo ==============================================================================
echo.
echo Opening Git Bash for you...
echo (Copy the commands above and paste them in Git Bash)
echo.
pause

REM Try to open Git Bash
where git >nul 2>&1
if %errorlevel% equ 0 (
    echo Starting Git Bash...
    start "" "%ProgramFiles%\Git\git-bash.exe"
) else (
    echo Git Bash not found in default location.
    echo Please open Git Bash manually from Start Menu.
)
