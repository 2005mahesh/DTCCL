@echo off
set "ROOT=%~dp0"
start "SafeAI Backend" /D "%ROOT%" cmd /k "python -m uvicorn backend.main:app --reload --port 8000"
timeout /t 2 /nobreak >nul
start "SafeAI Frontend" /D "%ROOT%frontend" cmd /k "python -m http.server 5500"
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:5500/login.html"
