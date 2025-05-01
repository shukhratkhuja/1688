#!/bin/bash

# Start virtual display for headless Chrome
Xvfb :99 -screen 0 1280x1024x24 -ac +extension GLX +render -noreset &

# Wait for Xvfb to start
sleep 2

# Create required directories if they don't exist
mkdir -p /app/logs
mkdir -p /app/output/images

# Check if client secrets file exists, if not create a placeholder
if [ ! -f /app/client_secrets.json ]; then
    echo "Warning: client_secrets.json not found. Please mount this file."
    echo "{}" > /app/client_secrets.json
fi

# Check if credentials file exists, if not create a placeholder
if [ ! -f /app/mycreds.txt ]; then
    echo "Warning: mycreds.txt not found. Google Drive uploads will fail."
    echo "" > /app/mycreds.txt
fi

# Run application
python main.py