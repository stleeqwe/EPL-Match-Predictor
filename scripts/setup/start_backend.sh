#!/bin/bash

# EPL Predictor Backend Startup Script
# =====================================

echo "======================================"
echo "EPL Predictor Backend Server"
echo "======================================"
echo ""

# Change to backend directory
cd "$(dirname "$0")/backend"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt

echo ""
echo "======================================"
echo "Checking trained models..."
echo "======================================"

# Check if models exist
if [ -f "model_cache/bayesian_model_real.pkl" ] && [ -f "model_cache/dixon_coles_real.pkl" ]; then
    echo "✓ Trained models found:"
    echo "  - bayesian_model_real.pkl"
    echo "  - dixon_coles_real.pkl"
else
    echo "⚠ Trained models not found!"
    echo "Please run: python3 scripts/train_fast.py"
fi

echo ""
echo "======================================"
echo "Starting Flask API Server..."
echo "======================================"
echo ""
echo "Server will start on: http://localhost:5001"
echo "API endpoints available at: http://localhost:5001/api"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Set Flask environment variables
export FLASK_APP=api/app.py
export FLASK_ENV=development

# Start Flask server
python3 -m flask run --host=0.0.0.0 --port=5001
