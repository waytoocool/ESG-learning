#!/bin/bash
echo "Killing Chrome processes..."
pkill -f chrome
sleep 2

echo "Killing Python/Flask processes..."
pkill -f "python3 run.py"
sleep 2

echo "All processes terminated"