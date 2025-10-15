# EPL Match Predictor v2.0 🎯⚽

**개인 선수 분석 기반 AI 경기 예측 플랫폼**

> v1.0: 통계 기반 예측 모델
> **v2.0**: 선수 능력치 기반 가상 시뮬레이션 플랫폼

---

## 🌟 서비스 개요

EPL Match Predictor v2.0은 **개인 선수 분석을 통한 가상 시뮬레이션**으로 경기 결과를 예측하는 AI 분석 플랫폼입니다.

### 핵심 가치

- 📊 **선수 중심 분석**: 팀 통계가 아닌 개별 선수 능력치 평가
- 🎮 **가상 시뮬레이션**: 실제 스쿼드 구성 기반 경기 시뮬레이션
- 🧠 **AI 기반 예측**: 선수 데이터 통합 및 머신러닝 예측
- 🎨 **직관적 UX**: 보라색 테마의 프리미엄 인터페이스

---

## 🚀 빠른 시작

### 신규 설치 (새로운 PC)

```bash
# 1. GitHub에서 클론
git clone https://github.com/stleeqwe/EPL-Match-Predictor.git
cd EPL-Match-Predictor

# 2. 원클릭 자동 설정
./scripts/setup/setup.sh

# 3. 환경 변수 설정
# backend/.env 파일에 API 키 입력

# 4. 앱 시작
./scripts/setup/start.sh
```

브라우저가 자동으로 `http://localhost:3000`을 엽니다.

> 📚 **상세 가이드**: [docs/development/SETUP_GUIDE.md](docs/development/SETUP_GUIDE.md) 참조

### 기존 환경에서 실행

```bash
# Backend + Frontend 동시 실행
./scripts/setup/start.sh
```

**개별 실행**:
```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
python api/app.py

# Terminal 2: Frontend
cd frontend
npm start
```

---

## 🎯 주요 기능 (v2.0)

### 1️⃣ 선수 능력치 평가 시스템

**포지션별 세분화 평가**
- GK (골키퍼): 8개 항목 (반응속도, 포지셔닝, 핸들링 등)
- DF (수비수): CB, FB 세부 포지션 10개 항목
- MF (미드필더): DM, CM, CAM 세부 포지션 11개 항목
- FW (공격수): WG, ST 세부 포지션 9-12개 항목

**가중치 기반 평가**
- 각 능력치 항목에 포지션별 중요도 가중치 적용
- 0.0-5.0 점수 시스템 (0.25 단위)
- 실시간 가중 평균 계산

**시각적 피드백**
- 색상 등급 시스템:
  - 🟢 4.5-5.0: 월드클래스 (밝은 녹색)
  - 🔷 4.0-4.5: 최상위 (청록색)
  - 🔵 3.0-4.0: 상위권 (파란색)
  - 🟡 2.0-3.0: 평균 (노란색)
  - 🔴 <2.0: 평균 이하 (빨간색)

### 2️⃣ 팀 분석 시스템

**스쿼드 빌더**
- 4-3-3, 4-4-2 등 포메이션 선택
- 드래그 앤 드롭 선수 배치
- 주전/후보 구분
- 팀 평균 능력치 자동 계산

**전력 분석**
- 포지션별 평균 능력치
- 라인별 (수비/미드필드/공격) 전력 분석
- 팀 종합 전력 점수

### 3️⃣ 경기 예측 시뮬레이션

**시뮬레이션 기반 예측**
- 양 팀 스쿼드 능력치 비교
- 포지션 매치업 분석
- 홈/원정 어드밴티지 적용
- 확률 기반 승/무/패 예측

**결과 시각화**
- 실시간 확률 업데이트
- 예상 스코어 분포
- 핵심 지표 비교

---

## 📊 API 엔드포인트 (v2.0)

### 선수 데이터

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/teams` | 전체 팀 목록 |
| GET | `/api/squad/<team>` | 팀별 선수 명단 |
| GET | `/api/player/<player_id>` | 선수 상세 정보 |
| POST | `/api/player/<player_id>/ratings` | 선수 능력치 저장 |

### 팀 분석

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/team-strength/<team>` | 팀 전력 분석 |
| GET | `/api/formation/<team>` | 포메이션 정보 |

### 경기 예측

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/api/fixtures` | 경기 일정 |
| POST | `/api/simulate` | 경기 시뮬레이션 |

### 예측 API 예시 (v2.0)

```bash
curl -X POST http://localhost:5001/api/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "home_team": "Manchester City",
    "away_team": "Liverpool",
    "home_formation": "4-3-3",
    "away_formation": "4-3-3"
  }'
