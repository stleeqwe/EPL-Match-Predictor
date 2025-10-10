# ⚽ EPL Odds-Based Value Betting System

**Version 2.0 - Pivot to Bookmaker Odds Analysis**

배당률 기반 Value Betting 시스템 - 북메이커의 배당률을 활용한 스마트 베팅 분석

---

## 🎯 핵심 개념

### 왜 배당률 기반 시스템인가?

**학술적 증거:**
- Dixon-Coles 모델: RPS 0.201
- **북메이커 배당률: RPS 0.193** ✅ (더 정확함)
- 북메이커는 수백만 달러를 걸고 최고의 전문가들이 만든 예측

**북메이커를 이기는 것은 불가능하지만, 활용하는 것은 가능합니다:**

1. **북메이커 간 배당률 차이 활용**
   - Pinnacle (가장 낮은 마진) vs 다른 북메이커
   - Value Betting: 시장 가격보다 높은 배당률 찾기

2. **Arbitrage (무위험 차익거래)**
   - 여러 북메이커의 배당률 차이로 무조건 수익
   - 매우 드물지만 존재함

3. **Kelly Criterion 자금 관리**
   - 장기적 자산 최대화
   - 리스크 관리

---

## 📋 프로젝트 구조

```
soccer-predictor/
├── backend/
│   ├── odds_collection/          # 🆕 배당률 수집
│   │   ├── odds_api_client.py   # The Odds API
│   │   └── odds_aggregator.py   # 다중 북메이커 통합
│   ├── value_betting/            # 🆕 Value Betting 엔진
│   │   ├── value_detector.py    # Value Bet 탐지
│   │   ├── arbitrage_finder.py  # Arbitrage 탐색
│   │   └── kelly_calculator.py  # Kelly Criterion
│   ├── api/
│   │   └── app_odds_based.py    # 🆕 새로운 API
│   └── models/
│       └── dixon_coles.py        # 보조 역할 (비교용)
└── frontend/
    └── epl-predictor/            # React 프론트엔드 (업데이트 예정)
```

---

## 🚀 빠른 시작

### 1. The Odds API 키 발급 (무료)

```bash
# 1. https://the-odds-api.com/ 방문
# 2. 무료 회원가입 (월 500 requests)
# 3. API 키 복사

# 4. 환경 변수 설정
export ODDS_API_KEY='your_api_key_here'

# 또는 .env 파일 생성
echo "ODDS_API_KEY=your_api_key_here" > backend/.env
```

### 2. 백엔드 실행

```bash
cd /Users/pukaworks/Desktop/soccer-predictor/backend

# 가상환경 활성화
source venv/bin/activate

# 의존성 설치 (pytest 추가됨)
pip install -r requirements.txt

# 새로운 API 서버 실행
python api/app_odds_based.py
```

서버가 `http://localhost:5001`에서 실행됩니다.

### 3. API 테스트

#### 데모 모드 (API 키 없이)

```bash
# 실시간 배당률 (데모)
curl "http://localhost:5001/api/odds/live?use_demo=true"

# Value Bets 탐지
curl "http://localhost:5001/api/value-bets?use_demo=true"

# Arbitrage 기회
curl "http://localhost:5001/api/arbitrage?use_demo=true"

# 통합 대시보드
curl "http://localhost:5001/api/dashboard?use_demo=true"
```

#### 실제 API 사용 (API 키 필요)

```bash
# API 키가 환경 변수에 설정되어 있어야 함
curl "http://localhost:5001/api/odds/live"
```

---

## 📊 API 엔드포인트

### Core Endpoints

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/health` | 헬스 체크 |
| GET | `/api/status` | 시스템 상태 |
| GET | `/api/odds/live` | 실시간 EPL 배당률 |
| GET | `/api/odds/analyze/<match_id>` | 특정 경기 분석 |
| GET | `/api/value-bets` | Value Bet 탐지 |
| GET | `/api/arbitrage` | Arbitrage 기회 |
| POST | `/api/kelly/calculate` | Kelly Criterion 계산 |
| POST | `/api/kelly/portfolio` | 포트폴리오 배분 |
| GET | `/api/dashboard` | 통합 대시보드 |

### Auxiliary Endpoints

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/auxiliary/dixon-coles` | Dixon-Coles 예측 (비교용) |

---

## 💡 사용 예시

### 1. Value Bet 탐지

```bash
curl -X GET "http://localhost:5001/api/value-bets?min_edge=0.03&min_confidence=0.7&use_demo=true" \
  | python -m json.tool
```

**응답 예시:**
```json
{
  "value_bets": [
    {
      "match": "Manchester City vs Liverpool",
      "outcome": "home",
      "bookmaker": "Bet365",
      "odds": 1.80,
      "true_probability": 0.60,
      "edge_percent": 8.0,
      "confidence": 0.82,
      "recommendation": "MODERATE BET",
      "kelly_stake": 3.2
    }
  ],
  "summary": {
    "total_value_bets": 1,
    "avg_edge": 0.08,
    "strong_bets": 0,
    "moderate_bets": 1
  }
}
```

