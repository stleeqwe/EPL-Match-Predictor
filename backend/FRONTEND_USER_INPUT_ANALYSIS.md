# 프론트엔드 사용자 Domain Input 분석

## 📅 작성일
2025-10-16

## 🎯 목적
프론트엔드에서 사용자가 입력하는 domain input이 무엇인지 파악하여,
백엔드 E2E 테스트에 사용된 input과 비교 분석

---

## 🖥️ 프론트엔드: 사용자가 직접 입력하는 Domain Input

### ✅ **1단계: 선수 평가 (Player Rating)**

**컴포넌트**: `PlayerRatingManager.js` → `RatingEditor.js`

**사용자 입력**:
```javascript
// 각 선수마다 18개 속성을 1.0 ~ 5.0 점수로 평가
const playerRatings = {
  [playerId]: {
    // 공격 속성 (6개)
    finishing: 4.5,        // 마무리
    shotPower: 4.0,        // 슛 파워
    longShots: 3.5,        // 중거리 슛
    heading: 3.0,          // 헤딩
    volleys: 3.5,          // 발리슛
    penalties: 4.0,        // 페널티킥

    // 기술 속성 (6개)
    dribbling: 4.5,        // 드리블
    ballControl: 4.5,      // 볼 컨트롤
    crossing: 3.5,         // 크로스
    shortPassing: 4.0,     // 짧은 패스
    longPassing: 3.5,      // 긴 패스
    curve: 3.5,            // 커브

    // 수비 속성 (3개)
    marking: 3.0,          // 마킹
    standingTackle: 3.0,   // 스탠딩 태클
    slidingTackle: 2.5,    // 슬라이딩 태클

    // 신체 속성 (3개)
    acceleration: 4.5,     // 가속력
    sprintSpeed: 4.5,      // 질주 속도
    stamina: 4.0,          // 스태미나

    // 추가 정보
    _subPosition: 'RW',    // 세부 포지션
    _comment: '오른쪽 윙어로 활용 가능' // 코멘트
  }
}
```

**저장 경로**: `backend/data/player_ratings/{team_name}/{player_id}.json`

**특징**:
- ✅ **18개 속성 직접 평가** (공격 6개, 기술 6개, 수비 3개, 신체 3개)
- ✅ **1.0 ~ 5.0 범위** (0.1 단위 조정 가능)
- ✅ **세부 포지션 지정** (예: RW, LW, ST, CM 등)
- ✅ **코멘트 추가** (자유 텍스트)
- ⚠️ **모든 선수를 평가해야 함** (최소 11명 이상)

---

### ✅ **2단계: 포메이션 선택 (Formation)**

**컴포넌트**: `SquadBuilder.js` (포메이션 드롭다운)

**사용자 입력**:
```javascript
const formation = '4-3-3'; // 6가지 포메이션 중 선택

// 가능한 포메이션:
// - '4-3-3': 전통적인 공격형 포메이션
// - '4-4-2': 균형잡힌 포메이션
// - '4-2-3-1': 현대적인 중원 밀집
// - '3-5-2': 측면 공격 중시
// - '3-4-3': 공격적 변형
// - '5-3-2': 수비적 변형
```

**저장 경로**: `backend/data/formations/{team_name}.json`

**형식**:
```json
{
  "team": "Arsenal",
  "formation": "4-3-3",
  "saved_at": "2025-10-16T12:00:00Z"
}
```

**특징**:
- ✅ **6가지 포메이션 중 선택**
- ✅ **각 포메이션마다 포지션 좌표 사전 정의됨**
- ✅ **드롭다운에서 한 번 클릭으로 선택**

---

### ✅ **3단계: 라인업 구성 (Lineup)**

**컴포넌트**: `SquadBuilder.js` (드래그 앤 드롭)

**사용자 입력**:
```javascript
const lineup = {
  starters: {
    // 포지션별로 선수 배치 (11명)
    'GK': playerId,
    'LB': playerId,
    'CB-L': playerId,
    'CB-R': playerId,
    'RB': playerId,
    'CM-L': playerId,
    'CDM': playerId,
    'CM-R': playerId,
    'LW': playerId,
    'ST': playerId,
    'RW': playerId
  },
  substitutes: [playerId1, playerId2, playerId3, ...] // 후보 선수
}
```

