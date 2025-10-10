# Market Value 탭 - 긴급 수정 사항

**목적**: Value Betting → 배당률 기반 승부예측 참조 시스템으로 전환

---

## 🚨 즉시 수정 필요 항목

### 1. 용어 변경

**현재 → 수정**:
- "Market Value" → "배당률 기반 예측" 또는 "승부예측 참조"
- "Value Betting 기회" → "배당률 분석"
- "Value Bets" → "경기 분석"
- "Edge" → "확률 편차" 또는 제거
- "Strong Bet" → "유력 예측"
- "Moderate Bet" → "예측"
- "Kelly 베팅 금액 계산" → 제거 또는 "배당률 상세"

### 2. UI 요소 수정

#### 통계 카드
```javascript
// 현재
<StatCard label="Value Bets" value={summary.total_count} />
<StatCard label="평균 Edge" value={`${edge}%`} />

// 수정
<StatCard label="분석 경기" value={matches.length} />
<StatCard label="컨센서스 신뢰도" value={`${confidence}%`} />
```

#### ValueBetCard → MatchPredictionCard
```javascript
// 핵심 변경
- Edge 배지 제거
- 추천 등급 배지 제거
- Kelly 버튼 제거
+ 승률 프로그레스 바 강조
+ "참조용 정보입니다" 표시
```

### 3. 메시지 추가

모든 페이지 상단에:
```
⚠️ 이 정보는 북메이커 배당률 기반 참조 자료입니다.
   배팅을 권유하거나 보장하지 않습니다.
```

---

## 📝 상세 수정 방법

### Step 1: App.js 탭 이름 변경

```javascript
// 수정 전
{ id: 'market-value', label: 'Market Value', icon: '💰' }

// 수정 후
{ id: 'market-value', label: '배당률 분석', icon: '📊' }
```

### Step 2: MarketValueDashboard.js 텍스트 변경

```javascript
// 수정할 텍스트 목록
"Market Value" → "배당률 기반 승부예측"
"Value Betting 기회" → "경기별 예측 분석"
"배당률 기반 가치 베팅 분석" → "북메이커 배당률 기반 승부 참조"
"Value Bets" → "분석 경기"
"평균 Edge" → "평균 확률 편차" (또는 제거)
```

### Step 3: ValueBetCard.js 대폭 수정

**제거할 요소**:
- Edge 배지 (우측 상단)
- 추천 등급 배지 (STRONG_BET 등)
- Kelly 베팅 금액 계산 버튼

**강조할 요소**:
- 추정 확률 (estimated_probability)
- consensus_probability (있는 경우)
- 북메이커 수

**추가할 요소**:
```javascript
<div className="text-xs text-white/40 mt-2">
  ⚠️ 이 정보는 참조용입니다. 배팅을 권유하지 않습니다.
</div>
```

### Step 4: Kelly Modal 제거 또는 변경

**Option A: 완전 제거** (추천)
```javascript
// onCalculateKelly 함수 제거
// Kelly Modal 전체 제거
```

**Option B: "배당률 상세" 모달로 변경**
```javascript
// Kelly 계산 대신
// - 북메이커별 확률 분포
// - 시간에 따른 배당률 변화 (있으면)
// - 통계적 신뢰도
```

---

## 🎨 새로운 MatchPredictionCard 디자인

```javascript
<div className="prediction-card">
  {/* 헤더 */}
  <div className="header">
    <h3>Manchester City vs Liverpool</h3>
    <span className="time">Oct 5, 15:00</span>
  </div>
  
  {/* 승부예측 (3개 결과) */}
  <div className="predictions">
    {/* 홈 승 */}
    <div className="outcome home">
      <div className="label">🏠 홈 승 (Man City)</div>
      <div className="probability">52.4%</div>
      <ProgressBar value={52.4} color="blue" />
      <div className="odds">평균 배당: 1.91</div>
    </div>
    
    {/* 무승부 */}
    <div className="outcome draw">
      <div className="label">⚖️ 무승부</div>
      <div className="probability">28.6%</div>
      <ProgressBar value={28.6} color="gray" />
      <div className="odds">평균 배당: 3.50</div>
    </div>
    
    {/* 원정 승 */}
    <div className="outcome away">
      <div className="label">✈️ 원정 승 (Liverpool)</div>
      <div className="probability">19.0%</div>
      <ProgressBar value={19.0} color="red" />
      <div className="odds">평균 배당: 5.26</div>
    </div>
  </div>
  
  {/* 북메이커 컨센서스 */}
  <div className="consensus">
    <div className="icon">🎯</div>
    <div className="text">
      <div>북메이커 합의: 홈 승 유력</div>
      <div className="confidence">신뢰도: 높음 (편차 2.1%)</div>
    </div>
  </div>
  
  {/* 면책 */}
  <div className="disclaimer">
    ⚠️ 북메이커 배당률 기반 참조 정보입니다.
  </div>
</div>
```

