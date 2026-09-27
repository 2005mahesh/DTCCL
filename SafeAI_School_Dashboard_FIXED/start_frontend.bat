@echo off
cd /d "%~dp0frontend"
echo Starting SafeAI School frontend on http://127.0.0.1:5500
python -m http.server 5500
pause
