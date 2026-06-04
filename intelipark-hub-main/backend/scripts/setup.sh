#!/bin/bash

echo "Setting up SmartPark Backend..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.10+ from your package manager"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Copy environment file
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "Please edit .env file with your settings"
fi

# Initialize database
echo "Initializing database..."
python -c "from database import init_db; init_db()"

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Arduino device path (e.g., /dev/ttyUSB0)"
echo "2. Upload arduino_sketch/smartpark_arduino.ino to your Arduino"
echo "3. Run: python run.py"
echo ""
