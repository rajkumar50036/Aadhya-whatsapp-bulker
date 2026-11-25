@echo off
title Stop Aadhya WhatsApp Bulker Background Service
echo Stopping Aadhya WhatsApp Bulker background processes...
taskkill /F /IM ngrok.exe >nul 2>&1
echo Background services stopped successfully.
pause
