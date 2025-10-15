# EPL 팀 분석 전문 플랫폼 전환 계획서

## 📋 개요

**현재 시스템**: 통계 모델 기반 경기 예측 시스템
**목표 시스템**: EPL 팀 선수 능력치 전문 분석 플랫폼

### 핵심 변경사항
- ❌ 제거: Dixon-Coles, Bayesian, XGBoost 등 모든 통계 모델
- ❌ 제거: 경기 예측, 확률 계산, 스코어 예측
- ✅ 유지: PlayerRatingManager 기반 개인 분석
- ✅ 강화: 선수 데이터 스크래핑 및 능력치 평가 시스템

---

## 🎯 새로운 시스템 목표

### 핵심 기능
1. **EPL 20개 팀 선수 명단 자동 스크래핑**
2. **포지션별 세부 능력치 평가 시스템**
   - 평가 범위: -5.0 ~ +5.0 (0.25 단위)
   - 포지션별 맞춤 능력치 항목
3. **팀별 선수 관리 및 분석**
4. **능력치 데이터 저장/불러오기/내보내기**

---

## 📊 현재 시스템 분석

### 제거 대상 (Backend)

#### 1. 통계 모델 파일 (9개)
```
backend/models/
├── dixon_coles.py                    # Dixon-Coles 모델
├── bayesian_dixon_coles.py           # Bayesian 버전
├── bayesian_dixon_coles_simplified.py
├── bayesian_diagnostics.py
├── xgboost_model.py                  # XGBoost 모델
├── xgboost_model.pkl                 # 학습된 모델 (2.1MB)
├── catboost_model.py                 # CatBoost 모델
├── ensemble.py                       # 앙상블 모델
└── train_pipeline.py                 # 학습 파이프라인
```

#### 2. 예측 관련 파일 (2개)
```
backend/models/
├── hybrid_predictor.py               # 하이브리드 예측기
└── personal_predictor.py             # 개인 분석 예측기
```

#### 3. 통계 기능 파일
```
backend/features/
└── expected_threat.py                # xT (Expected Threat) 계산

backend/value_betting/                # 배팅 관련 전체 디렉토리
├── value_detector.py
├── kelly_calculator.py
└── arbitrage_finder.py
```

#### 4. 데이터 수집 (일부)
```
backend/data_collection/
├── understat_scraper.py              # 통계 데이터 스크래퍼 (삭제)
└── production_data_pipeline.py       # 통계 파이프라인 (삭제)
```

#### 5. API 엔드포인트
```
backend/api/app.py
- /api/predict                        # 경기 예측 (삭제)
- /api/predictions/history            # 예측 히스토리 (삭제)
- /api/evaluate/model                 # 모델 평가 (삭제)
- /api/xT/heatmap                     # xT 히트맵 (삭제)
- /api/ensemble/predict               # 앙상블 예측 (삭제)
```

#### 6. 테스트 파일
```
backend/tests/
├── test_dixon_coles.py               # 모델 테스트 (삭제)
├── test_value_detector.py            # 배팅 테스트 (삭제)
└── test_odds_api_client.py           # 배당률 테스트 (삭제)
```

### 제거 대상 (Frontend)

#### 1. 통계 분석 컴포넌트 (8개)
```
frontend/epl-predictor/src/components/
├── PredictionResult.js               # 예측 결과 표시
├── PredictionLoadingState.js         # 로딩 상태
├── StatsChart.js                     # 통계 차트
├── TopScores.js                      # 예상 스코어
├── ModelContribution.js              # 모델 기여도
├── WeightEditor.js                   # 가중치 편집기
├── EvaluationDashboard.js            # 평가 대시보드
├── EnsemblePredictor.js              # 앙상블 예측기
└── ExpectedThreatVisualizer.js       # xT 시각화
```

#### 2. 경기 관련 컴포넌트 (1개)
```
frontend/epl-predictor/src/components/
└── MatchSelector.js                  # 경기 선택기 (삭제 또는 단순화)
```

