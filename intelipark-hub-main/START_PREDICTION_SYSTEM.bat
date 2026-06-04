@echo off
echo ========================================
echo   SmartPark Prediction System Launcher
echo ========================================
echo.

REM Start Backend
echo [1/2] Starting Prediction Backend...
cd backend
start "SmartPark Prediction API" cmd /k "python main_prediction.py"
cd ..

REM Wait for backend
echo.
echo [2/2] Waiting for backend to initialize...
timeout /t 5 /nobreak >nul

REM Start Frontend
echo.
echo Starting Frontend...
start "SmartPark Frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo   System Started Successfully!
echo ========================================
echo.
echo   Backend API: http://localhost:8000
echo   API Docs: http://localhost:8000/docs
echo   Frontend: http://localhost:5173
echo.
echo   Features Available:
echo   - Live countdown timers on occupied slots
echo   - Auto-release when timers expire
echo   - ML predictions for slot availability
echo   - Smart recommendations
echo   - Real-time WebSocket updates
echo   - Analytics dashboard
echo.
echo   Pages:
echo   - Dashboard: http://localhost:5173/
echo   - Predictions: http://localhost:5173/predictions
echo   - Analytics: http://localhost:5173/analytics
echo.
echo ========================================
echo.
pause
