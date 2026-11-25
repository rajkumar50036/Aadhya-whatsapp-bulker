@echo off
title WhatsApp Automation Studio (3-Window Desktop App)
echo ========================================================
echo   Launching WhatsApp Automation Studio (Desktop)
echo   Window 1: Phone Number ^& WhatsApp QR Link
echo   Window 2: Message Box
echo   Window 3: Send Files (Photos ^& Videos)
echo ========================================================
cd /d "%~dp0"
python app_gui.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error encountered while running the app.
    pause
)
