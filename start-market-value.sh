#!/bin/bash

# Market Value 탭 - Quick Start 스크립트
# 프론트엔드와 백엔드를 한 번에 실행

echo "======================================================================"
echo "  Market Value 탭 - Quick Start"
echo "======================================================================"
echo ""

# 프로젝트 루트 디렉토리 확인
if [ ! -f "README.md" ]; then
    echo "❌ 오류: 프로젝트 루트 디렉토리에서 실행해주세요."
    exit 1
fi

echo "✅ 프로젝트 디렉토리 확인 완료"
echo ""

# 1. 백엔드 서버 실행 (백그라운드)
echo "🚀 백엔드 서버 실행 중..."
cd backend

# Python 가상환경 활성화 (있는 경우)
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Python 가상환경 활성화"
fi

# 백엔드 서버 실행 (백그라운드)
python api/app_odds_based.py > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "✅ 백엔드 서버 실행 (PID: $BACKEND_PID)"
echo "   Log: /tmp/backend.log"
echo ""

# 2초 대기 (서버 시작)
sleep 2

# 2. 프론트엔드 실행
echo "🎨 프론트엔드 실행 중..."
cd ../frontend/epl-predictor

# npm 의존성 확인
if [ ! -d "node_modules" ]; then
    echo "📦 npm 패키지 설치 중..."
    npm install
fi

# 프론트엔드 실행
npm start &
FRONTEND_PID=$!
echo "✅ 프론트엔드 실행 (PID: $FRONTEND_PID)"
echo ""

# 완료 메시지
echo "======================================================================"
echo "  ✅ Market Value 탭 실행 완료!"
echo "======================================================================"
echo ""
echo "📍 접속 정보:"
echo "   - 프론트엔드: http://localhost:3000"
echo "   - 백엔드 API: http://localhost:5001"
echo ""
echo "🎯 사용 방법:"
echo "   1. 브라우저에서 http://localhost:3000 접속"
echo "   2. 상단 네비게이션에서 '💰 Market Value' 탭 클릭"
echo "   3. Value Betting 기회 확인"
echo "   4. Kelly 계산기로 베팅 금액 계산"
echo ""
echo "⚠️  종료 방법:"
echo "   - 백엔드: kill $BACKEND_PID"
echo "   - 프론트엔드: kill $FRONTEND_PID"
echo "   - 또는: Ctrl+C (이 터미널에서)"
echo ""
echo "📚 문서:"
echo "   - 사용 가이드: frontend/epl-predictor/MARKET_VALUE_GUIDE.md"
echo "   - 구현 보고서: frontend/epl-predictor/MARKET_VALUE_IMPLEMENTATION.md"
echo ""
echo "💡 데모 모드:"
echo "   현재 데모 모드로 실행 중입니다."
echo "   실제 배당률을 받아오려면 The Odds API 키가 필요합니다."
echo "   https://the-odds-api.com/"
echo ""
echo "======================================================================"

# PID 파일 저장 (나중에 종료할 때 사용)
echo "$BACKEND_PID" > /tmp/market_value_backend.pid
echo "$FRONTEND_PID" > /tmp/market_value_frontend.pid

# 로그 실시간 출력 (선택사항)
# tail -f /tmp/backend.log

# 종료 시그널 대기
wait
