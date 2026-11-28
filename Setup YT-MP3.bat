@echo off
title YT-MP3 Setup
rem Runs scripts\windows\setup.ps1. Double-click this file once on each computer.
if not exist "%~dp0scripts\windows\setup.ps1" (
  echo Extract the whole YT-MP3 ZIP to a folder first, then run this file from there.
  pause
  exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\windows\setup.ps1"
echo.
pause
