@echo off
echo 🌐 SMARTPARK — AI-Powered IoT Smart Parking System
echo ================================================
echo Entry/Exit Detection with 3-Slot Management
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: Python is not installed
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: Node.js is not installed
    echo Please install Node.js 16+ from https://nodejs.org
    pause
    exit /b 1
)

echo ✅ Prerequisites check passed
echo.

REM Initialize database if needed
echo 🗄️ Initializing database...
cd backend
python -c "from database_entry_exit import init_db; init_db()" 2>nul
cd ..

REM Start backend server
echo.
echo ⚡ Starting FastAPI Backend (Entry/Exit System)...
cd backend
start "SmartPark Backend" cmd /k "python main_entry_exit.py"
cd ..

REM Wait for backend to start
echo ⏳ Waiting for backend to initialize...
timeout /t 5 /nobreak >nul

REM Start serial bridge
echo.
echo 🖥️ Starting Serial Bridge (Arduino Communication)...
cd serial_bridge
start "SmartPark Serial Bridge" cmd /k "python event_bridge.py"
cd ..

REM Start frontend
echo.
echo 🌐 Starting React Frontend...
start "SmartPark Frontend" cmd /k "npm run dev"

echo.
echo ✅ SmartPark System Started Successfully!
echo.
echo 📋 System Components:
echo   • Backend API: http://localhost:8000
echo   • API Documentation: http://localhost:8000/docs
echo   • Frontend Dashboard: http://localhost:5173
echo   • WebSocket: ws://localhost:8000/ws/realtime
echo.
echo 🔧 Hardware Setup Required:
echo   1. Connect Arduino UNO via USB
echo   2. Upload arduino/smartpark_entry_exit.ino
echo   3. Connect IR sensors:
echo      - IR_ENTRY → Arduino Pin 2
echo      - IR_EXIT → Arduino Pin 3
echo   4. Connect servo motor → Arduino Pin 9
echo   5. Ensure common ground connections
echo.
echo 🎯 System Features:
echo   • Entry/Exit detection with 2 IR sensors
echo   • Automatic slot assignment (3 logical slots)
echo   • Real-time WebSocket updates
echo   • AI-powered occupancy predictions
echo   • Servo gate control
echo   • Reservation management
echo.
echo 🧪 Testing:
echo   • Check Arduino Serial Monitor (9600 baud)
echo   • Trigger IR sensors to test detection
echo   • Visit http://localhost:8000/api/health
echo   • Open frontend at http://localhost:5173
echo   • Watch real-time slot updates
echo.
echo Press any key to open system URLs...
pause >nul

start http://localhost:8000/docs
timeout /t 2 /nobreak >nul
start http://localhost:5173

echo.
echo 🎉 SmartPark IoT System is running!
echo.
echo 💡 Tips:
echo   • Monitor Arduino Serial output for events
echo   • Check WebSocket connection in browser console
echo   • Train AI model after collecting data
echo   • Use /api/ai/insights for smart recommendations
echo.
echo Press any key to exit...
pause >nul
