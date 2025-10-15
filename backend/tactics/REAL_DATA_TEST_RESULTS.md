# 전술 프레임워크 실전 테스트 결과

**테스트 일시**: 2025-10-12
**테스트 데이터**: 실제 EPL 2025-26 시즌 스쿼드 데이터 (20팀)
**테스트 범위**: 포메이션 분석, 실제 경기 매칭, 전술 추천

---

## 📊 테스트 결과 요약

### ✅ 성공 사항

1. **실제 EPL 데이터 통합 성공**
   - 20개 팀의 실제 스쿼드 데이터 로드
   - 선수 정보와 전술 시스템 연동 완료

2. **포메이션별 효과성 분석 정상 작동**
   - 12가지 득점 경로 분류 시스템 작동
   - 6개 포메이션별 차단률 계산 정확
   - EPL 빈도 데이터 기반 가중치 적용

3. **실제 경기 시나리오 시뮬레이션**
   - Arsenal vs Man City 빅매치 분석 성공
   - 팀 능력 계수 반영 (Arsenal: 1.15, Man City: 1.18)
   - 종합 수비력 점수 산출 (Arsenal: 90.5/100, Man City: 92.3/100)

4. **전술 추천 시스템 작동**
   - 상대 공격 스타일에 맞는 포메이션 추천
   - 차단률 기반 우선순위 정렬

---

## 🔍 주요 발견 사항

### 1. 포메이션별 특징 (실전 데이터 기반)

#### **중앙 침투 대응** (EPL에서 28% 빈도)
```
🥇 4-2-3-1 미드 블록: 95% 차단률
🥈 4-4-2 로우 블록: 90%
🥉 4-3-3 하이 프레싱: 85%
```
→ **인사이트**: 중앙 밀집 포메이션이 가장 효과적

#### **측면 침투 대응** (EPL에서 28% 빈도)
```
🥇 3-5-2 윙백 시스템: 93% 차단률
🥈 4-3-3 하이 프레싱: 78%
🥉 4-4-2 로우 블록: 75%
```
→ **인사이트**: 윙백이 있는 3백 시스템이 측면 커버에 유리

#### **역습 대응** (EPL에서 4% 빈도)
```
🥇 4-4-2 로우 블록: 95% 차단률
🥈 4-2-3-1 미드 블록: 82%
🥉 3-5-2 윙백 시스템: 55%
   4-3-3 하이 프레싱: 45% (취약)
```
→ **인사이트**: 하이 프레싱은 역습에 매우 취약

---

### 2. 실제 경기 분석: Arsenal vs Man City

#### 기본 정보
- **홈팀**: Arsenal (스쿼드 36명, 능력 1.15)
- **원정팀**: Man City (스쿼드 47명, 능력 1.18)
- **포메이션**: 둘 다 4-3-3 (하이 프레싱)

#### 분석 결과
```
Arsenal 수비력:  90.5/100 (Exceptional)
Man City 수비력: 92.3/100 (Exceptional)
전술적 우위:     BALANCED (차이 1.8점)
```

#### 결론
- 두 팀 모두 최상위 수비력 보유
- 동일한 4-3-3 포메이션 사용으로 전술적 우위 없음
- **균형잡힌 접전 예상** → 선수 개인 능력과 컨디션이 승부 결정

---

### 3. Man City 스타일 대응 전략

#### Man City 공격 패턴 (추정)
- 중앙 침투: 35%
- 측면 침투: 25%
- 컷백: 20%
- 역습: 10%
- 세트피스: 10%

#### 최적 대응 포메이션 Top 3

**🥇 4-4-2 로우 블록 (93.7% 종합 차단률)**
- 고속 역습 차단: 100.0%
- 중앙 침투 차단: 99.0%
- 코너킥 차단: 96.8%
- **특징**: 수비적이지만 가장 안정적

**🥈 4-2-3-1 미드 블록 (91.4%)**
- 중앙 침투 차단: 100.0%
- 컷백 차단: 96.8%
- 고속 역습 차단: 90.2%
- **특징**: 공수 밸런스가 좋음

**🥉 3-5-2 윙백 시스템 (91.0%)**
- 측면 침투 차단: 100.0%
- 컷백 차단: 96.8%
- 중앙 침투 차단: 90.2%
- **특징**: 측면 수비 특화

---

### 4. 포메이션 매칭 분석

#### 균형잡힌 매칭 (차이 < 5점)
- **4-3-3 vs 4-2-3-1**: 차이 1.6점 → 선수 실력이 승부 가름
- **3-5-2 vs 4-4-2**: 차이 0.8점 → 거의 동일한 수비력