**저장 경로**: `backend/data/lineups/{team_name}.json`

**형식**:
```json
{
  "team": "Arsenal",
  "formation": "4-3-3",
  "starters": {
    "GK": 123,
    "LB": 456,
    "CB-L": 789,
    ...
  },
  "substitutes": [999, 888, 777],
  "saved_at": "2025-10-16T12:00:00Z"
}
```

**특징**:
- ✅ **드래그 앤 드롭으로 11명 배치**
- ✅ **포메이션에 따라 포지션 자동 생성**
- ✅ **부상자는 배치 불가** (빨간색 표시)
- ✅ **후보 선수도 등록 가능**
- ⚠️ **정확히 11명을 배치해야 함**

---

### ✅ **4단계: 전술 설정 (Tactics)**

**컴포넌트**: `TacticsEditor.js` (추정 - 실제 파일 미확인)

**사용자 입력** (추정):
```javascript
const tactics = {
  // 수비 전술
  defensive_line: 70,        // 수비 라인 높이 (0-100)
  defensive_width: 60,       // 수비 폭 (0-100)
  defensive_aggression: 50,  // 수비 압박 강도 (0-100)

  // 공격 전술
  attacking_width: 70,       // 공격 폭 (0-100)
  attacking_tempo: 65,       // 공격 템포 (0-100)
  attacking_risk: 60,        // 공격 위험 감수도 (0-100)

  // 전환 전술
  counter_attack_speed: 80,  // 역습 속도 (0-100)
  build_up_style: 'short',   // 빌드업 스타일 ('short', 'long', 'mixed')
  pressing_intensity: 75     // 프레싱 강도 (0-100)
}
```

**저장 경로**: `backend/data/tactics/{team_name}.json`

**특징** (추정):
- ✅ **9-12개 전술 파라미터**
- ✅ **슬라이더로 0-100 범위 조정**
- ✅ **프리셋 제공 가능** (예: 'Attacking', 'Defensive', 'Balanced')

---

## 🔄 시뮬레이션 실행 조건

### ✅ **필수 완료 항목**

`backend/api/app.py` - `/api/teams/<team_name>/simulation-ready` 엔드포인트에서 확인:

```python
def check_simulation_ready(team_name):
    # 1. Rating 확인
    has_rating = os.path.exists(f"data/overall_scores/{team_name}.json")

    # 2. Formation 확인
    has_formation = os.path.exists(f"data/formations/{team_name}.json")

    # 3. Lineup 확인
    has_lineup = os.path.exists(f"data/lineups/{team_name}.json")

    # 4. Tactics 확인
    has_tactics = os.path.exists(f"data/tactics/{team_name}.json")

    ready = has_rating and has_formation and has_lineup and has_tactics

    return {
        'ready': ready,
        'completed': {
            'rating': has_rating,
            'formation': has_formation,
            'lineup': has_lineup,
            'tactics': has_tactics
        },
        'missing': ['rating', 'formation', 'lineup', 'tactics']  # 누락된 항목
    }
```

**4가지 조건이 모두 충족되어야만 시뮬레이션 실행 가능!**

---

## 📊 백엔드 E2E 테스트와의 비교

### 🔴 **차이점 발견**

#### **백엔드 E2E 테스트 Input** (test_e2e_comprehensive.py)
```python
# 간소화된 TeamInput
team_input = TeamInput(
    name="Arsenal",
    formation="4-3-3",
    recent_form="WWDWL",         # ✅ 프론트엔드에 없음
    injuries=["Partey"],         # ✅ 프론트엔드에 없음
    key_players=["Saka", "Odegaard", "Martinelli"],  # ✅ 프론트엔드에 없음
    attack_strength=85.0,        # ❌ 계산된 값 (프론트엔드에서 직접 입력 안 함)
    defense_strength=82.0,       # ❌ 계산된 값
    press_intensity=88.0,        # ❌ 계산된 값
    buildup_style="possession"   # ❌ 계산된 값
)
```

