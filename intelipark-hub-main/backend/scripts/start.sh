#!/bin/bash

echo "Starting SmartPark Backend..."

# Activate virtual environment
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
else
    echo "Error: Virtual environment not found"
    echo "Please run setup.sh first"
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    echo "Please copy .env.example to .env and configure it"
    exit 1
fi

# Start the backend
echo "Starting FastAPI server..."
python run.py
