# Value Betting Module

**배당률 기반 가치 베팅 시스템**

---

## 📚 개요

이 모듈은 북메이커 배당률을 분석하여 Value Bet, Arbitrage, Kelly Criterion 기반 최적 자금 관리를 제공합니다.

### 학술적 근거

- **Constantinou & Fenton (2012)**: 북메이커 배당률이 통계 모델보다 4% 더 정확
- **Kelly (1956)**: 장기적 자금 극대화를 위한 최적 베팅 비율
- **Dixon & Coles (1997)**: 축구 득점 예측 모델 (비교 기준)

---

## 🏗️ 구조

```
value_betting/
├── __init__.py                # 모듈 진입점
├── value_detector.py          # Value Bet 탐지 엔진
├── arbitrage_finder.py        # Arbitrage 기회 탐지
├── kelly_criterion.py         # Kelly Criterion 계산기
├── utils.py                   # 공통 유틸리티
├── exceptions.py              # 커스텀 예외
└── test_integration.py        # 통합 테스트
```

---

## 🚀 Quick Start

### 1. 기본 사용법

```python
from value_betting import ValueDetector, ArbitrageFinder, KellyCriterion

# 1. Value Detector 초기화
detector = ValueDetector(
    min_edge=0.02,          # 최소 2% edge
    min_confidence=0.65     # 최소 65% 신뢰도
)

# 2. 경기 분석
match_analysis = {
    'match_id': 'epl_001',
    'home_team': 'Manchester City',
    'away_team': 'Liverpool',
    'bookmakers_raw': {
        'pinnacle': {'home': 2.00, 'draw': 3.50, 'away': 4.00},
        'bet365': {'home': 2.10, 'draw': 3.40, 'away': 3.90}
    }
}

# 3. Value Bet 탐지
value_bets = detector.detect_value_bets(match_analysis)

for bet in value_bets:
    print(f"{bet['outcome']} @ {bet['bookmaker']}")
    print(f"  Edge: {bet['edge']:.1%}")
    print(f"  Confidence: {bet['confidence']:.1%}")
    print(f"  Recommendation: {bet['recommendation']}")
```

### 2. Arbitrage 탐지

```python
arb_finder = ArbitrageFinder(min_profit=0.005)

arb = arb_finder.check_arbitrage(match_analysis)

if arb:
    print(f"Profit: {arb['profit_margin']:.2%}")
    print(f"Stakes: {arb['stake_distribution']}")
```

### 3. Kelly Criterion

```python
kelly = KellyCriterion(fraction=0.25, max_bet=0.05)

# 단일 베팅
result = kelly.calculate_bet_amount(
    win_probability=0.60,
    decimal_odds=2.00,
    bankroll=10000.0
)

print(f"Bet: ${result['bet_amount']:,.2f}")
print(f"Expected Value: ${result['expected_value']:,.2f}")

# 포트폴리오 배분
portfolio = kelly.calculate_bankroll_allocation(
    value_bets=value_bets,
    bankroll=10000.0
)

print(f"Total Allocated: ${portfolio['total_bet_amount']:,.2f}")
print(f"Expected ROI: {portfolio['expected_roi']:.2f}%")
```

---

## 📖 주요 클래스

### ValueDetector

**목적**: Pinnacle을 기준으로 다른 북메이커의 배당률에서 Value Bet 탐지

**핵심 개념**:
- Pinnacle은 "sharp bookmaker"로 시장 효율성 대표
- Edge = (추정 확률 × 배당률) - 1
- Edge > 임계값이면 Value Bet

**Parameters**:
- `min_edge` (float): 최소 edge (기본: 0.02 = 2%)
- `min_confidence` (float): 최소 신뢰도 (기본: 0.65 = 65%)
- `sharp_bookmaker` (str): 기준 북메이커 (기본: 'pinnacle')

**Methods**:
- `detect_value_bets(match_analysis)`: Value Bet 탐지
- `summarize_value_bets(value_bets)`: 통계 요약

