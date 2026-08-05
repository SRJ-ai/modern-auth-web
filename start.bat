@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Aegis - local server

echo ============================================
echo   Aegis  -  starting up
echo ============================================

REM --- find Python 3 ---
set "PY="
py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY ( python --version >nul 2>&1 && set "PY=python" )
if not defined PY (
  echo [X] Python 3.10+ not found. Install from https://www.python.org/downloads/
  echo     ^(tick "Add python.exe to PATH" during install^), then run this again.
  pause & exit /b 1
)

REM --- create venv on first run ---
if not exist ".venv\Scripts\python.exe" (
  echo [*] Creating virtual environment...
  %PY% -m venv .venv || ( echo [X] venv creation failed & pause & exit /b 1 )
)
set "VPY=.venv\Scripts\python.exe"

REM --- install deps once (downloads bundled Postgres binaries) ---
if not exist ".venv\.installed" (
  echo [*] Installing dependencies ^(first run only, may take a few minutes^)...
  "%VPY%" -m pip install --upgrade pip
  "%VPY%" -m pip install -r requirements.txt || ( echo [X] pip install failed & pause & exit /b 1 )
  echo installed> ".venv\.installed"
)

REM --- ensure env file exists ---
if not exist ".env.local" (
  copy /y ".env.example" ".env.local" >nul
  echo [!] Created .env.local - add GMAIL_USER and GMAIL_APP_PASSWORD to send real emails.
  echo     (The app still runs and saves signups without them.)
)

echo [*] Booting local Postgres + web server...
echo [*] Open:  http://127.0.0.1:8000
start "" http://127.0.0.1:8000
"%VPY%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000

endlocal
