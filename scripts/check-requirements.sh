#!/bin/bash

# 사전 요구사항 확인

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=== Checking Requirements ==="
echo ""

MISSING=0

# Docker
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✅ Docker installed:${NC} $(docker --version)"
else
    echo -e "${RED}❌ Docker not installed${NC}"
    echo -e "${YELLOW}Install: https://www.docker.com/products/docker-desktop${NC}"
    MISSING=1
fi

# Python
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✅ Python installed:${NC} $(python3 --version)"
else
    echo -e "${RED}❌ Python not installed${NC}"
    MISSING=1
fi

# Node.js
if command -v node &> /dev/null; then
    echo -e "${GREEN}✅ Node.js installed:${NC} $(node --version)"
else
    echo -e "${RED}❌ Node.js not installed${NC}"
    MISSING=1
fi

# venv (backend)
if [ -d "backend/venv" ]; then
    echo -e "${GREEN}✅ Backend venv exists${NC}"
else
    echo -e "${YELLOW}⚠️  Backend venv not found${NC}"
    echo -e "${YELLOW}Run: cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt${NC}"
fi

# node_modules (frontend)
if [ -d "frontend/node_modules" ]; then
    echo -e "${GREEN}✅ Frontend dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend dependencies not found${NC}"
    echo -e "${YELLOW}Run: cd frontend && npm install${NC}"
fi

echo ""

if [ $MISSING -eq 1 ]; then
    echo -e "${RED}Missing required software. Install them first.${NC}"
    exit 1
else
    echo -e "${GREEN}All requirements met!${NC}"
    exit 0
fi
