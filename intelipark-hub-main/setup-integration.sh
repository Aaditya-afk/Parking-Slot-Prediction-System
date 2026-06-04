#!/bin/bash

echo "🚀 SmartPark Frontend-Backend Integration Setup"
echo "================================================"

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Please run this script from the frontend root directory"
    echo "Expected to find package.json in current directory"
    exit 1
fi

echo "📁 Setting up environment configuration..."

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env file from .env.example"
    else
        cat > .env << EOF
# SmartPark Frontend Environment
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws/slots
VITE_MOCK_DATA=false
VITE_ENABLE_REALTIME=true
EOF
        echo "✅ Created .env file with default settings"
    fi
else
    echo "⚠️  .env file already exists, skipping creation"
fi

echo ""
echo "🔧 Installing additional dependencies..."

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ Error: npm is not installed or not in PATH"
    echo "Please install Node.js from https://nodejs.org"
    exit 1
fi

# Install dependencies (they should already be in package.json)
echo "Installing existing dependencies..."
npm install

echo ""
echo "🔍 Checking backend availability..."

# Check if backend is running
if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "✅ Backend is running and accessible"
else
    echo "⚠️  Backend is not running"
    echo "Please start the backend first:"
    echo "  cd backend"
    echo "  python run.py"
fi

echo ""
echo "📋 Integration Setup Complete!"
echo ""
echo "🎯 Next Steps:"
echo "1. Start the backend: cd backend && python run.py"
echo "2. Start the frontend: npm run dev"
echo "3. Open http://localhost:5173 in your browser"
echo "4. Check real-time connection indicator in the UI"
echo ""
echo "📚 Documentation:"
echo "- Integration Guide: INTEGRATION_GUIDE.md"
echo "- Backend API: backend/API_DOCUMENTATION.md"
echo "- Quick Start: backend/QUICK_START.md"
echo ""
echo "🔧 Troubleshooting:"
echo "- Check .env file for correct API URL"
echo "- Ensure backend is running on port 8000"
echo "- Check browser console for any errors"
echo ""
