# EPL Match Predictor 🎯

축구 경기 승부 예측 시스템 - Dixon-Coles + XGBoost 하이브리드 모델

## 📋 프로젝트 구조

```
soccer-predictor/
├── backend/
│   ├── data_collection/    # FBref, Understat 스크래퍼
│   ├── models/             # Dixon-Coles, XGBoost, 앙상블
│   ├── api/                # Flask REST API
│   ├── database/           # SQLAlchemy 스키마
│   └── utils/              # 유틸리티 함수
├── frontend/
│   └── epl-predictor/      # React 프론트엔드
├── venv/                   # Python 가상환경
└── requirements.txt        # Python 패키지 목록
```

## 🚀 빠른 시작

### 1. 백엔드 실행

```bash
# 프로젝트 루트 디렉토리에서
source venv/bin/activate
python backend/api/app.py
```

서버가 `http://localhost:5000`에서 실행됩니다.

### 2. 프론트엔드 실행

새 터미널을 열고:

```bash
cd frontend/epl-predictor
npm start
```

브라우저가 자동으로 `http://localhost:3000`을 엽니다.

## 🔬 주요 기능

### 1. Data 분석 (통계 기반)
- **Dixon-Coles 모델** (1997): dependency parameter (ρ), time decay (ξ)
- **Pi-ratings**: 홈/원정 별도 레이팅 시스템
- 최근 5경기, 현재 시즌, 지난 시즌 데이터 가중치 조절

### 2. 개인 분석
- 팀별 선수 명단 관리
- 포지션별 능력치 입력
- 선수 평균 기반 팀 전력 계산

### 3. 하이브리드 예측
- 통계 모델 + 개인 분석 가중치 조절
- XGBoost 앙상블
- 실시간 확률 업데이트

## 📊 API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/health` | 헬스 체크 |
| GET | `/api/fixtures` | EPL 경기 일정 |
| POST | `/api/predict` | 경기 예측 |
| GET | `/api/teams` | 팀 목록 |
| GET | `/api/team-stats/<team>` | 팀 통계 |
| GET | `/api/squad/<team>` | 선수 명단 |

### 예측 API 예시

```bash
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "home_team": "Manchester City",
    "away_team": "Liverpool",
    "model_type": "hybrid",
    "stats_weight": 75,
    "personal_weight": 25
  }'
```

응답:
```json
{
  "home_win": 55.0,
  "draw": 25.0,
  "away_win": 20.0,
  "expected_home_goals": 2.3,
  "expected_away_goals": 1.5,
  "top_scores": [
    {"score": "2-1", "probability": 16.2},
    {"score": "3-0", "probability": 14.1}
  ]
}
```

## 🧪 모델 설명

### Dixon-Coles 모델 (1997)

**핵심 공식:**
```
λ_home = α_home × β_away × γ × 1.43
λ_away = α_away × β_home

P(결과) = Poisson(λ) × τ(i,j)
```

**파라미터:**
- α: 공격력 (attack strength)
- β: 수비력 (defense strength)
- γ: 홈 어드밴티지 (약 1.3)
- τ: dependency correction (저점수 경기 보정)
- ξ: time decay (최근 경기 가중치, 0.0065)

### Pi-ratings (Constantinou & Fenton, 2013)

- 홈/원정 별도 레이팅
- 학습률: λ = 0.06, γ = 0.6
- 골 차이 기반 업데이트
- 영점 중심 (평균 팀 = 0)

### XGBoost 앙상블

```python
XGBoost(
    n_estimators=500,
    max_depth=10,
    learning_rate=0.1,
    reg_alpha=0.9,
    reg_lambda=0.8
)
```

**특징:**
- Pi-ratings, 최근 폼, 홈/원정 통계
- 3-class 분류 (홈승/무/원정승)
- Soft voting 앙상블

## 📚 이론적 배경

### 주요 논문

1. **Dixon & Coles (1997)** - "Modelling Association Football Scores and Inefficiencies in the Football Betting Market"
   - 450+ 인용
   - dependency parameter 도입
   - time weighting 제안

2. **Constantinou & Fenton (2013)** - "Determining the level of ability of football teams by dynamic ratings"
   - Pi-ratings 시스템
   - EPL 북메이커 대비 수익성 입증

3. **Karlis & Ntzoufras (2003)** - "Analysis of sports data by using bivariate Poisson models"
   - Bivariate Poisson 적용
   - 무승부 예측 개선

### 성능 벤치마크

- **Dixon-Coles**: RPS 0.19-0.20
- **Pi-ratings + XGBoost**: RPS 0.1925 (최고 성능)
- **Voting ensemble**: 83-84% 정확도 (특정 리그)
- **일반 모델**: 52-67% 정확도 (3-class)

## 🔧 기술 스택

### Backend
- Python 3.9+
- Flask (REST API)
- SQLAlchemy (ORM)
- XGBoost (ML)
- SciPy (통계)
- Pandas, NumPy (데이터 처리)

### Frontend
- React 18
- Axios (HTTP)
- Lucide React (아이콘)
- Tailwind CSS

### Data Sources
- FBref.com (경기 통계)
- Understat.com (xG 데이터)

## 📈 향후 개선 사항

1. **실시간 데이터 수집**
   - 자동 스크래핑 스케줄러
   - 라이브 배당 통합

2. **고급 모델**
   - Transformer 기반 예측
   - Multi-modal 학습
   - Graph Neural Networks

3. **추가 기능**
   - 부상/출전 정보 통합
   - 선수 마켓 가치 분석
   - 경기 중 실시간 업데이트

4. **배포**
   - Docker 컨테이너화
   - PostgreSQL 마이그레이션
   - 웹 서비스 배포

## 📝 라이선스

MIT License

## 👤 개발자

프로젝트 생성: 2025-10-01

---

**참고:** 현재 버전은 로컬 개발용이며, 더미 데이터를 사용합니다. 실제 스크래핑 기능은 FBref/Understat의 이용 약관을 준수해야 합니다.
