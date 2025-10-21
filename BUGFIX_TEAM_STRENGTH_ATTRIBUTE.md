# 🐛 버그 수정: 'EnrichedTeamInput' object has no attribute 'team_strength'

## 🔍 에러 발견

**에러 메시지**:
```
Unexpected error: 'EnrichedTeamInput' object has no attribute 'team_strength'
```

**발생 위치**: `backend/services/enriched_simulation_service.py:297`

**발생 시점**: 시뮬레이션 실행 시 팀 데이터를 TeamInfo로 변환하는 과정

---

## 🔎 근본 원인 분석

### 잘못된 가정
Statistical Engine 스트리밍 기능을 추가하면서, `EnrichedTeamInput` 객체의 구조를 잘못 가정했습니다.

**잘못된 코드** (lines 297-300):
```python
home_team_info = TeamInfo(
    name=home_team_data.name,
    formation=home_team_data.formation,
    attack_strength=home_team_data.team_strength.get('attack', 75.0),  # ❌ 존재하지 않는 속성
    defense_strength=home_team_data.team_strength.get('defense', 75.0),  # ❌
    press_intensity=home_team_data.tactics.get('press_intensity', 70.0),  # ❌ tactics는 dict가 아님
    buildup_style=home_team_data.tactics.get('buildup_style', 'mixed')  # ❌
)
```

### 실제 데이터 구조

**`EnrichedTeamInput` 클래스** (`backend/ai/enriched_data_models.py:204-446`):

```python
@dataclass
class EnrichedTeamInput:
    name: str
    formation: str
    lineup: Dict[str, EnrichedPlayerInput]
    tactics: TacticsInput  # ✅ TacticsInput 객체 (dict가 아님)
    team_strength_ratings: TeamStrengthRatings  # tactical_understanding, positioning_balance, buildup_quality
    team_strategy_commentary: Optional[str] = None
    derived_strengths: Optional['DerivedTeamStrengths'] = None  # ✅ 여기에 attack/defense strength가 있음!
```

**`DerivedTeamStrengths` 클래스** (lines 448-479):

```python
@dataclass
class DerivedTeamStrengths:
    """11명 선수 속성에서 자동 계산된 팀 전력"""
    attack_strength: float        # 0-100
    defense_strength: float       # 0-100
    midfield_control: float       # 0-100
    physical_intensity: float     # 0-100
    press_intensity: float        # 0-100 (tactics.defensive.pressing_intensity * 10)
    buildup_style: str            # 'possession', 'direct', 'mixed'
```

**핵심**:
- ❌ `team_strength` 속성은 존재하지 않음
- ✅ `derived_strengths.attack_strength` 사용해야 함
- ✅ `derived_strengths.defense_strength` 사용해야 함
- ✅ `derived_strengths.press_intensity` 사용해야 함
- ✅ `derived_strengths.buildup_style` 사용해야 함

---

## ✅ 해결 방법

### 수정된 코드

**파일**: `backend/services/enriched_simulation_service.py:293-310`

```python
# Convert enriched team data to TeamInfo for statistical engine
home_team_info = TeamInfo(
    name=home_team_data.name,
    formation=home_team_data.formation,
    attack_strength=home_team_data.derived_strengths.attack_strength,  # ✅ 수정
    defense_strength=home_team_data.derived_strengths.defense_strength,  # ✅ 수정
    press_intensity=home_team_data.derived_strengths.press_intensity,  # ✅ 수정
    buildup_style=home_team_data.derived_strengths.buildup_style  # ✅ 수정
)

away_team_info = TeamInfo(
    name=away_team_data.name,
    formation=away_team_data.formation,
    attack_strength=away_team_data.derived_strengths.attack_strength,  # ✅ 수정
    defense_strength=away_team_data.derived_strengths.defense_strength,  # ✅ 수정
    press_intensity=away_team_data.derived_strengths.press_intensity,  # ✅ 수정
    buildup_style=away_team_data.derived_strengths.buildup_style  # ✅ 수정
)
```

---

## 📊 데이터 변환 플로우

### Before (잘못된 플로우)
```
EnrichedTeamInput
  └─ team_strength ❌ (존재하지 않음)
       ├─ attack: ?
       └─ defense: ?
  └─ tactics ❌ (TacticsInput 객체인데 dict로 취급)
       ├─ press_intensity: ?
       └─ buildup_style: ?
```

### After (올바른 플로우)
```
EnrichedTeamInput (실제 데이터)
  ├─ name: "Arsenal"
  ├─ formation: "4-3-3"
  ├─ lineup: {11명 선수 데이터}
  ├─ tactics: TacticsInput 객체
  │    ├─ defensive.pressing_intensity: 9 (0-10)
  │    └─ offensive.buildup_style: "short_passing"
  ├─ team_strength_ratings: TeamStrengthRatings
  │    ├─ tactical_understanding: 4.5
  │    ├─ positioning_balance: 4.25
  │    └─ buildup_quality: 4.5
  └─ derived_strengths: DerivedTeamStrengths ✅
       ├─ attack_strength: 85.7 (0-100) ← 11명 공격수/미드필더 평균
       ├─ defense_strength: 82.3 (0-100) ← 11명 수비수/미드필더 평균
       ├─ midfield_control: 78.5 (0-100)
       ├─ physical_intensity: 81.2 (0-100)
       ├─ press_intensity: 90.0 (0-100) ← tactics.defensive.pressing_intensity * 10
       └─ buildup_style: "possession" ← "short_passing" → "possession" 매핑
```

