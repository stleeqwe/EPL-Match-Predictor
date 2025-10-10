#!/bin/bash

echo "=========================================="
echo "🚀 EPL Squad Data Updater"
echo "=========================================="
echo ""

# 백엔드 디렉토리로 이동
cd "$(dirname "$0")"

# Python 가상환경 확인
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Please run: python3 -m venv venv"
    exit 1
fi

# 가상환경 활성화
source venv/bin/activate

# 의존성 확인
echo "📦 Checking dependencies..."
pip install -q requests flask flask-cors flask-caching 2>/dev/null

echo ""
echo "🔄 Updating squad data from Fantasy Premier League API..."
echo ""

# Python 스크립트 실행
python3 scripts/update_squad_from_fpl.py

echo ""
echo "=========================================="
echo "✅ Update complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Restart your backend server"
echo "  2. Check: curl http://localhost:5001/api/teams"
echo ""
