@echo off

title AirSwitch Final Demo

cd /d "%~dp0"

echo ==========================================
echo       AirSwitch Final Demo
echo ==========================================
echo.

call venv\Scripts\activate.bat

start "AirSwitch - ESP32 Simulator" cmd /k "python esp32_simulator.py"

timeout /t 2 /nobreak >nul

start "AirSwitch - Dashboard" cmd /k "python server.py"

timeout /t 3 /nobreak >nul

start "AirSwitch - Hand Gestures" cmd /k "python gesture_detector.py"

echo.
echo Dashboard:
echo http://127.0.0.1:5000
echo.
echo Close the three opened windows to stop the demo.

pause