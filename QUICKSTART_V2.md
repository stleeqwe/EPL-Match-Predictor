# 🚀 Quick Start Guide - Odds-Based Value Betting System

5분 안에 시작하기!

---

## ⚡ 1단계: API 테스트 (API 키 없이)

```bash
cd /Users/pukaworks/Desktop/soccer-predictor/backend

# 가상환경 활성화
source venv/bin/activate

# 새로운 API 서버 실행
python api/app_odds_based.py
```

**브라우저에서 확인:**
```
http://localhost:5001/api/health
```

---

## 📊 2단계: 데모 데이터로 테스트

### 터미널 1: API 서버 실행 중

### 터미널 2: API 호출

```bash
# 1. 실시간 배당률 조회 (데모)
curl "http://localhost:5001/api/odds/live?use_demo=true" | python -m json.tool

# 2. Value Bets 탐지
curl "http://localhost:5001/api/value-bets?use_demo=true&min_edge=0.02" | python -m json.tool

# 3. Arbitrage 기회
curl "http://localhost:5001/api/arbitrage?use_demo=true" | python -m json.tool

# 4. 통합 대시보드
curl "http://localhost:5001/api/dashboard?use_demo=true" | python -m json.tool
```

---

## 🔑 3단계: 실제 API 키 설정 (선택사항)

### The Odds API 무료 키 발급

1. https://the-odds-api.com/ 방문
2. 무료 회원가입 (이메일만)
3. API 키 복사
4. 환경 변수 설정:

```bash
# 방법 1: 환경 변수
export ODDS_API_KEY='your_api_key_here'

# 방법 2: .env 파일
cd backend
echo "ODDS_API_KEY=your_api_key_here" > .env
```

5. API 서버 재시작

```bash
python api/app_odds_based.py
```

6. 실제 데이터로 테스트:

```bash
# use_demo=true 제거
curl "http://localhost:5001/api/odds/live" | python -m json.tool
```

---

## 🧪 4단계: 테스트 실행

```bash
cd backend

# 모든 테스트 실행
pytest tests/ -v

# 개별 모듈 테스트
python -m odds_collection.odds_api_client
python -m value_betting.value_detector
python -m value_betting.arbitrage_finder
python -m value_betting.kelly_calculator
```

---

## 📖 5단계: API 엔드포인트 탐색

### Value Bet 탐지 (파라미터 조정)

```bash
curl "http://localhost:5001/api/value-bets?min_edge=0.05&min_confidence=0.8&use_demo=true" \
  | python -m json.tool
```

**파라미터:**
- `min_edge`: 최소 Edge (0.05 = 5%)
- `min_confidence`: 최소 신뢰도 (0.8 = 80%)

### Kelly Criterion 계산

```bash
curl -X POST "http://localhost:5001/api/kelly/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "win_probability": 0.60,
    "decimal_odds": 2.00,
    "bankroll": 10000,
    "fraction": 0.25
  }' | python -m json.tool
```

### 특정 경기 분석

```bash
# 먼저 match_id 확인
curl "http://localhost:5001/api/odds/live?use_demo=true" | python -m json.tool

# match_id로 상세 분석
curl "http://localhost:5001/api/odds/analyze/demo_001?use_demo=true" \
  | python -m json.tool
```

---

## 🎯 6단계: 실제 사용 시나리오

### 시나리오 1: Value Bet 찾기

```python
import requests

# 1. Value Bets 조회
response = requests.get('http://localhost:5001/api/value-bets?use_demo=true&min_edge=0.03')
data = response.json()

# 2. 추천 베팅 확인
for bet in data['value_bets']:
    if bet['recommendation'] == 'STRONG BET':
        print(f"🎯 {bet['match']}")
        print(f"   Outcome: {bet['outcome']}")
        print(f"   Odds: {bet['odds']:.2f} @ {bet['bookmaker']}")
        print(f"   Edge: {bet['edge_percent']:.2f}%")
        print(f"   Kelly Stake: {bet['kelly_stake']*100:.2f}%")
        print()
```

### 시나리오 2: 포트폴리오 배분

```python
import requests

# 1. Value Bets 가져오기
value_response = requests.get('http://localhost:5001/api/value-bets?use_demo=true')
value_bets = value_response.json()['value_bets']

# 2. Kelly 포트폴리오 계산
portfolio_response = requests.post(
    'http://localhost:5001/api/kelly/portfolio',
    json={
        'value_bets': value_bets,
        'bankroll': 10000,
        'fraction': 0.25
    }
)

allocation = portfolio_response.json()['allocation']

# 3. 배분 계획 출력
print(f"Total Kelly: {allocation['total_kelly_percent']:.1f}%")
print(f"Total Bet: ${allocation['total_bet_amount']:.2f}")
print(f"Expected Profit: ${allocation['total_expected_profit']:.2f}")
print("\nBet Breakdown:")
for bet in allocation['allocations']:
    print(f"  {bet['match']} ({bet['outcome']})")
    print(f"    Stake: ${bet['bet_amount']:.2f}")
```

---

## 🐛 문제 해결

### API 서버가 시작되지 않음

```bash
# 포트 5001이 사용 중인지 확인
lsof -i :5001

# 사용 중이면 프로세스 종료
kill -9 <PID>

# 또는 다른 포트 사용
python api/app_odds_based.py --port 5002
```

### The Odds API 키 에러

```bash
# 환경 변수 확인
echo $ODDS_API_KEY

# 설정되지 않았으면
export ODDS_API_KEY='your_key'

# 또는 데모 모드 사용
curl "http://localhost:5001/api/odds/live?use_demo=true"
```

### Import 에러

```bash
# PYTHONPATH 설정
export PYTHONPATH=/Users/pukaworks/Desktop/soccer-predictor/backend:$PYTHONPATH

# 또는 가상환경 재생성
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📚 다음 단계

### 학습 리소스

1. **API 문서 읽기**
   ```bash
   curl http://localhost:5001/api/docs | python -m json.tool
   ```

2. **전체 README 읽기**
   ```bash
   cat README_v2.md
   ```

3. **코드 탐색**
   ```bash
   # 핵심 모듈
   backend/odds_collection/odds_api_client.py
   backend/value_betting/value_detector.py
   backend/value_betting/kelly_calculator.py
   ```

### 프론트엔드 개발 (다음 단계)

```bash
cd frontend/epl-predictor

# 의존성 설치
npm install axios recharts

# 개발 서버 실행
npm start
```

---

## ✅ 체크리스트

- [ ] API 서버 실행 성공
- [ ] 데모 데이터로 Value Bets 확인
- [ ] Kelly Criterion 계산 테스트
- [ ] 테스트 실행 (pytest)
- [ ] (선택) The Odds API 키 발급 및 설정
- [ ] (선택) 실제 API로 배당률 조회

---

## 🎉 완료!

이제 배당률 기반 Value Betting 시스템을 사용할 준비가 되었습니다!

**다음 단계:**
- 프론트엔드 개발
- 실시간 모니터링 구현
- 베팅 히스토리 추적

---

**도움이 필요하면:**
- README_v2.md 참고
- `GET /api/docs` 엔드포인트 확인
- 각 모듈의 `if __name__ == '__main__'` 블록 실행해보기
