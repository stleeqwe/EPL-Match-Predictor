# 🔄 Migration Guide: v1.0 → v2.0

**기존 Dixon-Coles 예측 시스템** → **배당률 기반 Value Betting 시스템**

---

## 📋 요약

### 변경 사항

| 항목 | v1.0 (Before) | v2.0 (After) |
|------|---------------|--------------|
| **핵심 접근** | Dixon-Coles 모델로 예측 | 북메이커 배당률 활용 |
| **목표** | 경기 결과 예측 | Value Bet 탐지 |
| **데이터 소스** | FBref, Understat (경기 통계) | The Odds API (배당률) |
| **API 엔드포인트** | `/api/predict` | `/api/value-bets`, `/api/dashboard` |
| **Frontend** | 경기 예측 결과 표시 | 배당률 비교 + Value Bet 표시 |

---

## 🚀 Step-by-Step Migration

### Step 1: 기존 시스템 백업

```bash
cd /Users/pukaworks/Desktop/soccer-predictor

# Git commit (현재 상태 저장)
git add .
git commit -m "Backup before v2.0 migration"
git tag v1.0-backup

# 또는 디렉토리 복사
cp -r /Users/pukaworks/Desktop/soccer-predictor /Users/pukaworks/Desktop/soccer-predictor-v1-backup
```

### Step 2: 새로운 의존성 설치

```bash
cd backend

# 가상환경 활성화
source venv/bin/activate

# Requirements 업데이트 (이미 완료됨)
pip install -r requirements.txt

# 테스트 실행으로 검증
pytest tests/ -v
```

### Step 3: API 서버 전환

#### 옵션 A: 새 API 서버로 완전 전환 (권장)

```bash
# 기존 app.py 백업
mv backend/api/app.py backend/api/app_v1_backup.py

# 새 API를 메인으로 설정
cp backend/api/app_odds_based.py backend/api/app.py

# 서버 실행
python backend/api/app.py
```

#### 옵션 B: 병렬 운영 (점진적 전환)

```bash
# v1.0 API: 포트 5001
python backend/api/app.py &

# v2.0 API: 포트 5002
python backend/api/app_odds_based.py --port 5002 &

# 두 시스템 동시 테스트 가능
```

### Step 4: Frontend 전환

```bash
cd frontend/epl-predictor

# 기존 App.js 백업
mv src/App.js src/App_v1_backup.js

# 새 버전 적용
cp src/App_v2.js src/App.js

# 개발 서버 재시작
npm start
```

### Step 5: 환경 변수 설정

```bash
# backend/.env 파일 생성
cat > backend/.env << EOF
# The Odds API (필수)
ODDS_API_KEY=your_api_key_here

# Flask
ALLOWED_ORIGINS=http://localhost:3000
SECRET_KEY=$(openssl rand -base64 32)

# Logging
LOG_LEVEL=INFO
EOF

# The Odds API 키 발급
# 1. https://the-odds-api.com/ 방문
# 2. 무료 회원가입
# 3. API 키 복사 후 .env에 추가
```

### Step 6: 테스트

```bash
# 1. 백엔드 테스트
cd backend
pytest tests/ -v

# 2. API 엔드포인트 테스트
curl http://localhost:5001/api/health
curl "http://localhost:5001/api/dashboard?use_demo=true" | python -m json.tool

# 3. 프론트엔드 테스트
# 브라우저에서 http://localhost:3000 접속
# - Odds Comparison 탭 확인
# - Value Bets 탭 확인
# - Kelly Calculator 탭 확인
```

---

## 🔍 주요 변경 사항 상세

### 1. API 엔드포인트 매핑

| v1.0 Endpoint | v2.0 Replacement | 설명 |
|---------------|------------------|------|
| `GET /api/fixtures` | `GET /api/odds/live` | 경기 일정 → 실시간 배당률 |
| `POST /api/predict` | `GET /api/value-bets` | 예측 → Value Bet 탐지 |
| `GET /api/team-stats/<team>` | `GET /api/odds/analyze/<match_id>` | 팀 통계 → 경기 배당률 분석 |
| - | `POST /api/kelly/calculate` | 🆕 Kelly Criterion |
| - | `GET /api/dashboard` | 🆕 통합 대시보드 |

### 2. 데이터 구조 변경

#### v1.0 Prediction Response:
```json
{
  "home_win": 55.0,
  "draw": 25.0,
  "away_win": 20.0,
  "expected_home_goals": 2.3,
  "expected_away_goals": 1.5
}
```

#### v2.0 Value Bet Response:
```json
{
  "match": "Manchester City vs Liverpool",
  "outcome": "home",
  "bookmaker": "Bet365",
  "odds": 1.80,
  "edge_percent": 8.0,
  "confidence": 0.82,
  "recommendation": "MODERATE BET",
  "kelly_stake": 3.2
}
```

### 3. Frontend 컴포넌트 변경

