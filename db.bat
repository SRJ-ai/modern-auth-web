@echo off
REM Aegis DB admin. Examples:
REM   db.bat count
REM   db.bat list
REM   db.bat add "Ada Lovelace" ada@company.com "+1 555 123 4567" "ACME"
REM   db.bat delete ada@company.com
REM   db.bat url
REM   db.bat psql
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo [X] Not set up yet. Run start.bat once first.
  pause & exit /b 1
)
".venv\Scripts\python.exe" -m app.dbcli %*
