#!/bin/bash
# OmniCore-AI Recovery Script
# This script is called by the Sentinel to restart the backend engine.

echo "[$(date)] Sentinel triggered restart sequence..."

# 1. Find and kill existing uvicorn/python processes running the app
# We look for the main entry point to avoid killing the sentinel itself
PIDS=$(pgrep -f "uvicorn src.api.main:app")

if [ -n "$PIDS" ]; then
    echo "Stopping existing engine processes: $PIDS"
    kill -9 $PIDS
else
    echo "No running engine processes found."
fi

# 2. Start the engine in the background
# Using nohup to ensure it persists after the script exits
echo "Starting OmniCore-AI Engine..."
nohup python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 > logs/engine.log 2>&1 &

echo "Engine started in background. Monitoring logs at logs/engine.log"
echo "[$(date)] Recovery sequence completed."
