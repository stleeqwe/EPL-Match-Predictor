# 🚀 빠른 시작 가이드

## Phase 3 완료! 축구 경기 승부 예측 시스템이 준비되었습니다.

---

## ✅ 현재 상태

### 백엔드 (Python Flask) ✓
- Dixon-Coles 통계 모델 구현 완료
- Pi-ratings 시스템 통합
- Feature Engineering 모듈
- Flask REST API 서버 (포트 5001)
- **서버 실행 중**: http://localhost:5001

### 프론트엔드 (React) ✓
- 프로토타입 기반 UI 구현
- API 연동 완료
- 3가지 예측 모드 (Data/개인/하이브리드)

---

## 🎯 지금 바로 실행하기

### 1단계: 백엔드 실행 (이미 실행 중)

현재 백엔드 서버가 실행 중입니다:
```
✓ Flask API: http://localhost:5001
✓ Dixon-Coles 모델 학습 완료
✓ API 엔드포인트 활성화
```

**API 테스트:**
```bash
curl http://localhost:5001/api/health
# 응답: {"message": "API is running", "status": "ok"}
```

### 2단계: 프론트엔드 실행

새 터미널을 열어서:
```bash
cd /Users/pukaworks/soccer-predictor/frontend/epl-predictor
npm start
```

브라우저가 자동으로 `http://localhost:3000`을 엽니다!

---

## 📖 사용 방법

### 웹 인터페이스

1. **경기 선택**: 좌우 화살표로 Gameweek 8 경기 탐색
2. **모드 선택**:
   - 📊 **Data 분석**: Dixon-Coles 통계 모델
   - ⚙️ **개인분석**: 선수 능력치 기반 (개발 중)
   - 🎯 **하이브리드**: 두 모델 결합

3. **예측 결과 확인**:
   - 예상 스코어 (소수점)
   - 승/무/패 확률 (%)
   - 확률 바 시각화

### API 직접 호출

```bash
# 경기 예측
curl -X POST http://localhost:5001/api/predict \
  -H "Content-Type: application/json" \
  -d '{
    "home_team": "Manchester City",
    "away_team": "Liverpool",
    "model_type": "statistical"
  }'

# 팀 목록
curl http://localhost:5001/api/teams

# 경기 일정
curl http://localhost:5001/api/fixtures
```

---

## 🔬 구현된 모델

### Dixon-Coles 모델 (1997)
```
λ_home = α_home × β_away × γ × 1.43
λ_away = α_away × β_home

P(결과) = Poisson(λ) × τ(i,j)
```

**특징:**
- Dependency parameter (ρ): 저점수 경기 보정
- Time weighting (ξ): 최근 경기 가중치
- Home advantage (γ): 약 1.3

### Pi-ratings 시스템
- 홈/원정 별도 레이팅
- 학습률: λ = 0.06
- 골 차이 기반 동적 업데이트

---

## ⚠️ 알려진 이슈

### XGBoost Warning
```
Warning: XGBoost not available
Install libomp: brew install libomp
```

**해결 방법** (선택사항):
```bash
brew install libomp
```

현재는 Dixon-Coles 모델만 사용하며 정상 작동합니다.

### Port 5000 충돌
macOS AirPlay Receiver가 포트 5000 사용 → 포트 5001로 변경 완료 ✓

---

## 📂 프로젝트 구조

```
soccer-predictor/
├── backend/
│   ├── api/app.py                     # Flask API 서버
│   ├── models/
│   │   ├── dixon_coles.py             # Dixon-Coles 모델
│   │   ├── feature_engineering.py     # Pi-ratings 등
│   │   └── ensemble.py                # 앙상블
│   ├── data_collection/
│   │   ├── fbref_scraper.py           # FBref 스크래퍼
│   │   └── understat_scraper.py       # xG 데이터
│   └── database/schema.py             # DB 스키마
│
├── frontend/epl-predictor/
│   └── src/App.js                     # React 메인
│
├── README.md                           # 상세 문서
└── QUICKSTART.md                       # 이 파일
```

---

## 🎨 UI/UX 기능

### 구현 완료 ✓
- ✅ 다크모드 토글
- ✅ 경기 선택 네비게이션
- ✅ 3가지 분석 모드 탭
- ✅ 실시간 예측 결과 표시
- ✅ 확률 바 애니메이션
- ✅ 예상 스코어 시각화

### 개발 예정
- ⏳ 가중치 조절 슬라이더
- ⏳ 선수 능력치 입력 UI
- ⏳ 과거 경기 예측 정확도 차트

---

## 🧪 테스트

### 백엔드 테스트
```bash
cd /Users/pukaworks/soccer-predictor

# Dixon-Coles 모델 테스트
source venv/bin/activate
python backend/models/dixon_coles.py

# 특징 엔지니어링 테스트
python backend/models/feature_engineering.py
```

### API 테스트
```bash
# 헬스 체크
curl http://localhost:5001/api/health

# 경기 예측
curl -X POST http://localhost:5001/api/predict \
  -H "Content-Type: application/json" \
  -d '{"home_team":"Manchester City","away_team":"Liverpool","model_type":"statistical"}'

# 팀 통계
curl http://localhost:5001/api/team-stats/Manchester%20City
```

---

## 🛠️ 문제 해결

### 서버가 시작되지 않을 때
```bash
# 포트 확인
lsof -ti:5001

# 기존 프로세스 종료
kill -9 $(lsof -ti:5001)

# 재시작
cd /Users/pukaworks/soccer-predictor
source venv/bin/activate
python backend/api/app.py
```

### React 빌드 오류
```bash
cd frontend/epl-predictor
rm -rf node_modules package-lock.json
npm install
npm start
```

---

## 📊 예측 정확도 (이론적)

| 모델 | 정확도 | RPS |
|------|--------|-----|
| Dixon-Coles | 52-67% | 0.19-0.20 |
| Pi-ratings | - | 0.1925 |
| 북메이커 | - | 0.202-0.206 |

**현재 구현**: Dixon-Coles 기반 (더미 데이터)

---

## 🚀 다음 단계

### 즉시 가능
1. 프론트엔드 실행: `cd frontend/epl-predictor && npm start`
2. 브라우저에서 테스트: http://localhost:3000
3. 다양한 경기 선택하여 예측 확인

### 단기 개선
1. 실제 FBref/Understat 데이터 연동
2. PostgreSQL 설정 및 마이그레이션
3. 선수 능력치 입력 UI 완성

### 장기 목표
1. XGBoost 모델 학습 (실제 데이터)
2. Transformer 기반 모델 실험
3. 웹 서비스 배포 (Docker + Cloud)

---

## 🎉 축하합니다!

**Phase 3 완료**: 풀스택 축구 경기 승부 예측 시스템이 로컬에서 실행 중입니다!

```
백엔드 ✓   Flask API (Dixon-Coles)
프론트엔드 ✓   React 앱 (프로토타입 통합)
API 연동 ✓   실시간 예측
```

**지금 바로 사용해보세요:**
```bash
cd frontend/epl-predictor && npm start
```

Happy Predicting! ⚽️
