@echo off
title WhatsApp Automation Suite (Web App)
echo ========================================================
echo   Launching WhatsApp Automation Web Suite
echo   3-Window Web Dashboard on http://127.0.0.1:5000
echo ========================================================
cd /d "%~dp0"

REM Open in Edge app mode after 2 seconds
start /b cmd /c "timeout /t 2 /nobreak >nul && start msedge --app=http://127.0.0.1:5000"

python app_web.py
pause