**Return Example**:
```python
{
    'match_id': 'epl_001',
    'outcome': 'home',
    'bookmaker': 'bet365',
    'odds': 2.10,
    'edge': 0.05,  # 5%
    'confidence': 0.75,
    'estimated_probability': 0.524,
    'recommendation': 'MODERATE_BET'  # STRONG_BET, MODERATE_BET, SMALL_BET
}
```

---

### ArbitrageFinder

**목적**: 북메이커 간 배당률 차이로 무위험 차익거래 기회 탐지

**핵심 개념**:
- Arbitrage Percentage = (1/odds_home) + (1/odds_draw) + (1/odds_away)
- < 1.0이면 arbitrage 존재
- 현실적으로 매우 드물고 즉시 사라짐

**Parameters**:
- `min_profit` (float): 최소 수익률 (기본: 0.005 = 0.5%)

**Methods**:
- `check_arbitrage(match_analysis)`: 단일 경기 확인
- `find_arbitrage_opportunities(matches_analysis)`: 여러 경기 탐색
- `calculate_arbitrage_from_raw_odds(bookmakers_odds)`: 원본 데이터에서 계산

**Return Example**:
```python
{
    'arb_percentage': 0.95,
    'profit_margin': 0.05,  # 5% 보장 수익
    'best_odds': {
        'home': {'bookmaker': 'bet365', 'odds': 2.15},
        'draw': {'bookmaker': 'williamhill', 'odds': 3.80},
        'away': {'bookmaker': 'betfair', 'odds': 4.50}
    },
    'stake_distribution': {
        'home': 45.2,
        'draw': 28.1,
        'away': 22.4,
        'guaranteed_profit': 4.3
    },
    'urgency': 'HIGH',  # CRITICAL, HIGH, MEDIUM, LOW
    'risk_level': 'MEDIUM'  # HIGH, MEDIUM, LOW
}
```

---

### KellyCriterion

**목적**: 장기적 자금 극대화를 위한 최적 베팅 금액 계산

**Kelly Formula**:
```
f* = (bp - q) / b

f* = 베팅할 자금 비율
b = 순이익 배당률 (decimal_odds - 1)
p = 승리 확률
q = 패배 확률 (1 - p)
```

**Parameters**:
- `fraction` (float): Kelly 비율
  - 1.0 = Full Kelly (공격적, 변동성 큼)
  - 0.5 = Half Kelly (균형)
  - 0.25 = Quarter Kelly (보수적, **권장**)
- `max_bet` (float): 최대 베팅 비율 (기본: 0.05 = 5%)

**Methods**:
- `calculate_kelly(win_probability, decimal_odds)`: Kelly 비율 계산
- `calculate_bet_amount(win_prob, odds, bankroll)`: 실제 베팅 금액
- `calculate_bankroll_allocation(value_bets, bankroll)`: 포트폴리오 배분
- `simulate_kelly_growth(...)`: 시뮬레이션
- `compare_strategies(...)`: 전략 비교

**Return Example**:
```python
{
    'kelly_percent': 0.05,  # 5% 베팅
    'bet_amount': 500.0,
    'potential_profit': 500.0,
    'potential_loss': 500.0,
    'expected_value': 100.0,
    'bankroll_after_win': 10500.0,
    'bankroll_after_loss': 9500.0
}
```

---

## 🧪 테스트

### 통합 테스트 실행

```bash
cd backend
python value_betting/test_integration.py
```

**예상 결과**:
```
================================================================================
Value Betting Module - Integration Tests
================================================================================

[Test 1] Utility Functions
--------------------------------------------------------------------------------
...
✅ Test 1 PASSED

[Test 2] Value Detector
--------------------------------------------------------------------------------
...
✅ Test 2 PASSED

[Test 3] Arbitrage Finder
--------------------------------------------------------------------------------
...
✅ Test 3 PASSED

[Test 4] Kelly Criterion
--------------------------------------------------------------------------------
...
✅ Test 4 PASSED

[Test 5] End-to-End Workflow Simulation
--------------------------------------------------------------------------------
...
✅ Test 5 PASSED

================================================================================
🎉 ALL TESTS PASSED!
================================================================================
```

---

## 🔧 Flask API 통합

`app_odds_based.py`에서 사용:

