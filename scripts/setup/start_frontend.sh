#!/bin/bash

# EPL Predictor Frontend Startup Script
# ======================================

echo "======================================"
echo "EPL Predictor Frontend (React)"
echo "======================================"
echo ""

# Change to frontend directory
cd "$(dirname "$0")/frontend/epl-predictor"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
    echo "✓ Dependencies installed"
else
    echo "✓ Dependencies already installed"
fi

echo ""
echo "======================================"
echo "Starting React Development Server..."
echo "======================================"
echo ""
echo "Frontend will start on: http://localhost:3000"
echo "Make sure backend is running on: http://localhost:5001"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start React development server
npm start
