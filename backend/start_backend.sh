#!/bin/bash

# AI Chip Trading Signal System - Backend Startup Script

echo "🚀 Starting AI Chip Trading Signal System Backend..."

# Create data and logs directories
mkdir -p data logs

# Set environment variables (update these with your actual keys)
export FRED_API_KEY=${FRED_API_KEY:-"demo_key"}
export DATABASE_PATH="data/trading_signals.db"
export DATA_UPDATE_INTERVAL=300

# Install dependencies if needed
if [ ! -d "venv" ]; then
	echo "📦 Creating virtual environment..."
	python3 -m venv venv
fi

echo "📦 Activating virtual environment..."
source venv/bin/activate

echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run tests first
echo "🧪 Running backend tests..."
python test_backend.py

echo ""
echo "🎯 Starting FastAPI server..."
echo "Dashboard will be available at: http://localhost:8000"
echo "API docs available at: http://localhost:8000/docs"
echo ""

# Start the FastAPI server
cd src && python main.py
