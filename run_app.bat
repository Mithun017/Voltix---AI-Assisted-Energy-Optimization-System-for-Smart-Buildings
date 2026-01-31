@echo off
echo Starting Voltix AI Energy Optimzation System...

:: Start Backend in background
echo Starting Backend...
start "Voltix Backend" cmd /k "cd AI_Energy_Optimization/backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

:: Start Frontend in background
echo Starting Frontend...
start "Voltix Frontend" cmd /k "cd AI_Energy_Optimization/frontend && npm run dev"

:: Wait for 3 seconds
echo Waiting for services to initialize...
timeout /t 3 /nobreak >nul

:: Open Browser
echo Opening Dashboard...
start http://localhost:5173

echo System is running. Close the terminal windows to stop.
