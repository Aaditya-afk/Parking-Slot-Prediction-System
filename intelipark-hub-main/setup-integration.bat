@echo off
echo 🚀 SmartPark Frontend-Backend Integration Setup
echo ================================================

REM Check if we're in the right directory
if not exist "package.json" (
    echo ❌ Error: Please run this script from the frontend root directory
    echo Expected to find package.json in current directory
    pause
    exit /b 1
)

echo 📁 Setting up environment configuration...

REM Create .env file if it doesn't exist
if not exist ".env" (
    if exist ".env.example" (
        copy .env.example .env
        echo ✅ Created .env file from .env.example
    ) else (
        echo # SmartPark Frontend Environment > .env
        echo VITE_API_URL=http://localhost:8000 >> .env
        echo VITE_WS_URL=ws://localhost:8000/ws/slots >> .env
        echo VITE_MOCK_DATA=false >> .env
        echo VITE_ENABLE_REALTIME=true >> .env
        echo ✅ Created .env file with default settings
    )
) else (
    echo ⚠️  .env file already exists, skipping creation
)

echo.
echo 🔧 Installing additional dependencies...

REM Check if npm is available
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: npm is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)

REM Install dependencies (they should already be in package.json)
echo Installing existing dependencies...
npm install

echo.
echo 🔍 Checking backend availability...

REM Check if backend is running
curl -s http://localhost:8000/api/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Backend is running and accessible
) else (
    echo ⚠️  Backend is not running
    echo Please start the backend first:
    echo   cd backend
    echo   python run.py
)

echo.
echo 📋 Integration Setup Complete!
echo.
echo 🎯 Next Steps:
echo 1. Start the backend: cd backend && python run.py
echo 2. Start the frontend: npm run dev
echo 3. Open http://localhost:5173 in your browser
echo 4. Check real-time connection indicator in the UI
echo.
echo 📚 Documentation:
echo - Integration Guide: INTEGRATION_GUIDE.md
echo - Backend API: backend/API_DOCUMENTATION.md
echo - Quick Start: backend/QUICK_START.md
echo.
echo 🔧 Troubleshooting:
echo - Check .env file for correct API URL
echo - Ensure backend is running on port 8000
echo - Check browser console for any errors
echo.
pause