```python
from value_betting import ValueDetector, ArbitrageFinder, KellyCriterion

# 초기화
value_detector = ValueDetector(min_edge=0.02, min_confidence=0.65)
arbitrage_finder = ArbitrageFinder(min_profit=0.005)
kelly_calculator = KellyCriterion(fraction=0.25, max_bet=0.05)

# API 엔드포인트에서 사용
@app.route('/api/value-bets', methods=['GET'])
def get_value_bets():
    # 배당률 가져오기
    matches = odds_client.get_epl_odds()
    
    # Value Bet 탐지
    all_value_bets = []
    for match in matches:
        analysis = odds_aggregator.analyze_match_odds(match)
        value_bets = value_detector.detect_value_bets(analysis)
        all_value_bets.extend(value_bets)
    
    # 통계 요약
    summary = value_detector.summarize_value_bets(all_value_bets)
    
    return jsonify({
        'value_bets': all_value_bets,
        'summary': summary
    })
```

---

## 📊 실전 사용 시나리오

### Scenario 1: 주말 EPL 베팅

```python
# 1. 실시간 배당률 수집
from odds_collection import OddsAPIClient, OddsAggregator

odds_client = OddsAPIClient()
odds_aggregator = OddsAggregator()

matches = odds_client.get_epl_odds()

# 2. 모든 경기 분석
analyzed_matches = []
for match in matches:
    analysis = odds_aggregator.analyze_match_odds(match)
    analyzed_matches.append(analysis)

# 3. Value Bet 탐지
all_value_bets = []
for analysis in analyzed_matches:
    vbs = value_detector.detect_value_bets(analysis)
    all_value_bets.extend(vbs)

print(f"Found {len(all_value_bets)} value bets")

# 4. Kelly 포트폴리오 배분
bankroll = 10000.0
portfolio = kelly_calculator.calculate_bankroll_allocation(
    all_value_bets, bankroll
)

print(f"Total Allocation: ${portfolio['total_bet_amount']:,.2f}")
print(f"Expected ROI: {portfolio['expected_roi']:.2f}%")

# 5. 실행
for bet in portfolio['allocations']:
    print(f"\n{bet['home_team']} vs {bet['away_team']}")
    print(f"  {bet['outcome']} @ {bet['bookmaker']} ({bet['odds']:.2f})")
    print(f"  Bet: ${bet['bet_amount']:,.2f}")
    print(f"  Edge: {bet['edge']:.1%}, Confidence: {bet['confidence']:.1%}")
```

---

## ⚠️ 주의사항

### 1. 책임감 있는 베팅
- **도박은 오락이지 투자가 아닙니다**
- 잃어도 괜찮은 금액만 사용
- 감정적 베팅 금지

### 2. 시장 효율성
- 북메이커는 전문가입니다
- Value Bet은 드뭅니다 (주말에 2-3개)
- Arbitrage는 거의 불가능합니다

### 3. 북메이커 리스크
- 베팅 제한 가능
- 계정 폐쇄 위험
- Arbitrage 베터 차단

### 4. 기술적 한계
- API 제한 (무료: 월 500 requests)
- 배당률 변동 (초 단위)
- 실시간 실행 필요

---

## 📚 참고 문헌

1. **Kelly, J. L. (1956)**. "A New Interpretation of Information Rate". *Bell System Technical Journal*, 35(4), 917-926.

2. **Constantinou, A. C., & Fenton, N. E. (2012)**. "Solving the problem of inadequate scoring rules for assessing probabilistic football forecast models". *Journal of Quantitative Analysis in Sports*, 8(1).

3. **Dixon, M. J., & Coles, S. G. (1997)**. "Modelling Association Football Scores and Inefficiencies in the Football Betting Market". *Journal of the Royal Statistical Society*, Series C, 46(2), 265-280.

---

## 🎯 다음 단계

1. ✅ **모듈 구현 완료**
2. ⏳ **Flask API 통합**
3. ⏳ **프론트엔드 대시보드**
4. ⏳ **실시간 데이터 수집**
5. ⏳ **프로덕션 배포**

---

**버전**: 2.0.0  
**최종 업데이트**: 2025-10-06  
**개발자**: AI + Human Collaboration
