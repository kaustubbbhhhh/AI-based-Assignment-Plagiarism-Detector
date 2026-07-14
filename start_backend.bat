@echo off
echo Starting PlagiarismAI Backend...
cd backend
python -m uvicorn main:app --host 0.0.0.0 --reload --port 8000
pause