---

## 🔄 데이터 흐름 변경

### 현재 (Value Betting)
```
Pinnacle (기준) → Edge 계산 → Value Bet 탐지 → 베팅 추천
```

### 수정 후 (승부예측)
```
모든 북메이커 → Consensus 계산 → 확률 추정 → 승부예측 제시
```

### 필요한 데이터

프론트엔드에서 표시할 데이터:
```javascript
{
  match_id: 'abc123',
  home_team: 'Manchester City',
  away_team: 'Liverpool',
  commence_time: '2025-10-05T15:00:00Z',
  
  // ✅ 핵심: 컨센서스 확률
  consensus_probability: {
    home: 0.524,   // 52.4%
    draw: 0.286,   // 28.6%
    away: 0.190    // 19.0%
  },
  
  // ✅ 평균 배당률
  average_odds: {
    home: 1.91,
    draw: 3.50,
    away: 5.26
  },
  
  // ✅ 북메이커별 배당률 (기존 유지)
  bookmakers_raw: {
    'pinnacle': { home: 2.00, draw: 3.50, away: 4.00 },
    'bet365': { home: 2.10, draw: 3.40, away: 3.90 },
    // ...
  },
  
  // ✅ 신뢰도 지표
  confidence_metrics: {
    bookmaker_count: 8,
    std_deviation: 0.021,  // 2.1%
    confidence_level: 'high'  // 'low', 'medium', 'high'
  }
}
```

---

## 📋 수정 체크리스트

### Phase 1: 긴급 수정 (1-2시간)

- [ ] App.js: 탭 이름 "Market Value" → "배당률 분석"
- [ ] MarketValueDashboard.js: 모든 "Value Bet" → "경기 분석"
- [ ] ValueBetCard.js: Edge 배지 제거
- [ ] ValueBetCard.js: Kelly 버튼 제거
- [ ] 모든 컴포넌트: 면책 문구 추가
- [ ] 통계 카드: "평균 Edge" 제거

### Phase 2: 구조 개선 (3-4시간)

- [ ] MatchPredictionCard.js 새로 작성
- [ ] 3개 결과 (홈/무/원정) 모두 표시
- [ ] 프로그레스 바로 확률 시각화
- [ ] 북메이커 컨센서스 표시
- [ ] 신뢰도 지표 추가

### Phase 3: 완전 재구성 (1-2일)

- [ ] 백엔드 API 엔드포인트 추가 (/api/match-predictions)
- [ ] 배당률 히스토리 추적
- [ ] 차트로 시각화 (Recharts)
- [ ] 모바일 최적화

---

## ⚠️ 주의사항

### 법적 면책

반드시 다음 문구를 여러 곳에 표시:

```
⚠️ 이 정보는 북메이커 배당률을 기반으로 한 참조 자료입니다.
   승부 결과를 보장하거나 배팅을 권유하지 않습니다.
   
⚠️ 도박은 중독성이 있으며 재정적 손실을 초래할 수 있습니다.
   책임감 있게 즐기시기 바랍니다.
```

### 용어 사용 금지

❌ 사용하지 말 것:
- "베팅하세요"
- "수익 보장"
- "확실한 예측"
- "이길 확률 높음"
- "추천 베팅"

✅ 사용 가능:
- "배당률 분석"
- "참조 정보"
- "북메이커 컨센서스"
- "확률 추정"
- "예측 참고"

---

## 🎯 최종 목표

**Before**:
```
"Manchester City 홈 승에 베팅하세요!
Edge 5.2%로 Strong Bet입니다.
Kelly Criterion으로 $625 추천"
```

**After**:
```
"Manchester City vs Liverpool
배당률 기반 예측:
- 홈 승: 52.4% (Man City 유력)
- 무승부: 28.6%
- 원정 승: 19.0%

북메이커 8개 합의 (신뢰도: 높음)
⚠️ 참조용 정보입니다"
```

---

## 📞 구현 지원

수정 작업을 도와드릴까요?

1. **긴급 패치 (1-2시간)**: 텍스트만 변경
2. **중간 수정 (3-4시간)**: 컴포넌트 구조 개선
3. **완전 재구성 (1-2일)**: 새로운 UI 전면 개발

어떤 옵션을 선택하시겠습니까?
