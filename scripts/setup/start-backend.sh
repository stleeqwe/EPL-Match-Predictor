#!/bin/bash

echo "🚀 Starting EPL Match Predictor Backend..."
echo ""

# 가상환경 활성화
source venv/bin/activate

# Flask 서버 실행
cd backend
echo "✅ Backend server starting at http://localhost:5000"
python api/app.py
