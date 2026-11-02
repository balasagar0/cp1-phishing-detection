@echo off
cd /d "%~dp0"
echo Installing dependencies (first run only)
python -m pip install -r requirements.txt
echo.
echo Starting API on http://127.0.0.1:8000
echo Press Ctrl+C to stop.
python -m uvicorn api:app --port 8000 --no-access-log
pause