### 2. Kelly Criterion 계산

```bash
curl -X POST "http://localhost:5001/api/kelly/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "win_probability": 0.60,
    "decimal_odds": 2.00,
    "bankroll": 10000
  }' | python -m json.tool
```

**응답:**
```json
{
  "kelly_percent": 5.0,
  "bet_amount": 500.0,
  "edge": 20.0,
  "fraction_used": 0.25
}
```

### 3. Arbitrage 탐색

```bash
curl "http://localhost:5001/api/arbitrage?min_profit=0.01&use_demo=true"
```

---

## 🧪 테스트

### 단위 테스트 실행

```bash
cd backend

# 모든 테스트 실행
pytest tests/ -v

# 커버리지 포함
pytest tests/ --cov=odds_collection --cov=value_betting --cov-report=html

# 특정 테스트만
pytest tests/test_value_detector.py -v
```

### 모듈별 테스트

```bash
# Odds API Client 테스트
python -m odds_collection.odds_api_client

# Value Detector 테스트
python -m value_betting.value_detector

# Arbitrage Finder 테스트
python -m value_betting.arbitrage_finder

# Kelly Calculator 테스트
python -m value_betting.kelly_calculator
```

---

## 📚 이론적 배경

### 1. Value Betting

**핵심 공식:**
```
Expected Value (EV) = (True Probability × Odds) - 1

Value Bet 조건: EV > 0
```

**예시:**
- Pinnacle: Man City 승 @ 1.75 (True Prob: 57%)
- Bet365: Man City 승 @ 1.80 (Implied Prob: 56%)
- EV = 0.57 × 1.80 - 1 = 0.026 = **2.6% edge** ✅

### 2. Kelly Criterion

**공식:**
```
f* = (p × b - q) / b

where:
  p = 승리 확률
  q = 1 - p
  b = 배당률 - 1
  f* = 베팅 비율
```

**Fractional Kelly:**
- Full Kelly: 매우 공격적, 높은 변동성
- **Quarter Kelly (권장)**: f* / 4, 보수적

### 3. Arbitrage

**조건:**
```
1/odds_home + 1/odds_draw + 1/odds_away < 1.0
```

매우 드물며 빠르게 사라짐!

---

## 🔧 설정

### 환경 변수 (.env)

```bash
# The Odds API
ODDS_API_KEY=your_api_key_here

# Flask
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
SECRET_KEY=your_secret_key

# 기타
LOG_LEVEL=INFO
```

### 고급 설정

```python
# Value Detector 파라미터 조정
value_detector = ValueDetector(
    min_edge=0.03,           # 최소 3% edge
    min_confidence=0.70,     # 최소 70% 신뢰도
    use_pinnacle_as_truth=True
)

# Kelly Criterion 파라미터
kelly = KellyCriterion(
    fraction=0.25,  # Quarter Kelly
    max_bet=0.05    # 최대 5%
)
```

---

## 📈 성능 지표

### 북메이커 배당률 vs 모델

| 모델 | RPS (낮을수록 좋음) | 정확도 |
|------|---------------------|--------|
| **Pinnacle 배당률** | **0.193** | **Best** |
| Dixon-Coles | 0.201 | 53-55% |
| XGBoost | 0.205 | 52-54% |

### Value Betting 기대 수익

- **장기 ROI**: 2-5% (현실적)
- **연간 베팅**: 100-200회
- **성공률**: 55-60% (value bets만)

⚠️ **주의**: 과거 성과가 미래를 보장하지 않습니다!

---

## 🚧 향후 개선 사항

### Phase 1 (완료) ✅
- [x] Odds API 통합
- [x] Value Betting 엔진
- [x] Arbitrage Finder
- [x] Kelly Criterion
- [x] 단위 테스트

### Phase 2 (진행 예정)
- [ ] React 프론트엔드 업데이트
- [ ] 실시간 배당률 모니터링
- [ ] 알림 시스템 (Value Bet 발견 시)
- [ ] 베팅 히스토리 추적

### Phase 3 (계획)
- [ ] 추가 리그 지원 (LaLiga, Serie A)
- [ ] 배당률 히스토리 분석
- [ ] 머신러닝 기반 edge 예측
- [ ] 모바일 앱

---

## ⚠️ 면책 조항

이 시스템은 **교육 목적**으로만 제공됩니다.

- 스포츠 베팅은 중독성이 있을 수 있습니다
- 책임감 있게 베팅하세요
- 잃어도 괜찮은 금액만 베팅하세요
- 법적 규제를 준수하세요

**개발자는 이 시스템 사용으로 인한 어떠한 손실에도 책임지지 않습니다.**

---

## 📞 지원

- **문서**: 이 README
- **이슈**: GitHub Issues
- **API 문서**: `GET /api/docs`

---

## 📝 라이선스

MIT License

---

**Version 2.0.0**  
**Last Updated**: 2025-10-03  
**Maintained By**: Engineering Team

🎯 **목표**: 북메이커를 이기는 것이 아니라, 북메이커를 **활용**하는 것!
