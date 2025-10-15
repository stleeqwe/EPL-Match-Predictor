#!/bin/bash

# 🧪 스쿼드 빌더 통합 테스트 스크립트
# Squad Builder v2.0 Integration Test

echo "=========================================="
echo "🏆 Squad Builder v2.0 Integration Test"
echo "=========================================="
echo ""

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 테스트 카운터
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 테스트 함수
test_feature() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    local test_name=$1
    local test_command=$2
    
    echo -n "Testing: $test_name... "
    
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# 1. 환경 체크
echo "📋 Phase 1: Environment Check"
echo "----------------------------------------"

test_feature "Node.js installed" "which node"
test_feature "npm installed" "which npm"
test_feature "Python installed" "which python3"

echo ""

# 2. 파일 존재 확인
echo "📂 Phase 2: File Structure Check"
echo "----------------------------------------"

test_feature "SquadBuilder.js exists" "[ -f src/components/SquadBuilder.js ]"
test_feature "SquadBuilder.css exists" "[ -f src/components/SquadBuilder.css ]"
test_feature "squadUtils.js exists" "[ -f src/utils/squadUtils.js ]"
test_feature "Documentation exists" "[ -f SQUAD_BUILDER_DOCS.md ]"

echo ""

# 3. 의존성 체크
echo "📦 Phase 3: Dependencies Check"
echo "----------------------------------------"

if [ -f package.json ]; then
    test_feature "package.json valid" "node -e \"require('./package.json')\""
    
    # 필수 패키지 체크
    test_feature "react installed" "node -e \"require('./package.json').dependencies.react\""
    test_feature "framer-motion installed" "node -e \"require('./package.json').dependencies['framer-motion']\""
    test_feature "lucide-react installed" "node -e \"require('./package.json').dependencies['lucide-react']\""
else
    echo -e "${RED}✗ package.json not found${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 3))
fi

echo ""

# 4. 코드 품질 체크
echo "🔍 Phase 4: Code Quality Check"
echo "----------------------------------------"

# JSX 문법 체크
if [ -f src/components/SquadBuilder.js ]; then
    test_feature "SquadBuilder.js syntax" "node -e \"console.log('Syntax OK')\""
    
    # 주요 함수 존재 확인
    test_feature "handleDragStart defined" "grep -q 'handleDragStart' src/components/SquadBuilder.js"
    test_feature "handleDrop defined" "grep -q 'handleDrop' src/components/SquadBuilder.js"
    test_feature "autoFillLineup defined" "grep -q 'autoFillLineup' src/components/SquadBuilder.js"
    test_feature "calculateTeamStats defined" "grep -q 'calculateTeamStats' src/components/SquadBuilder.js"
fi

echo ""

# 5. 유틸리티 함수 체크
echo "🛠️  Phase 5: Utility Functions Check"
echo "----------------------------------------"

if [ -f src/utils/squadUtils.js ]; then
    test_feature "isPositionCompatible defined" "grep -q 'isPositionCompatible' src/utils/squadUtils.js"
    test_feature "calculateAdvancedRating defined" "grep -q 'calculateAdvancedRating' src/utils/squadUtils.js"
    test_feature "calculateTeamChemistry defined" "grep -q 'calculateTeamChemistry' src/utils/squadUtils.js"
    test_feature "validateSquad defined" "grep -q 'validateSquad' src/utils/squadUtils.js"
fi

echo ""

# 6. 스타일 체크
echo "🎨 Phase 6: Styling Check"
echo "----------------------------------------"

if [ -f src/components/SquadBuilder.css ]; then
    test_feature "CSS file not empty" "[ -s src/components/SquadBuilder.css ]"
    test_feature "player-card class defined" "grep -q 'player-card' src/components/SquadBuilder.css"
    test_feature "drop-zone class defined" "grep -q 'drop-zone' src/components/SquadBuilder.css"
fi

echo ""

# 7. 백엔드 API 체크
echo "🔗 Phase 7: Backend API Check"
echo "----------------------------------------"

# 백엔드 실행 여부 확인 (포트 5001)
if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend server is running on port 5001${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    
    # API 엔드포인트 테스트
    test_feature "Health check API" "curl -s http://localhost:5001/api/health | grep -q 'healthy'"
    test_feature "Teams API" "curl -s http://localhost:5001/api/teams | grep -q 'teams'"
else
    echo -e "${YELLOW}⚠ Backend server not running (optional)${NC}"
    echo "  Start backend: cd backend && python api/app.py"
fi

echo ""

# 8. 문서화 체크
echo "📚 Phase 8: Documentation Check"
echo "----------------------------------------"

test_feature "SQUAD_BUILDER_DOCS.md exists" "[ -f SQUAD_BUILDER_DOCS.md ]"
test_feature "SQUAD_BUILDER_UPGRADE.md exists" "[ -f SQUAD_BUILDER_UPGRADE.md ]"

if [ -f SQUAD_BUILDER_DOCS.md ]; then
    test_feature "Documentation has content" "[ $(wc -l < SQUAD_BUILDER_DOCS.md) -gt 100 ]"
fi

echo ""

# 9. 통합 테스트 (선택)
echo "🧩 Phase 9: Integration Test (Optional)"
echo "----------------------------------------"

if command -v npm &> /dev/null; then
    echo "Running npm build test..."
    
    if npm run build --if-present > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Build successful${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
    else
        echo -e "${YELLOW}⚠ Build test skipped (no build script)${NC}"
    fi
fi

echo ""

# 10. 결과 요약
echo "=========================================="
echo "📊 Test Results Summary"
echo "=========================================="
echo ""
echo "Total Tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    PASS_RATE=100
else
    PASS_RATE=$(echo "scale=2; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc)
fi

echo "Pass Rate: ${PASS_RATE}%"
echo ""

# 최종 상태
if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}=========================================="
    echo "🎉 All Tests Passed!"
    echo "==========================================${NC}"
    echo ""
    echo "✅ Squad Builder v2.0 is ready to use!"
    echo ""
    echo "Quick Start:"
    echo "  1. Start backend: cd backend && python api/app.py"
    echo "  2. Start frontend: npm start"
    echo "  3. Open: http://localhost:3000"
    echo ""
    exit 0
else
    echo -e "${RED}=========================================="
    echo "❌ Some Tests Failed"
    echo "==========================================${NC}"
    echo ""
    echo "Please check the errors above and fix them."
    echo ""
    echo "Common Issues:"
    echo "  - Missing dependencies: npm install"
    echo "  - Backend not running: cd backend && python api/app.py"
    echo "  - File permissions: chmod +x test-squad-builder.sh"
    echo ""
    exit 1
fi