#### 명확한 우위 (차이 > 5점)
- **4-1-4-1 vs 4-3-3**: 4-3-3이 5.0점 우위
  - 4-1-4-1(수비형)은 공격력이 약하지만 수비도 4-3-3보다 취약

---

## ⚠️ 현재 한계점

### 1. 데이터 부족
- ❌ **실제 선수 능력치 없음**: 현재는 팀 레벨 계수만 사용 (1.15, 1.18 등)
- ❌ **포지션별 선수 매칭 없음**: squad_data에 선수 정보는 있지만 포지션별 능력치가 없음
- ❌ **최근 경기 폼 미반영**: 컨디션, 부상, 피로도 등 실시간 데이터 없음

### 2. 전술 세부사항 부족
- ❌ **세부 전술 파라미터 없음**: 압박 강도, 수비 라인 높이 등 실제 설정값 없음
- ❌ **감독 스타일 미반영**: 각 팀의 실제 플레이 스타일 데이터 없음

### 3. EPL 실제 데이터 검증 필요
- ⚠️ **차단률 수치 검증 필요**: 현재는 이론적 수치, 실제 경기 데이터와 비교 필요
- ⚠️ **득점 경로 빈도 업데이트**: 현재 2017-2024 데이터, 2025 시즌 업데이트 필요

---

## 🚀 다음 단계 제안

### Phase 1: 데이터 수집 및 검증 (우선순위: 높음)

#### 1.1 실제 경기 데이터 수집
```
데이터 소스:
- FBref.com (포메이션, 패스맵, 슈팅 위치)
- Understat.com (xG 데이터, 슈팅 좌표)
- WhoScored.com (전술 분석, 히트맵)
- StatsBomb (이벤트 데이터, 상업용)

수집 항목:
1. 팀별 실제 포메이션 사용률
2. 득점 경로별 실제 골 수 (2024-25 시즌)
3. 포메이션별 실제 차단률 통계
4. xG Against by formation
```

#### 1.2 선수 능력치 통합
```python
# 현재 프로젝트의 Player 모델과 연동
# backend/models/player.py 활용

필요 작업:
1. squad_data의 선수를 Player 모델로 매핑
2. technical_attributes에서 전술 관련 능력치 추출
   - tackling, interceptions (수비)
   - passing, vision (빌드업)
   - pace, stamina (체력)
3. integration.py의 apply_tactics_to_player() 활용
```

#### 1.3 데이터 검증
```
목표: 전술 프레임워크 예측 vs 실제 경기 결과 비교

방법:
1. 최근 10경기 선택 (Arsenal, Man City, Liverpool 등)
2. 프레임워크로 예측 (수비력, 차단률)
3. 실제 경기 결과와 비교 (실제 실점, xGA)
4. 차이가 크면 차단률 수치 보정
```

---

### Phase 2: 기능 확장 (우선순위: 중)

#### 2.1 실시간 전술 분석 API
```python
# backend/tactics/api/endpoints.py

@app.route('/api/tactics/analyze-match', methods=['POST'])
def analyze_match():
    """
    실시간 경기 전술 분석

    Input:
    {
        "home_team": "Arsenal",
        "away_team": "Man City",
        "home_formation": "4-3-3",
        "away_formation": "4-3-3"
    }

    Output:
    {
        "tactical_advantage": "balanced",
        "home_defense_score": 90.5,
        "away_defense_score": 92.3,
        "recommendations": [...]
    }
    """
```

#### 2.2 득점 경로 자동 분류
```python
# 실제 골 비디오/데이터를 받아서 자동 분류
from tactics.analyzer.goal_path_classifier import GoalPathClassifier, GoalData

# Understat API에서 슈팅 데이터 가져오기
# → GoalData로 변환
# → 자동 분류
# → 통계 업데이트
```

#### 2.3 포메이션 추천 시스템
```python
# 상대팀 분석 → 최적 포메이션 추천

@app.route('/api/tactics/recommend-formation', methods=['POST'])
def recommend_formation():
    """
    Input:
    {
        "opponent_team": "Man City",
        "our_squad": [player_ids],
        "match_importance": "high"  # high/medium/low
    }

    Output:
    {
        "recommended_formation": "4-4-2",
        "reasoning": "Man City's central attack is 35%...",
        "expected_blocking_rate": 93.7
    }
    """
```

---

### Phase 3: 시각화 및 UI (우선순위: 중)