```

응답:
```json
{
  "home_win": 58.5,
  "draw": 23.2,
  "away_win": 18.3,
  "home_strength": 4.32,
  "away_strength": 4.18,
  "key_matchups": [
    {
      "position": "ST",
      "home_player": "Erling Haaland",
      "home_rating": 4.8,
      "away_player": "Darwin Núñez",
      "away_rating": 4.2
    }
  ],
  "predicted_score": "2-1"
}
```

---

## 🎨 UI/UX 특징 (v2.0)

### 디자인 시스템

**색상 팔레트**
- Primary: 보라색 계열 (#8B2BE2, #9F7AEA)
- Accent: 형광 녹색 (#00FF7F)
- Background: 다크 퍼플 그라데이션

**컴포넌트**
- 글래스모피즘 카드
- Framer Motion 애니메이션
- 반응형 그리드 레이아웃
- 커스텀 슬라이더 (WCAG AA 준수)

### 주요 화면

1. **선수 평가 화면**
   - 선수 카드 그리드/리스트 뷰
   - 필터 및 정렬 기능
   - 실시간 능력치 입력

2. **팀 분석 화면**
   - 스쿼드 빌더 (드래그 앤 드롭)
   - 팀 전력 분석 차트
   - 포지션별 통계

3. **경기 시뮬레이션 화면**
   - 팀 선택 및 포메이션 설정
   - 실시간 확률 계산
   - 결과 시각화

---

## 🏗️ 프로젝트 구조 (v2.0)

```
EPL-Match-Predictor/
├── docs/                          # 📚 프로젝트 문서
│   ├── architecture/              # 아키텍처 설계 문서
│   ├── deployment/                # 배포 가이드
│   ├── development/               # 개발 가이드
│   ├── features/                  # 기능별 문서
│   │   ├── simulation/
│   │   ├── agent-system/
│   │   ├── market-value/
│   │   └── bayesian/
│   ├── phases/                    # 단계별 완료 보고서
│   └── testing/                   # 테스트 문서
│
├── scripts/                       # 🔧 유틸리티 스크립트
│   ├── diagnostics/               # 진단 스크립트
│   ├── setup/                     # 설치/시작 스크립트
│   ├── testing/                   # 테스트 스크립트
│   └── analysis/                  # 분석 스크립트
│
├── backend/                       # ⚙️ Backend API
│   ├── api/                       # Flask REST API
│   │   ├── app.py                 # 메인 API 서버
│   │   └── v1/                    # API v1 엔드포인트
│   ├── services/                  # 비즈니스 로직
│   ├── simulation/                # 경기 시뮬레이션 엔진
│   │   ├── v2/                    # 최신 시뮬레이션 엔진
│   │   └── legacy/                # 레거시 엔진
│   ├── ai/                        # AI 분석 모듈
│   ├── tactics/                   # 전술 분석
│   ├── value_betting/             # Value Betting 모듈
│   ├── docs/                      # Backend 문서
│   ├── scripts/                   # Backend 스크립트
│   └── tests/                     # Backend 테스트
│
├── frontend/                      # 🎨 React Frontend
│   ├── src/                       # 소스 코드
│   │   ├── components/
│   │   │   ├── PlayerCard.js
│   │   │   ├── PlayerRatingManager.js
│   │   │   ├── SquadBuilder.js
│   │   │   ├── MatchSimulator.js
│   │   │   └── Leaderboard.js
│   │   ├── contexts/              # React Contexts
│   │   ├── services/              # API 클라이언트
│   │   └── utils/                 # 유틸리티 함수
│   ├── public/                    # 정적 파일
│   ├── docs/                      # Frontend 문서
│   └── package.json
│
├── data/                          # 데이터 파일
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🔧 기술 스택 (v2.0)

### Backend
- **Python 3.9+**
- **Flask 2.3**: REST API
- **LocalStorage**: 선수 평가 데이터 저장
- NumPy, Pandas: 데이터 처리

### Frontend
- **React 18.3**: UI 프레임워크
- **Framer Motion**: 애니메이션
- **Tailwind CSS**: 스타일링
- **Lucide React**: 아이콘
- **Axios**: HTTP 클라이언트

### 데이터 소스
- **Fantasy Premier League API**: 선수 데이터 및 사진
- **Custom Database**: 선수별 능력치 평가 데이터

---

## 📈 v2.0 업데이트 내역

### ✨ 신규 기능

1. **선수 능력치 평가 시스템**
   - 포지션별 세부화 (8가지 세부 포지션)
   - 가중치 기반 평가 (항목당 2-17%)
   - 코멘트 입력 (500자)

2. **스쿼드 빌더**
   - 4-3-3, 4-4-2, 3-4-3 포메이션
   - 드래그 앤 드롭 UI
   - 자동 포지션 검증

3. **팀 전력 분석**
   - 라인별 평균 능력치
   - 주전/후보 구분
   - 시각적 차트

4. **경기 시뮬레이션**
   - 선수 능력치 기반 예측
   - 포지션 매치업 분석
   - 확률 분포 시각화

