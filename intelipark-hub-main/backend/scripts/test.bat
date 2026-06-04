@echo off
echo Running SmartPark Backend Tests...

REM Activate virtual environment
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo Error: Virtual environment not found
    echo Please run setup.bat first
    pause
    exit /b 1
)

REM Check if backend is running
echo Checking if backend is running...
curl -s http://localhost:8000/api/health >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Backend is not running
    echo Please start the backend first with start.bat
    pause
    exit /b 1
)

REM Run tests
echo Running system tests...
python test_system.py

echo.
echo Tests completed!
pause
