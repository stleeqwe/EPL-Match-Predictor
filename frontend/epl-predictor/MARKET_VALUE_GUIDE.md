# Market Value 탭 - 사용 가이드

**배당률 기반 Value Betting 대시보드**

---

## 🎯 개요

**Market Value** 탭은 북메이커 배당률을 분석하여 가치 있는 베팅 기회를 탐지하고 최적의 베팅 금액을 계산하는 대시보드입니다.

### 주요 기능

1. ✅ **실시간 배당률 수집** (The Odds API)
2. ✅ **Value Bet 자동 탐지** (Pinnacle 기준)
3. ✅ **Kelly Criterion 계산기** (최적 자금 관리)
4. ✅ **북메이커별 배당률 비교**
5. ✅ **배당률 미오픈 시 안내 메시지**

---

## 🚀 사용 방법

### 1. 백엔드 서버 실행

```bash
cd backend
python api/app_odds_based.py
```

서버가 `http://localhost:5001`에서 실행됩니다.

### 2. 프론트엔드 실행

```bash
cd frontend/epl-predictor
npm start
```

브라우저가 자동으로 `http://localhost:3000`을 엽니다.

### 3. Market Value 탭 접속

상단 네비게이션에서 **💰 Market Value** 탭을 클릭합니다.

---

## 📊 화면 구성

### 1. 통계 카드 (상단)

4개의 핵심 지표를 한눈에 확인:

- **분석된 경기**: 현재 배당률이 오픈된 EPL 경기 수
- **Value Bets**: 발견된 가치 베팅 기회 수
- **평균 Edge**: Value Bet의 평균 우위 (%)
- **평균 신뢰도**: Value Bet의 평균 신뢰도 (%)

### 2. Value Betting 기회 섹션

각 Value Bet 카드는 다음 정보를 표시:

- **경기 정보**: 홈팀 vs 원정팀, 경기 시간
- **추천 등급**: STRONG_BET 🔥, MODERATE_BET ⚡, SMALL_BET 💡
- **Edge**: 예상 이익률 (%)
- **베팅 결과**: 홈 승/무승부/원정 승
- **배당률**: 북메이커 제공 배당률
- **신뢰도**: AI가 계산한 신뢰도 (%)
- **추정 확률**: Pinnacle 기준 진짜 확률 (%)
- **북메이커**: 최고 배당률 제공 업체

### 3. Kelly Calculator (버튼 클릭)

각 Value Bet 카드의 **Kelly 베팅 금액 계산** 버튼을 클릭하면:

1. 총 자금(Bankroll) 입력
2. 추천 베팅 금액 자동 계산 (Quarter Kelly)
3. 예상 수익/손실 시뮬레이션
4. 기댓값(EV) 표시

### 4. 경기별 배당률 비교 섹션

모든 경기의 북메이커별 배당률을 비교:

- **Pinnacle**: Sharp Bookmaker (기준점)
- **최고 배당률**: 👑 표시
- **Consensus 확률**: 모든 북메이커 평균 확률

---

## 🎓 개념 설명

### Value Bet이란?

**정의**: 북메이커가 제시한 배당률이 실제 확률보다 높은 경우

**예시**:
```
Pinnacle 배당률: 2.00 (추정 확률: 50%)
Bet365 배당률: 2.10 (암시 확률: 47.6%)

Edge = (50% × 2.10) - 1 = 5%
→ 5% Value Bet!
```

### Kelly Criterion이란?

**정의**: 장기적으로 자금을 극대화하는 최적 베팅 비율

**공식**:
```
Kelly % = (확률 × 배당률 - 1) / (배당률 - 1)
```

**Quarter Kelly**: 안정성을 위해 Full Kelly의 25%만 사용 (권장)

### Edge란?

**정의**: 예상 이익률

**계산**:
```
Edge = (추정 확률 × 배당률) - 1
```

**해석**:
- Edge > 0: 가치 있는 베팅
- Edge = 0: 공정한 배당률
- Edge < 0: 불리한 베팅

---

## ⚠️ 배당률 미오픈 안내

### 표시 조건

다음 경우에 안내 메시지가 표시됩니다:

1. API에서 경기 데이터가 없는 경우
2. 배당률이 아직 오픈되지 않은 경우
3. The Odds API 할당량 초과

### 안내 메시지 내용

```
🟡 배당률 미오픈

다가오는 EPL 경기의 배당률이 아직 오픈되지 않았습니다.

배당률은 일반적으로 경기 시작 1-2일 전에 오픈됩니다.
다음 게임위크가 가까워지면 다시 확인해주세요.

[🔄 새로고침]
```

### 데모 모드 안내

API 키가 없는 경우 데모 데이터로 작동:

```
✨ 데모 모드 안내

현재 데모 모드로 실행 중입니다. 
실제 배당률을 받아오려면 The Odds API 키가 필요합니다.

The Odds API 키 발급받기 →
```

---

## 🔑 The Odds API 설정

### 1. API 키 발급

1. https://the-odds-api.com/ 방문
2. 무료 회원가입
3. API 키 복사

**무료 티어**:
- 월 500 requests
- 실시간 배당률
- 주요 북메이커 데이터

### 2. 환경 변수 설정

```bash
# backend/.env
ODDS_API_KEY=your_api_key_here
```

