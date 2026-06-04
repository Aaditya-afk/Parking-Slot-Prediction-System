@echo off
echo 🚀 Starting SmartPark IoT System
echo ================================

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

REM Start backend server
echo.
echo 🔧 Starting Backend Server...
cd backend
start "SmartPark Backend" cmd /k "python main.py"
cd ..

REM Wait for backend to start
echo ⏳ Waiting for backend to initialize...
timeout /t 5 /nobreak >nul

REM Start serial bridge
echo.
echo 🖥️ Starting Serial Bridge...
cd serial_bridge
start "SmartPark Serial Bridge" cmd /k "python bridge.py"
cd ..

REM Start frontend
echo.
echo 🌐 Starting Frontend...
start "SmartPark Frontend" cmd /k "npm run dev"

echo.
echo ✅ SmartPark System Started!
echo.
echo 📋 System Components:
echo   • Backend API: http://localhost:8000
echo   • API Docs: http://localhost:8000/docs
echo   • Frontend: http://localhost:5173
echo   • WebSocket: ws://localhost:8000/ws/realtime
echo.
echo 🔧 Hardware Setup:
echo   1. Connect Arduino UNO via USB
echo   2. Upload arduino/smartpark_3slots.ino
echo   3. Connect IR sensors to pins 2, 3, 4
echo   4. Connect servo motor to pin 9
echo.
echo 🧪 Testing:
echo   • Check Arduino Serial Monitor (9600 baud)
echo   • Visit http://localhost:8000/api/health
echo   • Open frontend at http://localhost:5173
echo.
echo Press any key to open system URLs...
pause >nul

start http://localhost:8000/docs
start http://localhost:5173

echo.
echo 🎉 SmartPark IoT System is running!
echo Press any key to exit...
pause >nul
