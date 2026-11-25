@echo off
title Cloudflare Tunnel - Aadhya WhatsApp Bulker
echo ============================================================
echo   Aadhya WhatsApp Bulker - Cloudflare Public Tunnel
echo ============================================================
echo.
echo Connecting your local WhatsApp server to Cloudflare...
echo Once connected, look for the 'https://*.trycloudflare.com' URL below.
echo You can open that link on ANY device anywhere in the world!
echo.
cloudflared.exe tunnel --url http://127.0.0.1:5000
pause
