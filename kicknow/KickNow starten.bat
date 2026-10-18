@echo off
title KickNow Server
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0server\server.ps1" %*
pause
