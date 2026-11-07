@echo off
rem One double-click demo start (R3-06): preflight checks, then the API with the console, then the browser.
rem Needs the project venv (see README, Install). Nothing here uses the internet.
cd /d "%~dp0"
set PY=.venv\Scripts\python.exe
if not exist "%PY%" (
  echo The project venv is missing. Follow README.md, section Install, once ^(it needs the internet^).
  pause
  exit /b 1
)
echo Running preflight and starting the API on http://127.0.0.1:8000 ...
"%PY%" scripts\preflight.py --port 8000 --keep-running --open
if errorlevel 1 (
  echo.
  echo NO-GO. See the lines marked NO above and docs\DEMO_SCRIPT.md, section Fallbacks.
  echo If port 8000 is taken: "%PY%" scripts\preflight.py --port 8001 --keep-running --open  and use http://127.0.0.1:8001/
)
pause
