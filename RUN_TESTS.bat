@echo off
cd /d "%~dp0"
echo Window, identity token and input check tests
python tests\test_window_and_ids.py
echo.
echo Workbook and validator checks
python tests\smoke_test.py
echo.
echo Note: smoke_test stops at the synthetic row generator, which needs
echo data\processed\pool_*.csv from run_all.sh. Not needed for the demo.
echo.
pause
