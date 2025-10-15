#!/bin/bash

# 통합 테스트 스크립트
# v2.0 Odds-Based Value Betting System

echo "============================================================"
echo "🧪 Integration Test - Odds-Based Value Betting System"
echo "============================================================"

# 색상 코드
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 카운터
PASSED=0
FAILED=0

# 테스트 함수
test_module() {
    local module=$1
    local description=$2
    
    echo -e "\n${YELLOW}Testing:${NC} $description"
    
    if python -m $module > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC} - $module"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAIL${NC} - $module"
        ((FAILED++))
    fi
}

# 디렉토리 확인
cd /Users/pukaworks/Desktop/soccer-predictor/backend

# 가상환경 활성화
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo -e "${RED}Error: Virtual environment not found${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Phase 1: Module Tests${NC}"
echo "------------------------------------------------------------"

# 1. Odds Collection
test_module "odds_collection.odds_api_client" "Odds API Client"
test_module "odds_collection.odds_aggregator" "Odds Aggregator"

# 2. Value Betting
test_module "value_betting.value_detector" "Value Detector"
test_module "value_betting.arbitrage_finder" "Arbitrage Finder"
test_module "value_betting.kelly_calculator" "Kelly Calculator"

echo -e "\n${YELLOW}Phase 2: Unit Tests (pytest)${NC}"
echo "------------------------------------------------------------"

if pytest tests/ -v --tb=short; then
    echo -e "${GREEN}✓ PASS${NC} - All unit tests"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} - Some unit tests failed"
    ((FAILED++))
fi

echo -e "\n${YELLOW}Phase 3: API Tests${NC}"
echo "------------------------------------------------------------"

# API 서버 시작 (백그라운드)
echo "Starting API server..."
python api/app_odds_based.py > /tmp/api_test.log 2>&1 &
API_PID=$!

# 서버 시작 대기
sleep 5

# Health check
echo -e "\nTesting: API Health Check"
if curl -s http://localhost:5001/api/health | grep -q "ok"; then
    echo -e "${GREEN}✓ PASS${NC} - Health check"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} - Health check"
    ((FAILED++))
fi

# Odds endpoint
echo -e "\nTesting: Odds API (demo mode)"
if curl -s "http://localhost:5001/api/odds/live?use_demo=true" | python -m json.tool > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC} - Odds API"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} - Odds API"
    ((FAILED++))
fi

# Value Bets endpoint
echo -e "\nTesting: Value Bets API"
if curl -s "http://localhost:5001/api/value-bets?use_demo=true" | python -m json.tool > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC} - Value Bets API"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} - Value Bets API"
    ((FAILED++))
fi

# Dashboard endpoint
echo -e "\nTesting: Dashboard API"
if curl -s "http://localhost:5001/api/dashboard?use_demo=true" | python -m json.tool > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC} - Dashboard API"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} - Dashboard API"
    ((FAILED++))
fi

# Kelly Calculator
echo -e "\nTesting: Kelly Calculator API"
if curl -s -X POST http://localhost:5001/api/kelly/calculate \
    -H "Content-Type: application/json" \
    -d '{"win_probability":0.6,"decimal_odds":2.0,"bankroll":10000}' \
    | python -m json.tool > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PASS${NC} - Kelly Calculator API"
    ((PASSED++))
else
    echo -e "${RED}✗ FAIL${NC} - Kelly Calculator API"
    ((FAILED++))
fi

# API 서버 종료
kill $API_PID 2>/dev/null

echo -e "\n============================================================"
echo "📊 Test Results"
echo "============================================================"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo "Total: $((PASSED + FAILED))"

if [ $FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✅ All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}❌ Some tests failed. Check logs above.${NC}"
    exit 1
fi