#### 3. App.js 수정 사항
```javascript
- activeTab: 'statistical', 'hybrid' 모드 제거
- 경기 예측 관련 state 제거
- 가중치 관련 state 제거
- fetchPrediction() 함수 제거
```

### 유지 대상 (핵심 자산)

#### Backend
```
backend/data/
└── squad_data.py                     # ✅ 3,499줄 선수 데이터 (확장 필요)

backend/api/app.py                    # ✅ 유지 엔드포인트:
- /api/teams                          # 팀 목록
- /api/squad/{team}                   # 팀별 선수 명단
- /api/player/{player_id}             # 선수 상세 정보

backend/data_collection/
└── fbref_scraper.py                  # ✅ 부분 유지 (선수 데이터 스크래핑)
```

#### Frontend
```
frontend/epl-predictor/src/components/
└── PlayerRatingManager.js            # ✅ 핵심 컴포넌트 (대폭 확장)

frontend/epl-predictor/src/components/
├── Header.js                         # ✅ 유지
├── TabButton.js                      # ✅ 유지 (용도 변경)
└── Accordion.js                      # ✅ 유지
```

---

## 🏗️ 새로운 시스템 아키텍처

### Backend 구조

```
backend/
├── api/
│   └── app.py                        # 간소화된 API 서버
│
├── data/
│   └── squad_data.py                 # 확장된 선수 데이터
│
├── data_collection/
│   ├── squad_scraper.py              # 새로 작성: 선수 명단 스크래퍼
│   └── player_stats_scraper.py       # 새로 작성: 선수 상세 정보
│
├── database/
│   ├── schema.py                     # 수정: 선수/능력치 스키마
│   └── player_db.py                  # 새로 작성: 선수 DB 관리
│
├── services/
│   ├── rating_service.py             # 새로 작성: 능력치 서비스
│   └── team_service.py               # 새로 작성: 팀 관리 서비스
│
└── tests/
    └── test_api.py                   # 수정: API 테스트
```

### Frontend 구조

```
frontend/epl-predictor/src/
├── App.js                            # 대폭 간소화
│
├── components/
│   ├── Header.js                     # 유지
│   ├── TeamSelector.js               # 새로 작성: 팀 선택
│   ├── PlayerList.js                 # 새로 작성: 선수 목록
│   ├── PlayerCard.js                 # 새로 작성: 선수 카드
│   ├── RatingEditor.js               # 새로 작성: 능력치 편집
│   ├── RatingSlider.js               # 새로 작성: 능력치 슬라이더
│   ├── PositionFilter.js             # 새로 작성: 포지션 필터
│   └── TeamAnalytics.js              # 새로 작성: 팀 분석 대시보드
│
├── services/
│   └── api.js                        # 수정: API 클라이언트
│
└── utils/
    ├── positionConfig.js             # 새로 작성: 포지션 설정
    └── ratingCalculator.js           # 새로 작성: 능력치 계산
```

---

## 🎨 능력치 평가 시스템 설계

### 포지션별 능력치 카테고리

#### 골키퍼 (GK)
1. **반응속도** (Reflexes): -5.0 ~ +5.0
2. **포지셔닝** (Positioning): -5.0 ~ +5.0
3. **핸들링** (Handling): -5.0 ~ +5.0
4. **발재간** (Kicking): -5.0 ~ +5.0
5. **공중볼 처리** (Aerial): -5.0 ~ +5.0
6. **1:1 대응** (One-on-One): -5.0 ~ +5.0

#### 수비수 (CB/FB/DF)
1. **태클** (Tackling): -5.0 ~ +5.0
2. **마크** (Marking): -5.0 ~ +5.0
3. **포지셔닝** (Positioning): -5.0 ~ +5.0
4. **헤더** (Heading): -5.0 ~ +5.0
5. **피지컬** (Physicality): -5.0 ~ +5.0
6. **스피드** (Speed): -5.0 ~ +5.0
7. **패스** (Passing): -5.0 ~ +5.0

