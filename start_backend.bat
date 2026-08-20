@echo off
echo Starting PlagiarismAI Backend...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do taskkill /F /PID %%a >nul 2>&1
cd backend
python -m uvicorn main:app --host 0.0.0.0 --reload --port 8000
pause

