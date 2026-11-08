@echo off
cd /d "%~dp0"
py -3 -m pip install -r requirements.txt >nul 2>&1
py -3 main.py
pause
