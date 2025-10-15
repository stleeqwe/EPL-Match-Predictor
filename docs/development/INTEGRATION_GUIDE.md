# 백엔드-프론트엔드 완벽 연동 가이드

## 📋 목차
1. [시스템 구조](#시스템-구조)
2. [빠른 시작](#빠른-시작)
3. [백엔드 설정](#백엔드-설정)
4. [프론트엔드 설정](#프론트엔드-설정)
5. [API 엔드포인트](#api-엔드포인트)
6. [통합 테스트](#통합-테스트)
7. [문제 해결](#문제-해결)

---

## 시스템 구조

```
┌─────────────────────────────────────────────────────────┐
│                    사용자 (Browser)                      │
└──────────────────────┬──────────────────────────────────┘
                       │
                       │ HTTP Requests
                       ▼
┌─────────────────────────────────────────────────────────┐
│          Frontend (React - Port 3000)                    │
│  ┌───────────────────────────────────────────────────┐  │
│  │  - App.js (메인 컴포넌트)                         │  │
│  │  - services/api.js (API 호출 레이어)              │  │
│  │  - components/* (UI 컴포넌트)                     │  │
│  └───────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │
                       │ axios (http://localhost:5001/api)
                       ▼
┌─────────────────────────────────────────────────────────┐
│          Backend (Flask - Port 5001)                     │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Flask API (api/app.py)                           │  │
│  │  ├─ /api/predict (Dixon-Coles)                    │  │
│  │  ├─ /api/predict/bayesian (Bayesian MCMC)         │  │
│  │  ├─ /api/teams (팀 목록)                          │  │
│  │  ├─ /api/fixtures (경기 일정)                     │  │
│  │  └─ /api/team-stats/<name> (팀 통계)             │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Pre-trained Models (model_cache/)                │  │
│  │  ├─ bayesian_model_real.pkl (280KB)               │  │
│  │  └─ dixon_coles_real.pkl                          │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Data Sources                                      │  │
│  │  ├─ soccer_predictor.db (SQLite - 1000 matches)   │  │
│  │  └─ data/epl_real_understat.csv (760 matches)     │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 빠른 시작

### 1단계: 백엔드 실행

```bash
# 프로젝트 루트에서
./start_backend.sh
```

**출력 예시:**
```
======================================
EPL Predictor Backend Server
======================================

Activating virtual environment...
Installing dependencies...
✓ Trained models found
  - bayesian_model_real.pkl
  - dixon_coles_real.pkl

======================================
Starting Flask API Server...
======================================

Server will start on: http://localhost:5001
```

### 2단계: 프론트엔드 실행 (새 터미널)

```bash
# 프로젝트 루트에서
./start_frontend.sh
```

**출력 예시:**
```
======================================
EPL Predictor Frontend (React)
======================================

✓ Dependencies already installed

Starting React Development Server...

Frontend will start on: http://localhost:3000
```

### 3단계: 브라우저 접속

```
http://localhost:3000
```

---

## 백엔드 설정

### 디렉토리 구조

```
backend/
├── api/
│   └── app.py                    # Flask API 서버
├── model_cache/
│   ├── bayesian_model_real.pkl   # 사전 학습된 베이지안 모델
│   └── dixon_coles_real.pkl      # 사전 학습된 Dixon-Coles
├── models/
│   ├── dixon_coles.py
│   ├── bayesian_dixon_coles_simplified.py
│   └── ensemble.py
├── data_collection/
│   └── production_data_pipeline.py
├── database/
│   └── schema.py
├── utils/
│   └── time_weighting.py
├── scripts/
│   ├── train_fast.py             # 빠른 모델 학습
│   ├── evaluate_models.py        # 모델 평가
│   └── test_api_load.py          # API 통합 테스트
├── requirements.txt              # Python 의존성
└── soccer_predictor.db           # SQLite 데이터베이스
```

### Python 의존성 설치

```bash
cd backend

# 가상환경 생성 (처음 한 번만)
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# 패키지 설치
pip install -r requirements.txt
```

### 필수 의존성

```txt
flask==3.0.0              # Web framework
flask-cors==4.0.0         # Cross-Origin Resource Sharing
flask-caching==2.1.0      # API response caching
pandas==2.1.4             # Data processing
numpy==1.26.2             # Numerical computing
scipy==1.11.4             # Scientific computing
scikit-learn==1.3.2       # Machine learning utilities
sqlalchemy==2.0.23        # Database ORM
beautifulsoup4==4.12.2    # Web scraping
requests==2.31.0          # HTTP library
```

### 환경 변수 (선택사항)

```bash
# backend/.env (생성 필요 없음 - 기본값 사용)
FLASK_ENV=development
FLASK_APP=api/app.py
```

### Flask 서버 수동 실행

```bash
cd backend
source venv/bin/activate

# 방법 1: Flask CLI
flask run --host=0.0.0.0 --port=5001

# 방법 2: Python 직접 실행
python3 api/app.py
```

---

## 프론트엔드 설정

### 디렉토리 구조

```
frontend/epl-predictor/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── Header.js
│   │   ├── MatchSelector.js
│   │   ├── PredictionResult.js
│   │   ├── StandingsTable.js
│   │   ├── EvaluationDashboard.js
│   │   └── ... (기타 컴포넌트)
│   ├── services/
│   │   └── api.js                # ✅ 백엔드 API 호출 레이어
│   ├── hooks/
│   │   └── useToast.js
│   ├── App.js                    # 메인 애플리케이션
│   ├── App.css
│   └── index.js
├── .env                          # ✅ 환경 변수 설정
├── package.json
└── tailwind.config.js
```

### npm 의존성 설치

```bash
cd frontend/epl-predictor
npm install
```

### 주요 의존성

```json
{
  "axios": "^1.12.2",           // HTTP 클라이언트
  "react": "^19.1.1",           // UI 라이브러리
  "react-dom": "^19.1.1",
  "recharts": "^3.2.1",         // 차트 시각화
  "framer-motion": "^12.23.22", // 애니메이션
  "lucide-react": "^0.544.0",   // 아이콘
  "tailwindcss": "^3.4.17"      // CSS 프레임워크
}
```

### 환경 변수 (.env)

**파일 위치:** `/frontend/epl-predictor/.env`

```bash
REACT_APP_API_URL=http://localhost:5001/api
```

**중요:**
- 파일명은 정확히 `.env` (dot env)
- `REACT_APP_` 접두사 필수
- 변경 후 개발 서버 재시작 필요

### React 개발 서버 수동 실행

```bash
cd frontend/epl-predictor
npm start
```

---

## API 엔드포인트

### 1. 예측 관련

#### POST `/api/predict`
**Dixon-Coles 예측 (빠른 예측)**

**요청:**
```json
{
  "home_team": "Manchester City",
  "away_team": "Liverpool",
  "model_type": "statistical",
  "stats_weight": 75,
  "personal_weight": 25,
  "save_prediction": true
}
```

**응답:**
```json
{
  "home_win": 45.3,
  "draw": 26.7,
  "away_win": 28.0,
  "expected_home_goals": 1.75,
  "expected_away_goals": 1.32,
  "top_scores": [
    {"score": "2-1", "probability": 12.5},
    {"score": "1-1", "probability": 11.2}
  ]
}
```

#### POST `/api/predict/bayesian`
**Bayesian Dixon-Coles (불확실성 정량화)**

**요청:**
```json
{
  "home_team": "Arsenal",
  "away_team": "Chelsea",
  "n_sims": 3000,
  "credible_interval": 0.95,
  "use_cached": true
}
```

**응답:**
```json
{
  "home_win": 48.5,
  "draw": 25.3,
  "away_win": 26.2,
  "expected_home_goals": 1.82,
  "expected_away_goals": 1.28,
  "credible_intervals": {
    "home_goals": [0.8, 2.9],
    "away_goals": [0.6, 2.1],
    "goal_difference": [-1.2, 2.5]
  },
  "top_scores": [...],
  "risk_metrics": {
    "var_95": 1.23,
    "cvar_95": 1.45,
    "prediction_entropy": 1.08
  },
  "model_info": {
    "type": "Bayesian Dixon-Coles (Metropolis-Hastings MCMC)",
    "n_simulations": 3000,
    "credible_interval": 0.95,
    "cached": true
  }
}
```

### 2. 팀 관련

#### GET `/api/teams`
**EPL 팀 목록 조회**

**응답:**
```json
[
  "Arsenal",
  "Aston Villa",
  "Bournemouth",
  "Brentford",
  "Brighton",
  ...
]
```

#### GET `/api/team-stats/{team_name}`
**특정 팀 통계**

**예시:** `/api/team-stats/Arsenal`

**응답:**
```json
{
  "pi_ratings": {
    "home": 1.42,
    "away": 1.28
  },
  "recent_form": {
    "wins": 3,
    "draws": 1,
    "losses": 1,
    "goals_scored": 8,
    "goals_conceded": 5
  },
  "home_stats": {
    "matches": 19,
    "avg_goals_scored": 2.1,
    "avg_goals_conceded": 1.2
  },
  "away_stats": {
    "matches": 19,
    "avg_goals_scored": 1.8,
    "avg_goals_conceded": 1.4
  }
}
```

### 3. 경기 일정

#### GET `/api/fixtures`
**EPL 경기 일정**

**응답:**
```json
[
  {
    "date": "2025-10-05",
    "home_team": "Manchester City",
    "away_team": "Liverpool",
    "status": "scheduled"
  },
  ...
]
```

### 4. 순위표

#### GET `/api/standings?season=2024-2025`
**리그 순위표**

**응답:**
```json
[
  {
    "position": 1,
    "team": "Liverpool",
    "played": 38,
    "won": 28,
    "drawn": 6,
    "lost": 4,
    "points": 90
  },
  ...
]
```

### 5. 헬스 체크

#### GET `/api/health`
**서버 상태 확인**

**응답:**
```json
{
  "status": "ok",
  "message": "API is running"
}
```

---

## 통합 테스트

### 1. 백엔드 단독 테스트

```bash
cd backend
python3 scripts/test_api_load.py
```

**예상 출력:**
```
============================================================
Testing Real Model Integration
============================================================

1. Loading Bayesian Model...
✓ Loaded: /path/to/bayesian_model_real.pkl

2. Loading Dixon-Coles Model...
✓ Loaded: /path/to/dixon_coles_real.pkl

3. Loading Historical Data...
✓ Loaded 760 matches

============================================================
✅ All Models Working Correctly!
============================================================
```

### 2. API 엔드포인트 테스트

**터미널 1 - 백엔드 실행:**
```bash
./start_backend.sh
```

**터미널 2 - curl 테스트:**

```bash
# Health check
curl http://localhost:5001/api/health

# 팀 목록
curl http://localhost:5001/api/teams

# 예측 (Dixon-Coles)
curl -X POST http://localhost:5001/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "home_team": "Arsenal",
    "away_team": "Chelsea",
    "model_type": "statistical"
  }'

# Bayesian 예측
curl -X POST http://localhost:5001/api/predict/bayesian \
  -H "Content-Type: application/json" \
  -d '{
    "home_team": "Manchester City",
    "away_team": "Liverpool",
    "n_sims": 1000,
    "use_cached": true
  }'
```

### 3. 프론트엔드-백엔드 통합 테스트

1. **백엔드 실행 (터미널 1)**
   ```bash
   ./start_backend.sh
   ```

2. **프론트엔드 실행 (터미널 2)**
   ```bash
   ./start_frontend.sh
   ```

3. **브라우저 테스트**
   - `http://localhost:3000` 접속
   - 브라우저 개발자 도구 (F12) → Console 탭 확인
   - 예상 로그:
     ```
     API Request: GET /teams
     API Response: 200 /teams
     API Request: POST /predict
     API Response: 200 /predict
     ```

4. **기능 테스트 체크리스트**
   - [ ] 팀 목록이 드롭다운에 표시되는가?
   - [ ] 예측 버튼 클릭 시 결과가 나타나는가?
   - [ ] 확률이 0-100% 범위로 표시되는가?
   - [ ] 예상 득점이 표시되는가?
   - [ ] 로딩 스피너가 작동하는가?
   - [ ] 에러 메시지가 적절히 표시되는가?

---

## 문제 해결

### 문제 1: 백엔드 포트 5001 이미 사용 중

**증상:**
```
Address already in use
```

**해결:**
```bash
# 포트 사용 프로세스 확인
lsof -i :5001

# 프로세스 종료
kill -9 <PID>

# 또는 다른 포트 사용
flask run --port=5002
```

프론트엔드 `.env` 파일도 업데이트:
```bash
REACT_APP_API_URL=http://localhost:5002/api
```

### 문제 2: CORS 에러

**증상:**
```
Access to XMLHttpRequest has been blocked by CORS policy
```

**확인 사항:**
1. `backend/api/app.py`에 `CORS(app)` 설정 확인
2. 백엔드가 실제로 실행 중인지 확인
3. API URL이 정확한지 확인

**해결:**
```python
# backend/api/app.py
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # ← 이 줄 확인
```

### 문제 3: 모델 파일 없음

**증상:**
```
FileNotFoundError: bayesian_model_real.pkl
```

**해결:**
```bash
cd backend
python3 scripts/train_fast.py
```

### 문제 4: 프론트엔드가 백엔드에 연결 안 됨

**증상:**
```
Network Error
Error: Request failed with status code 404
```

**체크리스트:**
1. 백엔드가 실행 중인가? → `http://localhost:5001/api/health` 접속 테스트
2. 프론트엔드 `.env` 파일이 존재하는가?
3. `.env` 파일의 URL이 정확한가? → `http://localhost:5001/api`
4. React 서버를 재시작했는가? (`.env` 변경 시 필수)

### 문제 5: npm install 실패

**증상:**
```
Error: EACCES: permission denied
```

**해결:**
```bash
# node_modules 삭제 후 재설치
cd frontend/epl-predictor
rm -rf node_modules package-lock.json
npm install
```

### 문제 6: Python 패키지 설치 실패

**증상:**
```
ERROR: Failed building wheel for scipy
```

**해결 (macOS):**
```bash
# Xcode Command Line Tools 설치
xcode-select --install

# 필요한 라이브러리 설치
brew install openblas

# 재시도
pip install -r requirements.txt
```

### 문제 7: 예측 응답이 느림

**원인:** Bayesian MCMC 시뮬레이션은 시간이 걸립니다.

**해결:**
1. **캐시 사용** (기본값): `use_cached: true`
2. **시뮬레이션 횟수 줄이기**: `n_sims: 1000` (기본값 3000)
3. **Dixon-Coles 사용**: 빠른 예측 (<100ms)

### 문제 8: 데이터베이스 에러

**증상:**
```
sqlalchemy.exc.OperationalError: no such table: teams
```

**해결:**
```bash
cd backend

# 데이터 재로드
python3 scripts/load_real_data.py data/epl_real_understat.csv
```

---

## 추가 리소스

### 로그 확인

**백엔드 로그:**
- Flask 콘솔 출력 확인
- API 요청/응답이 자동으로 로깅됨

**프론트엔드 로그:**
- 브라우저 개발자 도구 → Console
- Network 탭에서 API 호출 상세 확인

### 성능 최적화

1. **API 캐싱**: Flask-Caching 활용 (이미 적용됨)
2. **모델 캐싱**: Bayesian 모델은 메모리에 캐시 (이미 적용됨)
3. **데이터 로딩**: CSV 직접 로드 (데이터베이스 ORM 대신)

### 개발 팁

1. **Hot Reload**
   - React: 코드 변경 시 자동 리로드
   - Flask: 코드 변경 시 자동 재시작 (`FLASK_ENV=development`)

2. **디버깅**
   - Flask: `app.run(debug=True)`
   - React: `console.log()` 활용

3. **API 테스트 도구**
   - Postman
   - curl
   - HTTPie

---

## 요약

✅ **백엔드**
- Flask API 서버 (포트 5001)
- 사전 학습된 모델 로드
- CORS 설정 완료
- 실제 EPL 데이터 760경기

✅ **프론트엔드**
- React 개발 서버 (포트 3000)
- Axios로 백엔드 API 호출
- 환경 변수 설정 완료
- Bayesian 예측 API 추가

✅ **통합**
- API 엔드포인트 17개
- 실시간 예측 및 통계
- 에러 처리 및 로딩 상태
- 완전 자동화된 스타트업 스크립트

---

**문의 및 피드백**
- GitHub Issues
- README.md 참조

**마지막 업데이트:** 2025-10-02