#### 미드필더 (DM/CM/AM)
1. **패스** (Passing): -5.0 ~ +5.0
2. **비전** (Vision): -5.0 ~ +5.0
3. **드리블** (Dribbling): -5.0 ~ +5.0
4. **슈팅** (Shooting): -5.0 ~ +5.0
5. **태클** (Tackling): -5.0 ~ +5.0
6. **체력** (Stamina): -5.0 ~ +5.0
7. **창조력** (Creativity): -5.0 ~ +5.0

#### 공격수 (FW/ST/W)
1. **슈팅** (Finishing): -5.0 ~ +5.0
2. **위치선정** (Positioning): -5.0 ~ +5.0
3. **드리블** (Dribbling): -5.0 ~ +5.0
4. **스피드** (Pace): -5.0 ~ +5.0
5. **피지컬** (Physicality): -5.0 ~ +5.0
6. **헤더** (Heading): -5.0 ~ +5.0
7. **퍼스트터치** (First Touch): -5.0 ~ +5.0

### 평가 기준
- **+5.0**: 세계 최정상급 (월드클래스)
- **+3.0 ~ +4.75**: 리그 최상위권
- **+1.0 ~ +2.75**: 리그 평균 이상
- **0.0**: 리그 평균
- **-1.0 ~ -0.25**: 리그 평균 이하
- **-2.0 ~ -1.25**: 보완 필요
- **-5.0**: 매우 취약

---

## 📡 선수 데이터 스크래핑 전략

### 데이터 소스
1. **FBref (fbref.com)**
   - EPL 팀별 선수 명단
   - 선수 프로필 (이름, 나이, 국적, 포지션)
   - 경기 출전 기록

2. **Transfermarkt (선택적)**
   - 선수 시장 가치
   - 이적 정보

### 스크래핑 항목
```python
{
    'id': int,                    # 고유 ID
    'name': str,                  # 선수 이름
    'team': str,                  # 소속 팀
    'position': str,              # 포지션 (GK/DF/MF/FW)
    'detailed_position': str,     # 세부 포지션 (CB/CM/ST 등)
    'number': int,                # 등번호
    'age': int,                   # 나이
    'nationality': str,           # 국적
    'height': str,                # 키
    'foot': str,                  # 주발 (left/right/both)
    'market_value': str,          # 시장 가치 (선택)
    'contract_until': str,        # 계약 만료일 (선택)
    'appearances': int,           # 출전 경기 수
    'goals': int,                 # 득점
    'assists': int,               # 어시스트
}
```

### 스크래핑 주기
- **초기 로드**: 서버 시작 시 전체 팀 스크래핑
- **업데이트**: 주 1회 (매주 월요일 자동 업데이트)
- **캐싱**: 24시간 캐시 유지

---

## 🗄️ 데이터베이스 스키마

### 새로운 테이블 구조

#### 1. Teams (팀)
```sql
CREATE TABLE teams (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    short_name TEXT,
    logo_url TEXT,
    stadium TEXT,
    manager TEXT,
    founded INTEGER
);
```

#### 2. Players (선수)
```sql
CREATE TABLE players (
    id INTEGER PRIMARY KEY,
    team_id INTEGER,
    name TEXT NOT NULL,
    position TEXT NOT NULL,
    detailed_position TEXT,
    number INTEGER,
    age INTEGER,
    nationality TEXT,
    height TEXT,
    foot TEXT,
    market_value TEXT,
    contract_until TEXT,
    appearances INTEGER DEFAULT 0,
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    photo_url TEXT,
    FOREIGN KEY (team_id) REFERENCES teams(id)
);
```

#### 3. Player_Ratings (선수 능력치)
```sql
CREATE TABLE player_ratings (
    id INTEGER PRIMARY KEY,
    player_id INTEGER,
    user_id TEXT DEFAULT 'default',  -- 여러 사용자 지원 가능
    attribute_name TEXT NOT NULL,    -- 능력치 이름
    rating REAL NOT NULL,            -- -5.0 ~ +5.0
    notes TEXT,                      -- 메모
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(id),
    UNIQUE(player_id, user_id, attribute_name)
);
```