### 3. 실제 데이터 사용

프론트엔드에서 `useDemo` 파라미터를 `false`로 변경:

```javascript
// marketValueAPI.js
const data = await marketValueAPI.getDashboardData(false); // 실제 API 호출
```

---

## 📈 사용 시나리오

### Scenario 1: 주말 EPL 베팅

**금요일 저녁**:
1. Market Value 탭 접속
2. Value Bets 섹션 확인
3. STRONG_BET 또는 MODERATE_BET 찾기
4. Kelly Calculator로 베팅 금액 계산

**예시**:
```
경기: Manchester City vs Liverpool
결과: 홈 승
북메이커: Bet365
배당률: 2.10
Edge: 5.2%
신뢰도: 73%
추천: MODERATE_BET

총 자금: $10,000
추천 베팅 금액: $625 (6.25% - Quarter Kelly)
예상 수익: $688
기댓값: $72
```

### Scenario 2: 배당률 비교

**토요일 오전**:
1. 경기별 배당률 비교 섹션 확인
2. Pinnacle vs 다른 북메이커 비교
3. 최고 배당률(👑) 찾기
4. Value 있는지 판단

---

## 🎨 UI/UX 특징

### 색상 코드

**추천 등급**:
- 🔥 **STRONG_BET**: 녹색 (Edge ≥ 5%, 신뢰도 ≥ 75%)
- ⚡ **MODERATE_BET**: 파란색 (Edge ≥ 3%, 신뢰도 ≥ 65%)
- 💡 **SMALL_BET**: 노란색 (Edge ≥ 2%, 신뢰도 ≥ 65%)

**북메이커**:
- 🛡️ **Pinnacle**: 보라색 하이라이트 (Sharp Bookmaker)
- 👑 **최고 배당률**: 노란색 강조

### 애니메이션

- 카드 fade-in (staggered)
- 프로그레스 바 애니메이션
- 호버 효과 (scale + glow)
- 모달 부드러운 전환

---

## 🛠️ 문제 해결

### Q: Value Bet이 안 보여요

**A**: 다음을 확인하세요:
1. 백엔드 서버가 실행 중인지 (`http://localhost:5001/api/health`)
2. 배당률이 오픈된 경기가 있는지 (경기 1-2일 전)
3. `min_edge`와 `min_confidence` 설정이 너무 높지 않은지

### Q: 배당률이 업데이트 안 돼요

**A**: 새로고침 버튼 클릭:
- 우측 상단 🔄 버튼
- 또는 브라우저 새로고침 (F5)

### Q: Kelly 계산 결과가 이상해요

**A**: 다음을 확인하세요:
1. Bankroll이 올바르게 입력되었는지
2. 추정 확률이 합리적인지 (40-60% 범위)
3. Quarter Kelly를 사용 중인지 (안전)

### Q: 데모 모드를 끄고 싶어요

**A**: 
1. The Odds API 키 발급
2. `.env` 파일에 `ODDS_API_KEY` 설정
3. 프론트엔드 코드에서 `use_demo: false` 변경

---

## ⚠️ 주의사항

### 1. 책임감 있는 베팅

**도박은 오락이지 투자가 아닙니다**

- 잃어도 괜찮은 금액만 사용
- 감정적 베팅 금지
- 중독 징후 인지 시 전문가 상담

### 2. 시장 효율성

- Value Bet은 **드뭅니다** (주말에 2-3개)
- 북메이커가 틀릴 확률은 낮음
- Edge가 크다고 무조건 이기는 것은 아님

### 3. 북메이커 리스크

- 베팅 제한 가능
- 계정 폐쇄 위험
- Value Betting은 환영받지 않음

### 4. 기술적 한계

- API 할당량 제한 (무료: 월 500 requests)
- 배당률 변동 (초 단위)
- 실시간 실행 필요

---

## 📚 참고 자료

### 학술 논문

1. **Constantinou & Fenton (2012)**  
   "Determining the level of ability of football teams by dynamic ratings"  
   → 북메이커 배당률 > 통계 모델

2. **Kelly (1956)**  
   "A New Interpretation of Information Rate"  
   → 최적 자금 관리 공식

3. **Dixon & Coles (1997)**  
   "Modelling Association Football Scores"  
   → 축구 예측 모델 (비교 기준)

### 웹사이트

- The Odds API: https://the-odds-api.com/
- Pinnacle: https://www.pinnacle.com/
- 프로젝트 GitHub: (your repo)

---

## 🎯 요약

**Market Value 탭은**:

✅ 북메이커 배당률을 분석하여 Value Bet 자동 탐지  
✅ Kelly Criterion으로 최적 베팅 금액 계산  
✅ 배당률 미오픈 시 친절한 안내 메시지  
✅ 프리미엄 UI/UX (보라색 테마)  
✅ 학술적으로 검증된 알고리즘

**사용 시 주의**:

⚠️ 책임감 있게 베팅  
⚠️ Value Bet은 드뭄 (기대치 조절)  
⚠️ 장기적 관점 필요  
⚠️ 도박 중독 주의

---

**버전**: 2.0.0  
**최종 업데이트**: 2025-10-06  
**문의**: 프로젝트 GitHub Issues

💰 **Good luck and bet smart!**