**변환 로직**:
```python
# EnrichedTeamInput → TeamInfo 변환
TeamInfo(
    name=enriched.name,
    formation=enriched.formation,
    # ✅ derived_strengths에서 가져오기
    attack_strength=enriched.derived_strengths.attack_strength,    # 85.7
    defense_strength=enriched.derived_strengths.defense_strength,  # 82.3
    press_intensity=enriched.derived_strengths.press_intensity,    # 90.0
    buildup_style=enriched.derived_strengths.buildup_style         # "possession"
)
```

---

## 🧪 테스트 방법

### 1. 백엔드 재시작
```bash
cd backend
python app.py
```

### 2. 시뮬레이션 실행
프론트엔드에서 Arsenal vs Liverpool 시뮬레이션 실행

### 3. 기대 결과

#### ✅ 정상 동작
```
INFO - EnrichedSimulationService initialized with statistical engine
INFO - Enriched simulation starting: Arsenal vs Liverpool
INFO - ✓ Arsenal data loaded: 11 players
INFO - ✓ Liverpool data loaded: 11 players
DEBUG - ⚽ Statistical simulation event: simulation_started
DEBUG - ⚽ Statistical simulation event: simulation_minute (0')
```

#### ❌ 에러 발생 시 (이전)
```
ERROR - Unexpected error in simulate_with_progress: 'EnrichedTeamInput' object has no attribute 'team_strength'
```

---

## 📖 배경 지식: DerivedTeamStrengths 계산 방식

`EnrichedTeamInput.__post_init__()`에서 자동 계산됩니다:

### 1. Attack Strength (0-100)
```python
# 공격수들의 overall_rating 평균 (가중치 0.7)
# + 미드필더들의 overall_rating 평균 (가중치 0.3)
# → 5.0 스케일을 100 스케일로 변환

# 예: Arsenal
# 공격수 3명: Saka(4.5), Martinelli(4.25), Jesus(4.0) → 평균 4.25
# 미드필더 3명: Odegaard(4.75), Rice(4.5), Havertz(4.0) → 평균 4.42
# attack_strength = (4.25 * 20 * 0.7) + (4.42 * 20 * 0.3) / (0.7 + 0.3)
#                 = 85.7
```

### 2. Defense Strength (0-100)
```python
# 수비수들의 overall_rating 평균 (가중치 0.7)
# + 미드필더들의 overall_rating 평균 (가중치 0.3)

# 예: Arsenal
# 수비수 4명: Timber(3.15), Saliba(4.5), Gabriel(4.25), White(4.0) → 평균 3.975
# 미드필더 3명: 평균 4.42
# defense_strength = (3.975 * 20 * 0.7) + (4.42 * 20 * 0.3) / 1.0
#                  = 82.3
```

### 3. Press Intensity (0-100)
```python
# tactics.defensive.pressing_intensity (0-10 스케일) * 10
# 예: Arsenal pressing_intensity = 9
# press_intensity = 9 * 10 = 90.0
```

### 4. Buildup Style
```python
# tactics.offensive.buildup_style 매핑
# "short_passing" → "possession"
# "long_ball" → "direct"
# "mixed" → "mixed"
```

---

## 🎯 핵심 교훈

### 1. 데이터 구조 사전 확인
- ✅ 새 기능을 추가하기 전에 실제 데이터 모델 확인
- ✅ `EnrichedTeamInput` 클래스 정의를 먼저 읽어야 함
- ❌ 가정에 기반한 코딩 금지

### 2. Type Safety
```python
# Python type hints를 사용하면 IDE에서 미리 에러를 잡을 수 있음
def convert_to_team_info(team_data: EnrichedTeamInput) -> TeamInfo:
    return TeamInfo(
        attack_strength=team_data.team_strength.attack,  # ← IDE가 에러 표시!
        ...
    )
```

### 3. 계층적 데이터 구조 이해
```
EnrichedTeamInput (최상위)
  ├─ lineup (11명 선수 raw 데이터)
  ├─ tactics (전술 raw 데이터)
  ├─ team_strength_ratings (팀 전력 평가)
  └─ derived_strengths (계산된 값) ← AI/시뮬레이션에서 사용!
       ├─ attack_strength (선수 속성에서 계산)
       ├─ defense_strength (선수 속성에서 계산)
       ├─ press_intensity (tactics에서 변환)
       └─ buildup_style (tactics에서 변환)
```

---

## 📝 체크리스트

- [x] `EnrichedTeamInput` 실제 구조 확인
- [x] `DerivedTeamStrengths` 속성 이해
- [x] `enriched_simulation_service.py` 수정
- [x] 백엔드 재시작
- [x] 시뮬레이션 테스트 실행
- [ ] 에러 없이 90분 시뮬레이션 완료 확인

---

**수정일**: 2025-10-17
**수정자**: Claude Code (AI Assistant)
**상태**: ✅ 수정 완료, 재테스트 필요
