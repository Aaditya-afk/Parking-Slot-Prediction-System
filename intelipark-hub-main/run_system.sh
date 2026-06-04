#!/bin/bash

echo "🚀 Starting SmartPark IoT System"
echo "================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3.8+ from your package manager"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is not installed"
    echo "Please install Node.js 16+ from your package manager"
    exit 1
fi

echo "✅ Prerequisites check passed"

# Function to start component in new terminal
start_component() {
    local name=$1
    local command=$2
    local dir=$3
    
    echo "🔧 Starting $name..."
    
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal --title="SmartPark $name" --working-directory="$PWD/$dir" -- bash -c "$command; exec bash"
    elif command -v xterm &> /dev/null; then
        xterm -title "SmartPark $name" -e "cd $PWD/$dir && $command; bash" &
    elif command -v konsole &> /dev/null; then
        konsole --title "SmartPark $name" --workdir "$PWD/$dir" -e bash -c "$command; exec bash" &
    else
        echo "⚠️  No terminal emulator found. Running $name in background..."
        cd "$dir" && $command &
        cd ..
    fi
}

# Start backend server
start_component "Backend" "python3 main.py" "backend"

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
sleep 5

# Start serial bridge
start_component "Serial Bridge" "python3 bridge.py" "serial_bridge"

# Start frontend
start_component "Frontend" "npm run dev" "."

echo ""
echo "✅ SmartPark System Started!"
echo ""
echo "📋 System Components:"
echo "  • Backend API: http://localhost:8000"
echo "  • API Docs: http://localhost:8000/docs"
echo "  • Frontend: http://localhost:5173"
echo "  • WebSocket: ws://localhost:8000/ws/realtime"
echo ""
echo "🔧 Hardware Setup:"
echo "  1. Connect Arduino UNO via USB"
echo "  2. Upload arduino/smartpark_3slots.ino"
echo "  3. Connect IR sensors to pins 2, 3, 4"
echo "  4. Connect servo motor to pin 9"
echo ""
echo "🧪 Testing:"
echo "  • Check Arduino Serial Monitor (9600 baud)"
echo "  • Visit http://localhost:8000/api/health"
echo "  • Open frontend at http://localhost:5173"
echo ""

# Try to open URLs in default browser
if command -v xdg-open &> /dev/null; then
    echo "🌐 Opening system URLs..."
    xdg-open http://localhost:8000/docs &
    sleep 2
    xdg-open http://localhost:5173 &
elif command -v open &> /dev/null; then
    echo "🌐 Opening system URLs..."
    open http://localhost:8000/docs &
    sleep 2
    open http://localhost:5173 &
fi

echo ""
echo "🎉 SmartPark IoT System is running!"
echo "Press Ctrl+C to stop all components"

# Keep script running
trap 'echo ""; echo "🛑 Stopping SmartPark System..."; kill $(jobs -p) 2>/dev/null; exit' INT
while true; do
    sleep 1
done
