#!/bin/bash

# Desktop App Launcher Script
# This script sets up and runs the 1688 Desktop Scraper Application

echo "🚀 Starting 1688 Desktop Scraper Application..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Install desktop requirements if not already installed
echo "📥 Installing desktop app requirements..."
pip install --upgrade pip
pip install -r requirements_desktop.txt

# Install main project requirements
echo "📥 Installing main project requirements..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "✏️  Please edit .env file with your API keys before running the app."
    exit 1
fi

# Check if database exists, if not create it
if [ ! -f "product_data.db" ]; then
    echo "🗄️  Database not found. Creating initial database..."
    python utils/prepare_db.py
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs
mkdir -p output/images

# Run the desktop application
echo "🖥️  Launching Desktop Application..."
python app.py

echo "👋 Desktop application closed."