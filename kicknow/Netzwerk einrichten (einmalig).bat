@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0server\setup-network.ps1" %*