#### 4. Position_Attributes (포지션별 능력치 템플릿)
```sql
CREATE TABLE position_attributes (
    id INTEGER PRIMARY KEY,
    position TEXT NOT NULL,          -- GK/DF/MF/FW
    attribute_name TEXT NOT NULL,
    display_name_ko TEXT,            -- 한글 표시명
    display_order INTEGER,           -- 표시 순서
    UNIQUE(position, attribute_name)
);
```

---

## 🚀 구현 단계

### Phase 1: 정리 및 제거 (1-2일)
- [ ] 통계 모델 파일 제거
- [ ] 예측 관련 API 엔드포인트 제거
- [ ] 프론트엔드 통계 컴포넌트 제거
- [ ] App.js 간소화
- [ ] 불필요한 테스트 파일 제거

### Phase 2: 선수 데이터 인프라 구축 (2-3일)
- [ ] 선수 스크래퍼 개발 (`squad_scraper.py`)
- [ ] 데이터베이스 스키마 재설계
- [ ] 선수 데이터 초기 수집 (20개 팀)
- [ ] API 엔드포인트 재구성

### Phase 3: 능력치 시스템 개발 (3-4일)
- [ ] 포지션별 능력치 설정 시스템
- [ ] 능력치 저장/불러오기 로직
- [ ] RatingEditor 컴포넌트 개발
- [ ] RatingSlider 컴포넌트 개발
- [ ] 능력치 데이터 검증 로직

### Phase 4: UI/UX 개발 (3-4일)
- [ ] TeamSelector 컴포넌트
- [ ] PlayerList 컴포넌트
- [ ] PlayerCard 컴포넌트
- [ ] 필터링/검색 기능
- [ ] 반응형 디자인

### Phase 5: 고급 기능 (2-3일)
- [ ] 팀 전체 능력치 분석 대시보드
- [ ] 능력치 데이터 내보내기/가져오기 (JSON)
- [ ] 포지션별 평균 능력치 계산
- [ ] 능력치 히스토리 추적

### Phase 6: 테스트 및 배포 (1-2일)
- [ ] API 테스트 작성
- [ ] E2E 테스트
- [ ] 문서화
- [ ] 배포 준비

**예상 총 소요 시간**: 12-18일

---

## 📈 성공 지표

### 기술적 지표
- [ ] 20개 EPL 팀 선수 데이터 100% 수집
- [ ] 포지션별 능력치 평가 시스템 완성
- [ ] 평균 페이지 로딩 시간 < 2초
- [ ] API 응답 시간 < 500ms

### 사용자 경험 지표
- [ ] 팀 선택부터 선수 능력치 평가까지 < 5 클릭
- [ ] 능력치 저장/불러오기 성공률 100%
- [ ] 모바일 반응형 완벽 지원

---

## 🎯 최종 결과물

### 핵심 기능
1. ✅ EPL 20개 팀 선수 명단 실시간 조회
2. ✅ 포지션별 맞춤 능력치 평가 (6-7개 항목)
3. ✅ -5.0 ~ +5.0 범위, 0.25 단위 정밀 평가
4. ✅ 팀별 능력치 저장/관리
5. ✅ 능력치 데이터 내보내기/가져오기
6. ✅ 팀 분석 대시보드

### 제거된 기능
- ❌ 경기 예측
- ❌ 확률 계산
- ❌ 통계 모델
- ❌ 배팅 분석

---

## 💡 추가 개선 아이디어 (선택)

### 단기 (출시 후 1-2개월)
- 선수 비교 기능
- 포지션별 랭킹 시스템
- 능력치 변화 추적

### 중기 (3-6개월)
- 팀 라인업 시뮬레이터
- 전술 포메이션 분석
- 선수 이적 시나리오

### 장기 (6개월+)
- 다른 리그 지원 (라리가, 분데스리가 등)
- 커뮤니티 평균 능력치
- AI 추천 라인업

---

## 📝 다음 단계

1. **계획 승인 받기** ✅
2. **Phase 1 시작**: 불필요한 코드 제거
3. **선수 스크래퍼 개발** 우선순위 높음
4. **UI 목업 작성** (선택)

---

**작성일**: 2025-10-03
**예상 완료일**: 2025-10-21 (Phase 6 완료 기준)
