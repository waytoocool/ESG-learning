#!/bin/bash
# Kill existing Chrome processes
pkill -f chrome
sleep 2

# Start Flask application in background
cd "/Users/prateekgoyal/Desktop/Prateek/ESG DataVault Development/Claude/sakshi-learning"
python3 run.py &

echo "Flask application starting..."
sleep 5
echo "Ready for testing"