### 🎨 UI/UX 개선

1. **색상 시스템 표준화**
   - WCAG AA 접근성 기준 준수
   - 통일된 5단계 등급 색상
   - 보라색 배경 최적화

2. **컴포넌트 개선**
   - 글래스모피즘 카드
   - 매끄러운 애니메이션
   - 반응형 레이아웃

3. **사용성 향상**
   - 직관적인 슬라이더
   - 실시간 피드백
   - 명확한 시각적 위계

### 🔄 변경 사항

- **v1.0**: 통계 기반 Dixon-Coles 모델
- **v2.0**: 선수 능력치 기반 시뮬레이션

---

## 🎯 향후 계획

### Phase 1: 데이터 확장 (Q1 2025)
- [ ] 전체 EPL 20팀 선수 데이터 구축
- [ ] 실시간 FPL 데이터 동기화
- [ ] 부상/출전 정보 통합

### Phase 2: 시뮬레이션 고도화 (Q2 2025)
- [ ] 경기 흐름 시뮬레이션
- [ ] 교체 선수 전략 분석
- [ ] 전술 변화 시뮬레이션

### Phase 3: AI 모델 통합 (Q3 2025)
- [ ] Neural Network 기반 예측
- [ ] 과거 데이터 학습
- [ ] 예측 정확도 검증

### Phase 4: 서비스 확장 (Q4 2025)
- [ ] 다른 리그 지원 (La Liga, Serie A 등)
- [ ] 모바일 앱 출시
- [ ] 커뮤니티 기능

---

## 📝 버전 히스토리

| 버전 | 날짜 | 주요 변경사항 |
|------|------|--------------|
| **v2.0** | 2025-01-06 | 선수 분석 기반 시뮬레이션 플랫폼으로 전환 |
| v1.5 | 2024-12-15 | 개인 분석 기능 추가 |
| v1.0 | 2024-10-01 | Dixon-Coles 통계 모델 기반 첫 출시 |

---

## 💰 Value Betting 모듈 (NEW)

### 🎯 개요

프로젝트에 **배당률 기반 Value Betting 시스템**이 추가되었습니다!

**학술적 근거**:
- Constantinou & Fenton (2012): 북메이커 배당률이 통계 모델보다 4% 더 정확
- Kelly (1956): 최적 자금 관리 공식
- Dixon & Coles (1997): 축구 예측 모델 (비교 기준)

### 📦 주요 모듈

```
backend/value_betting/
├── value_detector.py      # Value Bet 탐지 엔진
├── arbitrage_finder.py    # Arbitrage 기회 탐지
├── kelly_criterion.py     # Kelly Criterion 계산기
└── utils.py               # 유틸리티 함수
```

### 🚀 Quick Start

```python
from value_betting import ValueDetector, KellyCriterion

# Value Bet 탐지
detector = ValueDetector(min_edge=0.02)
value_bets = detector.detect_value_bets(match_analysis)

# Kelly Criterion 자금 관리
kelly = KellyCriterion(fraction=0.25)
portfolio = kelly.calculate_bankroll_allocation(value_bets, 10000)

print(f"Total Bets: {portfolio['total_bets']}")
print(f"Expected ROI: {portfolio['expected_roi']:.2f}%")
```

### 🧪 테스트

```bash
cd backend
python value_betting/test_integration.py
```

**결과**:
```
🎉 ALL TESTS PASSED!
  ✅ Utility functions working correctly
  ✅ Value Detector finding opportunities
  ✅ Arbitrage Finder detecting arbitrage
  ✅ Kelly Criterion calculating optimal bets
  ✅ End-to-end workflow validated
```

### 📚 문서

- **README**: `backend/value_betting/README.md`
- **구현 보고서**: `backend/value_betting/IMPLEMENTATION_REPORT.md`
- **API 가이드**: `backend/api/app_odds_based.py`

### ⚠️ 주의사항

**도박은 오락이지 투자가 아닙니다**
- 잃어도 괜찮은 금액만 사용
- Value Bet은 드뭅니다 (주말에 2-3개)
- 북메이커가 계정을 제한할 수 있습니다

---

## 👥 기여자

**프로젝트 관리**: Puka
**버전**: v2.0
**마지막 업데이트**: 2025-01-06

---

## 📄 라이선스

MIT License

---

## 🙏 감사의 말

- **Fantasy Premier League**: 선수 데이터 및 이미지 제공
- **Lucide Icons**: 오픈소스 아이콘 라이브러리
- **Tailwind CSS**: UI 프레임워크

---

**참고**: v2.0은 개인 분석 기반 시뮬레이션 플랫폼입니다. 실제 베팅에 사용하지 마세요. 교육 및 엔터테인먼트 목적으로만 사용해주세요.