#### **프론트엔드 실제 Input**
```javascript
// 1. 선수 18개 속성 평가 (각 선수마다)
playerRatings[playerId] = {
  finishing: 4.5,
  shotPower: 4.0,
  // ... 18개 속성
}

// 2. 포메이션
formation = '4-3-3'

// 3. 라인업 (11명 배치)
lineup = {
  starters: { 'GK': id, 'LB': id, ... },
  substitutes: [id1, id2, ...]
}

// 4. 전술 파라미터
tactics = {
  defensive_line: 70,
  attacking_tempo: 65,
  // ... 9-12개 파라미터
}
```

---

## ⚠️ **주요 차이점 및 누락된 연결**

### 1. **Recent Form (최근 폼)** - 프론트엔드에서 입력 안 받음
- 백엔드 테스트: `recent_form="WWDWL"` 명시적으로 제공
- 프론트엔드: **입력 방법 없음**
- **해결 필요**: API에서 실시간 데이터 가져오거나 사용자 입력 추가

### 2. **Injuries (부상자 목록)** - 부분적으로만 반영
- 백엔드 테스트: `injuries=["Partey"]` 명시적으로 제공
- 프론트엔드: 부상자 데이터 있지만 **시뮬레이션 input으로 전달 안 됨**
- **해결 필요**: 라인업에서 부상자 제외 + MatchInput에 injuries 추가

### 3. **Key Players (핵심 선수)** - 입력 없음
- 백엔드 테스트: `key_players=["Saka", "Odegaard", "Martinelli"]`
- 프론트엔드: **입력 방법 없음**
- **해결 방안**: 선수 평가 점수 상위 3명 자동 선정

### 4. **Attack/Defense/Press Strength** - 계산 로직 확인 필요
- 백엔드 테스트: 직접 명시 (attack_strength=85.0)
- 프론트엔드: **18개 선수 속성에서 자동 계산되어야 함**
- **확인 필요**: TeamInputMapper가 올바르게 계산하는지

### 5. **Buildup Style** - 전술에서 추출 필요
- 백엔드 테스트: `buildup_style="possession"`
- 프론트엔드: **tactics에서 build_up_style 사용**
- **확인 필요**: TacticsEditor가 올바른 형식으로 저장하는지

---

## 🎯 결론

### ✅ **프론트엔드가 제공하는 것**
1. ✅ 선수별 18개 속성 평가 (매우 상세함)
2. ✅ 포메이션 선택
3. ✅ 11명 라인업 배치
4. ✅ 전술 파라미터 (9-12개)

### ❌ **프론트엔드가 제공하지 않는 것**
1. ❌ Recent Form (최근 5경기 결과)
2. ❌ Injuries (부상자 목록을 input으로 전달)
3. ❌ Key Players (핵심 선수 명단)

### 🔧 **계산으로 얻어야 하는 것**
1. 🔧 Attack Strength (18개 공격 속성 평균)
2. 🔧 Defense Strength (수비 속성 평균)
3. 🔧 Press Intensity (전술 파라미터에서)
4. 🔧 Buildup Style (전술 파라미터에서)

---

## 🚀 다음 단계

### 1. **백엔드 매핑 검증**
```bash
# TeamInputMapper가 프론트엔드 데이터를 올바르게 변환하는지 확인
python3 -m pytest backend/tests/unit/test_team_input_mapper.py -v
```

### 2. **누락된 Input 추가**
- [ ] Recent Form 입력 UI 추가
- [ ] Injuries를 MatchInput에 포함
- [ ] Key Players 자동 선정 로직 추가

### 3. **E2E 테스트 Input 현실화**
- [ ] 프론트엔드에서 실제로 제공하는 데이터로 E2E 테스트 재작성
- [ ] 18개 선수 속성 → 4개 팀 전력 자동 계산 검증
- [ ] Tactics → Buildup Style 매핑 검증

---

## 📝 요약

**프론트엔드는 매우 상세한 데이터를 받지만 (선수별 18개 속성),
백엔드 E2E 테스트는 간소화된 데이터를 사용 (4개 팀 속성).**

**중요한 연결고리**:
- `18개 선수 속성` → (계산) → `4개 팀 전력` → (AI 프롬프트) → `Scenario 생성`

**이 변환이 올바르게 작동하는지 검증이 필요합니다!**
