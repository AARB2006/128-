@echo off
title YT-MP3
rem Runs scripts\windows\start.ps1. Keep this window open while using YT-MP3.
if not exist "%~dp0scripts\windows\start.ps1" (
  echo Extract the whole YT-MP3 ZIP to a folder first, then run this file from there.
  pause
  exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\windows\start.ps1"
if errorlevel 1 pause