| v1.0 Component | v2.0 Replacement |
|----------------|------------------|
| `PredictionResult.js` | `OddsComparison.js` |
| `TopScores.js` | `ValueBetCard.js` |
| `WeightEditor.js` | `KellyCalculator.js` |
| - | `OddsDashboard.js` (메인) |

---

## 🔧 문제 해결

### Issue 1: "ODDS_API_KEY not found"

```bash
# 환경 변수 확인
echo $ODDS_API_KEY

# 설정
export ODDS_API_KEY='your_key'

# 또는 데모 모드 사용
curl "http://localhost:5001/api/odds/live?use_demo=true"
```

### Issue 2: Import Error (odds_collection not found)

```bash
# PYTHONPATH 설정
export PYTHONPATH=/Users/pukaworks/Desktop/soccer-predictor/backend:$PYTHONPATH

# 또는 sys.path 확인
python -c "import sys; print(sys.path)"
```

### Issue 3: Frontend가 API를 찾지 못함

```javascript
// frontend/epl-predictor/.env
REACT_APP_API_URL=http://localhost:5001/api
```

### Issue 4: 기존 Dixon-Coles 모델을 계속 사용하고 싶음

```bash
# v1.0 API 백업본 사용
python backend/api/app_v1_backup.py --port 5003

# 또는 v2.0에서 auxiliary 엔드포인트 사용
curl -X POST http://localhost:5001/api/auxiliary/dixon-coles \
  -H "Content-Type: application/json" \
  -d '{"home_team":"Man City","away_team":"Liverpool"}'
```

---

## 📊 기능 비교

### v1.0에서 제거된 기능

- ❌ Player Rating Manager (개인 분석)
- ❌ Hybrid Model (Stats + Personal)
- ❌ Weight Editor (시간 가중치)
- ❌ XGBoost 앙상블

**이유:** 북메이커 배당률이 더 정확하므로 불필요

### v2.0 새로운 기능

- ✅ Real-time Odds Aggregation
- ✅ Value Bet Detection
- ✅ Arbitrage Finder
- ✅ Kelly Criterion Calculator
- ✅ Bookmaker Comparison
- ✅ Market Efficiency Analysis

---

## 🎯 롤백 방법 (v2.0 → v1.0)

문제 발생 시 v1.0으로 돌아가는 방법:

```bash
# 1. Git 사용 시
git checkout v1.0-backup

# 2. 백업 디렉토리 사용 시
cd /Users/pukaworks/Desktop
rm -rf soccer-predictor
mv soccer-predictor-v1-backup soccer-predictor

# 3. 파일 복원
cd soccer-predictor/backend/api
mv app_v1_backup.py app.py

cd ../../frontend/epl-predictor/src
mv App_v1_backup.js App.js

# 4. 서버 재시작
python backend/api/app.py
npm start
```

---

## ✅ 마이그레이션 체크리스트

### 백엔드

- [ ] 기존 시스템 백업 완료
- [ ] 새 requirements.txt 설치
- [ ] 환경 변수 (.env) 설정
- [ ] API 서버 전환 (app.py)
- [ ] 테스트 실행 (pytest) 통과
- [ ] /api/health 엔드포인트 확인
- [ ] /api/dashboard?use_demo=true 작동 확인

### 프론트엔드

- [ ] 기존 App.js 백업
- [ ] 새 App_v2.js → App.js 적용
- [ ] npm 의존성 최신 상태 확인
- [ ] 개발 서버 재시작
- [ ] Odds Comparison 탭 작동 확인
- [ ] Value Bets 탭 작동 확인
- [ ] Kelly Calculator 작동 확인

### 선택사항

- [ ] The Odds API 키 발급 및 설정
- [ ] 실제 API로 테스트 (use_demo=false)
- [ ] 기존 v1.0 시스템 완전 제거

---

## 📚 추가 리소스

- **새 시스템 문서**: `README_v2.md`
- **Quick Start**: `QUICKSTART_V2.md`
- **API 문서**: `GET http://localhost:5001/api/docs`
- **테스트 실행**: `pytest backend/tests/ -v`

---

## 💬 FAQ

**Q: v1.0 데이터베이스는 어떻게 되나요?**  
A: v2.0은 별도 API를 사용하므로 기존 DB(`soccer_predictor.db`)는 영향받지 않습니다. 보관 또는 삭제 가능합니다.

**Q: Dixon-Coles 모델을 완전히 버리나요?**  
A: 아니오. `/api/auxiliary/dixon-coles` 엔드포인트로 여전히 사용 가능하며, 북메이커 배당률과 비교용으로 활용할 수 있습니다.

**Q: The Odds API 무료 티어로 충분한가요?**  
A: 월 500 requests로 개발/테스트는 충분합니다. 프로덕션에서는 유료 플랜 권장합니다.

**Q: 프론트엔드를 v1.0 스타일로 유지하고 싶어요.**  
A: `src/App_v1_backup.js`를 계속 사용하거나, 새 컴포넌트를 선택적으로 통합할 수 있습니다.

---

**마이그레이션 완료!** 🎉

v2.0 시스템으로 배당률 기반 스마트 베팅 분석을 시작하세요!
