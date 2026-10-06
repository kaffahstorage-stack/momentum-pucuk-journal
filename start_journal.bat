@echo off
cd /d "%~dp0"
py -3 -m pip install -r requirements.txt
if errorlevel 1 goto fail
py -3 mt5_bridge.py
:fail
pause
