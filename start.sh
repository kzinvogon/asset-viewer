#!/bin/bash
# Start Asset Viewer Application

cd "$(dirname "$0")"

echo "Starting Asset Viewer..."
echo "Opening browser at http://127.0.0.1:5001"
echo ""

# Kill any existing instance
pkill -f "asset_viewer/venv/bin/python app.py" 2>/dev/null

# Start server
./venv/bin/python app.py &

# Wait for server to start
sleep 2

# Open browser
open http://127.0.0.1:5001

echo "Server running. Press Ctrl+C to stop."
wait
