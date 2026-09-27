@echo off
cd /d "%~dp0"
echo Starting SafeAI School API on http://127.0.0.1:8000
python -m uvicorn backend.main:app --reload --port 8000
pause
