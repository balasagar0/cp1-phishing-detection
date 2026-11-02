@echo off
cd /d "%~dp0"
set PY=python
if exist ".venv\Scripts\python.exe" set PY=.venv\Scripts\python.exe
echo Unit and API tests (window, identity tokens, demo cases TC-01 to TC-08, defects, refit path)
%PY% -m pytest tests -q -p no:cacheprovider --ignore=tests/test_final_cases.py
echo.
echo The 112 ported test-plan cases (writes reports\final_cases_results.json)
%PY% tests\test_final_cases.py
echo.
echo Workbook and validator checks (the second half needs data\processed\pool_*.csv from run_all.sh)
%PY% tests\smoke_test.py
echo.
pause
