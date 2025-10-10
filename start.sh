#!/bin/bash

#######################################################
# EPL Match Predictor - Quick Start Script
# Version: 2.0
# Description: Starts both backend and frontend concurrently
#######################################################

GREEN='\033[0;32m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${PURPLE}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║   Starting EPL Match Predictor v2.0                      ║
╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
echo ""

# Check if setup was done
if [ ! -d "backend/venv" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo -e "${YELLOW}⚠️  Please run ./setup.sh first${NC}"
    exit 1
fi

if [ ! -d "frontend/epl-predictor/node_modules" ]; then
    echo -e "${RED}❌ Node modules not found!${NC}"
    echo -e "${YELLOW}⚠️  Please run ./setup.sh first${NC}"
    exit 1
fi

# Trap Ctrl+C to kill both processes
trap 'echo ""; echo -e "${YELLOW}Stopping services...${NC}"; kill $(jobs -p) 2>/dev/null; exit' EXIT INT TERM

# Start backend
echo -e "${BLUE}[Backend]${NC} Starting Flask API on port 5001..."
cd backend
source venv/bin/activate
python api/app.py > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo -e "${BLUE}[Backend]${NC} Waiting for server to start..."
sleep 3

# Check if backend is running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}❌ Backend failed to start!${NC}"
    echo -e "${YELLOW}Check backend.log for details${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"

# Start frontend
echo -e "${GREEN}[Frontend]${NC} Starting React app on port 3000..."
cd frontend/epl-predictor
npm start > ../../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ../..

# Wait a moment for frontend to start
sleep 2

echo ""
echo -e "${GREEN}✅ Both services started successfully!${NC}"
echo ""
echo -e "${PURPLE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${PURPLE}   Access the application:${NC}"
echo -e "${PURPLE}     • Frontend: http://localhost:3000${NC}"
echo -e "${PURPLE}     • Backend:  http://localhost:5001/api${NC}"
echo -e "${PURPLE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}📋 Logs:${NC}"
echo "  • Backend:  tail -f backend.log"
echo "  • Frontend: tail -f frontend.log"
echo ""
echo -e "${YELLOW}⚠️  Press Ctrl+C to stop both services${NC}"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