#### 3.1 전술 대시보드
```
Streamlit 또는 React 대시보드

화면 구성:
1. 팀 비교 화면
   - 양팀 포메이션 시각화
   - 수비력 비교 차트
   - 득점 경로별 차단률 히트맵

2. 포메이션 추천 화면
   - 상대팀 공격 스타일 입력
   - Top 3 포메이션 추천
   - 차단률 상세 분석

3. 경기 예측 화면
   - 실시간 경기 분석
   - 승무패 확률
   - 예상 스코어라인
```

#### 3.2 포메이션 비주얼라이저
```
필드 위에 선수 배치 시각화

기능:
- 포메이션별 선수 위치 표시
- 압박 구역 히트맵
- 공격/수비 라인 시각화
- 취약 구역 표시
```

---

### Phase 4: 머신러닝 통합 (우선순위: 낮음)

#### 4.1 차단률 예측 모델
```python
# 수작업 차단률 → ML 모델로 자동 학습

모델:
- Input: 포메이션, 팀 능력, 득점 경로, 상황
- Output: 예측 차단률
- 학습 데이터: 실제 경기 결과 (xGA, 실점)

알고리즘:
- XGBoost 또는 Random Forest
- 2017-2025 EPL 데이터 학습
```

#### 4.2 득점 경로 분류 개선
```python
# 규칙 기반 → 딥러닝 모델

모델:
- LSTM/Transformer for sequence data
- 패스 시퀀스 → 득점 경로 분류
- 정확도 목표: 85%+
```

---

## 💡 즉시 실행 가능한 개선안

### 1. 팀 능력 계수 자동화
```python
# 현재: 수동 매핑 (team_ability_map)
# 개선: EPL 순위 테이블 기반 자동 계산

def calculate_team_ability_from_standings(team_name, season="2024-25"):
    """
    EPL 순위표 기반 능력 계수 계산

    1위 → 1.20
    2-3위 → 1.15-1.18
    4-6위 → 1.10-1.12
    7-10위 → 1.05-1.08
    11-15위 → 1.00-1.03
    16-20위 → 0.85-0.95
    """
    # FPL API 또는 스크래핑으로 순위 가져오기
    # 수식으로 능력 계수 계산
```

### 2. 선수 데이터 매핑
```python
# squad_data.py와 Player 모델 연동

from data.squad_data import SQUAD_DATA
from models.player import Player

def map_squad_to_tactical_system(team_name):
    """
    스쿼드 데이터를 전술 시스템에 매핑

    Returns:
    {
        'GK': [player1_abilities],
        'CB': [player2_abilities, player3_abilities],
        'DM': [player4_abilities],
        ...
    }
    """
    # 포지션별로 선수 분류
    # 각 선수의 능력치 추출
    # 평균값으로 팀 전술 적합도 계산
```

### 3. 경기 히스토리 추적
```python
# 예측과 실제 결과 비교 DB

CREATE TABLE tactical_predictions (
    match_id INT,
    home_team VARCHAR(50),
    away_team VARCHAR(50),
    predicted_home_defense DECIMAL(5,2),
    predicted_away_defense DECIMAL(5,2),
    actual_home_goals INT,
    actual_away_goals INT,
    actual_home_xg DECIMAL(5,2),
    prediction_accuracy DECIMAL(5,2),
    created_at TIMESTAMP
);

# 예측 정확도 추적 및 모델 개선
```

---

## 📈 예상 로드맵

### 단기 (1-2주)
- [x] ✅ 기본 프레임워크 구축
- [x] ✅ 실전 데이터 테스트
- [ ] 🔄 실제 EPL 데이터 수집 시작
- [ ] 🔄 선수 능력치 매핑

### 중기 (1개월)
- [ ] 📊 데이터 검증 완료
- [ ] 🔌 API 엔드포인트 구현
- [ ] 📱 기본 대시보드 구축

### 장기 (3개월)
- [ ] 🤖 머신러닝 모델 통합
- [ ] 📈 실시간 예측 시스템
- [ ] 🎯 프로덕션 배포

---

## ✅ 결론

### 현재 상태
전술 프레임워크는 **독립적으로 정상 작동**하며, 실제 EPL 데이터와 통합 가능한 것을 확인했습니다.

### 핵심 강점
1. ✅ 이론적으로 타당한 포메이션 분석
2. ✅ EPL 통계 기반 차단률 설정
3. ✅ 확장 가능한 아키텍처
4. ✅ 기존 프로젝트와 독립적 운영 가능

### 다음 우선순위
**가장 시급한 작업: 실제 경기 데이터 수집 및 검증**

실제 2024-25 시즌 경기 결과와 비교하여 차단률 수치를 보정하면, 더 정확한 예측이 가능합니다.

---

**테스트 결과 파일**: `tests/test_real_data.py`
**실행 방법**: `cd backend/tactics && python3 tests/test_real_data.py`
