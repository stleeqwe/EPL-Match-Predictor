# 사용자 Domain Input 활용 매핑

**작성일**: 2025-10-18
**목적**: Phase 2-5 재설계에서 사용자 도메인 데이터가 어디서 어떻게 활용되는지 상세 분석

---

## 1. 사용자 Domain Input 구조 (EnrichedTeamInput)

### 1.1 팀 레벨 데이터

```python
EnrichedTeamInput:
    name: str                                   # "Arsenal", "Liverpool" 등
    formation: str                              # "4-3-3", "4-2-3-1" 등 (사용자 선택)

    # 포메이션 전술 특성 (formation_tactics.json에서 매핑)
    formation_tactics: FormationTactics
        ├─ formation: str                       # "4-3-3"
        ├─ name: str                            # "공격형 4-3-3"
        ├─ style: str                           # "공격적", "수비적", "균형잡힌"
        ├─ buildup: str                         # "빠른 패스 기반 빌드업..."
        ├─ pressing: str                        # "높은 라인에서 적극적 압박..."
        ├─ space_utilization: str               # "측면 공간 활용..."
        ├─ strengths: List[str]                 # ["높은 공격력", "빠른 전환"]
        └─ weaknesses: List[str]                # ["수비 취약성", "중앙 약함"]

    # 팀 전력 평가 (team_strength.json - 사용자 평가)
    team_strength_ratings: TeamStrengthRatings
        ├─ tactical_understanding: float        # 0.0-5.0
        ├─ positioning_balance: float           # 0.0-5.0
        └─ buildup_quality: float               # 0.0-5.0

    # 팀 전략 코멘터리 (사용자 입력, 핵심!)
    team_strategy_commentary: str
        # 예: "Arsenal은 측면 공격을 선호하며 빠른 역습에 강하다..."

    # 계산된 팀 전력 (11명 선수 속성에서 자동 계산)
    derived_strengths: DerivedTeamStrengths
        ├─ attack_strength: float               # 0-100 (공격수 속성 평균)
        ├─ defense_strength: float              # 0-100 (수비수 속성 평균)
        ├─ midfield_control: float              # 0-100 (미드필더 속성 평균)
        └─ physical_intensity: float            # 0-100 (전체 선수 체력/속도)
```

### 1.2 선수 레벨 데이터 (11명)

```python
lineup: Dict[str, EnrichedPlayerInput]          # {"GK": player1, "LB": player2, ...}

EnrichedPlayerInput (각 선수):
    player_id: int
    name: str                                   # "Leandro Trossard"
    position: str                               # "Winger" (풀네임)
    sub_position: str                           # "LW" (약자)

    # 포지션별 속성 (10-12개, 사용자 평가)
    ratings: Dict[str, float]
        # 예시 - Winger:
        ├─ speed_dribbling: 4.5
        ├─ crossing_accuracy: 4.0
        ├─ cutting_in: 4.25
        ├─ shooting_finishing: 3.75
        ├─ positioning_off_the_ball: 4.0
        ├─ defensive_workrate: 3.5
        ├─ passing_vision: 4.0
        ├─ physical_stamina: 4.0
        ├─ technical_ball_control: 4.25
        ├─ decision_making: 4.0
        ├─ teamwork_pressing: 3.75
        └─ creativity: 4.5

    # 선수별 코멘터리 (사용자 입력, 핵심!)
    user_commentary: str
        # 예: "매우 창의적인 윙어로 측면 돌파와 컷인 슈팅에 강함..."

    # 계산된 값
    overall_rating: float                       # ratings의 평균 (0-5.0)
```

---

## 2. Model 1: Poisson-Rating Hybrid 활용

### 사용하는 데이터

```python
# INPUT
home_team: EnrichedTeamInput
away_team: EnrichedTeamInput

# 사용하는 필드:
✓ home_team.derived_strengths.attack_strength       # 0-100
✓ home_team.derived_strengths.defense_strength      # 0-100
✓ away_team.derived_strengths.attack_strength
✓ away_team.derived_strengths.defense_strength

✓ home_team.formation                               # "4-3-3"
✓ away_team.formation                               # "4-3-3"

✓ home_team.formation_tactics.style                 # "공격적"
✓ home_team.formation_tactics.pressing              # "높은 압박"
✓ away_team.formation_tactics.style
✓ away_team.formation_tactics.pressing
```

### 활용 방식

```python
# 1. Attack/Defense Rating 직접 사용
home_attack = home_team.derived_strengths.attack_strength  # 60.8
away_defense = away_team.derived_strengths.defense_strength  # 78.8

# 2. Formation Compatibility 계산
def calculate_formation_compatibility(home_tactics, away_tactics):
    # 전술 스타일 조합으로 궁합도 계산
    if home_tactics.style == "공격적" and away_tactics.style == "공격적":
        return 1.15  # 고득점 경기 예상
    elif home_tactics.style == "수비적" and away_tactics.style == "공격적":
        return 0.9   # 전술 충돌
    # ...

formation_factor = calculate_formation_compatibility(
    home_team.formation_tactics,
    away_team.formation_tactics
)

# 3. Expected Goals (Poisson λ) 계산
λ_home = (
    (home_attack / 100) *           # 사용자 데이터!
    (1 - away_defense / 100) *      # 사용자 데이터!
    formation_factor *              # 사용자 데이터 기반 계산!
    EPL_AVG_GOALS *                # 베이스라인 (참고만)
    1.1                            # 홈 어드밴티지
)

# 4. Poisson Distribution으로 스코어 확률 도출
P_matrix[(1, 2)] = poisson.pmf(1, λ_home) * poisson.pmf(2, λ_away)
```

### OUTPUT

```python
{
    "lambda_home": 1.03,           # 사용자 데이터 기반!
    "lambda_away": 1.19,           # 사용자 데이터 기반!
    "probabilities": {
        "home_win": 0.28,
        "draw": 0.25,
        "away_win": 0.47           # Liverpool 우세 (데이터 반영)
    }
}
```

---

## 3. Model 2: Zone Dominance Matrix (9구역) 활용

### 사용하는 데이터

```python
# INPUT
home_team.lineup: Dict[str, EnrichedPlayerInput]  # 11명
away_team.lineup: Dict[str, EnrichedPlayerInput]  # 11명

# 사용하는 필드 (각 선수별):
✓ player.sub_position        # "LB", "CB", "LW", "ST" → 구역 매핑용
✓ player.overall_rating      # 4.09 → 구역 지배율 계산용
✓ player.ratings             # 세부 속성 (특정 구역 강도 계산용)
```

### 활용 방식

```python
# 1. Position → Zone Mapping
POSITION_TO_ZONES = {
    'LB': ['LD', 'LM'],         # Left Back → Left Defense + Left Midfield
    'CB': ['CD'],                # Center Back → Center Defense
    'DM': ['CM', 'CD'],          # Defensive Mid → Center Mid + drops back
    'LW': ['LA', 'LM'],          # Left Wing → Left Attack + Left Mid
    'ST': ['CA'],                # Striker → Center Attack
    # ... 전체 포지션 매핑
}

# 2. 구역별 지배율 계산
for zone in ['LD', 'CD', 'RD', 'LM', 'CM', 'RM', 'LA', 'CA', 'RA']:
    home_presence = 0
    for pos, player in home_team.lineup.items():
        if zone in POSITION_TO_ZONES.get(player.sub_position, []):
            # 사용자 데이터 (overall_rating) 직접 사용!
            weight = 1.0 if primary_zone else 0.5
            home_presence += player.overall_rating * weight

    # 정규화
    zone_control[zone] = {
        'home': home_presence / (home_presence + away_presence),
        'away': away_presence / (home_presence + away_presence)
    }

# 3. 공격 구역 지배율 → xG 변환
attack_zones = ['LA', 'CA', 'RA']
home_attack_control = sum(zone_control[z]['home'] for z in attack_zones) / 3

xG_home = home_attack_control * BASE_XG * 2  # 사용자 데이터 기반!
```

### OUTPUT

```python
{
    "zone_control": {
        "CA": {"home": 0.38, "away": 0.62},  # Isak (4.02) dominates!
        "LA": {"home": 0.45, "away": 0.55},  # Trossard (4.09) vs Liverpool
        # ... 9개 구역
    },
    "xG": {
        "xG_home": 1.15,        # 사용자 선수 rating 기반!
        "xG_away": 1.56         # 사용자 선수 rating 기반!
    }
}
```

---

## 4. Model 3: Key Player Weighted 활용

### 사용하는 데이터

```python
# INPUT
home_team.lineup: Dict[str, EnrichedPlayerInput]
away_team.lineup: Dict[str, EnrichedPlayerInput]

# 사용하는 필드 (각 선수별):
✓ player.overall_rating           # 4.02 → 영향력 base
✓ player.sub_position             # "ST" → position_weight (공격수 1.5x)
✓ player.ratings                  # 세부 속성 → key_strengths 추출
✓ player.get_key_strengths(3)     # 상위 3개 속성
```

### 활용 방식

```python
# 1. 선수별 영향력 지수 (0-10)
for pos, player in team.lineup.items():
    base = player.overall_rating  # 사용자 데이터!

    # Position weight
    position_weights = {
        'ST': 1.5,   # 공격수 높은 가중치
        'LW': 1.3,
        'CM': 1.0,
        'CB': 0.7,
        'GK': 0.6
    }
    weight = position_weights.get(player.sub_position, 1.0)

    # Calculate influence
    influence = (base / 5.0) * 10 * weight  # 사용자 데이터 기반!

    # Key strengths bonus
    top_attrs = player.get_key_strengths(3)  # 사용자 ratings 기반!
    avg_top = sum(player.ratings[a] for a in top_attrs) / 3
    if avg_top > 4.5:  # Elite attributes
        influence *= 1.15

# 2. 상대 취약 구역 vs 핵심 선수 교차 분석
# Zone control (Model 2) + Player influence (Model 3) 결합
for player in team.lineup.values():
    player_zones = POSITION_TO_ZONES[player.sub_position]
    weak_zones = [z for z in zones if opponent_control[z] < 0.45]

    if set(player_zones) & set(weak_zones):
        # 이 선수가 상대 취약 구역에서 활동!
        advantage = player.overall_rating * len(overlap)  # 사용자 데이터!
```

### OUTPUT

```python
{
    "player_influences": {
        "Alexander Isak": {
            "influence": 8.5,        # 사용자 rating 4.02 기반!
            "position": "ST",
            "top_attributes": ["shooting_finishing", "positioning", "pace"]
        },
        "Leandro Trossard": {
            "influence": 7.2,        # 사용자 rating 4.09 기반!
            "position": "LW"
        }
    },
    "matchup_advantages": {
        "home_advantages": [
            {
                "player": "Leandro Trossard",  # 사용자 데이터!
                "zones": ["LA"],
                "expected_impact": 0.82
            }
        ]
    }
}
```

---

## 5. AI Scenario Generation 활용

### 사용하는 데이터 (스토리 생성용)

```python
# INPUT
ensemble_results: dict           # Model 1-3의 수학적 분석 결과
home_team: EnrichedTeamInput
away_team: EnrichedTeamInput

# 사용하는 필드:
✓ team.team_strategy_commentary     # 팀 전략 코멘터리 (핵심!)
✓ player.user_commentary            # 선수별 코멘터리 (핵심!)
✓ formation_tactics.strengths       # 포메이션 강점
✓ formation_tactics.weaknesses      # 포메이션 약점
```

### 활용 방식

```python
# AI Prompt 구성
user_prompt = f"""
# Mathematical Analysis Results (Model 1-3의 결과)
- Home win: 24%
- Away win: 55%  ← Liverpool 우세 (사용자 데이터 반영)
- xG: Home 1.15, Away 1.56
- Zone: CA 62% away control (Isak 활동 구역)
- Key player: Isak (8.5), Trossard (7.2)

# User Domain Knowledge (스토리 생성용만!)

## Team Strategies
- Arsenal: {home_team.team_strategy_commentary}
  예: "측면 공격을 선호하며 빠른 역습에 강하다..."

- Liverpool: {away_team.team_strategy_commentary}
  예: "중앙 지배를 통한 공격 전개를 선호..."

## Key Players Commentary
- Alexander Isak (ST, Liverpool):
  {isak.user_commentary}
  예: "높은 퀄리티의 중앙 공격수로 마무리가 뛰어남..."

- Leandro Trossard (LW, Arsenal):
  {trossard.user_commentary}
  예: "매우 창의적인 윙어로 측면 돌파와 컷인 슈팅에 강함..."

## Tactical Insights
- Formation strengths:
  Arsenal: {home_team.formation_tactics.strengths}
  예: ["빠른 측면 공격", "역습 능력"]

- Formation weaknesses:
  Arsenal: {home_team.formation_tactics.weaknesses}
  예: ["중앙 수비 취약", "높은 라인 위험"]

# Task
Generate 2-5 MOST LIKELY scenarios.
- Focus on 55% away win probability (수학적 분석)
- Use user commentary for NARRATIVE only (스토리텔링)
- Events should reflect mathematical advantages (zone/player)
"""
```

### AI 응답 예시 (사용자 데이터 반영)

```json
{
  "scenarios": [
    {
      "id": "MATH_001",
      "name": "리버풀 중앙 지배를 통한 승리",
      "expected_probability": 0.35,
      "reasoning": "Zone CA 62% away + Isak influence 8.5",
      "events": [
        {
          "minute_range": [20, 30],
          "type": "goal",
          "team": "away",
          "actor": "Alexander Isak",
          "probability_boost": 2.6,
          "reason": "높은 퀄리티의 중앙 공격수(user_commentary)가 중앙 지배 구역(zone analysis)에서 마무리"
          # ↑ 수학 + 사용자 commentary 결합!
        }
      ]
    },
    {
      "id": "MATH_002",
      "name": "아스날 측면 역습 승리",
      "expected_probability": 0.15,
      "reasoning": "Trossard 7.2 influence in LA zone",
      "events": [
        {
          "minute_range": [35, 45],
          "type": "wing_breakthrough",
          "team": "home",
          "actor": "Leandro Trossard",
          "probability_boost": 2.2,
          "reason": "매우 창의적인 윙어(user_commentary)가 측면 공간(formation_tactics.strengths)을 활용한 돌파"
          # ↑ 수학 + 사용자 commentary 결합!
        }
      ]
    }
  ]
}
```

---

## 6. Monte Carlo Validation 활용

### 사용하는 데이터

```python
# INPUT
scenarios: List[Scenario]              # AI 생성 시나리오
mathematical_analysis: dict            # Model 1-3 결과

# 시뮬레이션 파라미터 조정에 사용:
✓ zone_control (Model 2 결과)          # 구역별 shot distribution 조정
✓ player_influences (Model 3 결과)     # 선수별 probability_boost 조정
```

### 활용 방식

```python
# 3000회 시뮬레이션 시 수학 모델 결과 반영
for run in range(3000):
    match_params = base_params.copy()

    # 1. Zone dominance → shot distribution 조정
    for zone in ['LA', 'CA', 'RA']:
        # 사용자 선수 ratings 기반 zone_control 반영!
        match_params['home_shot_zones'][zone] *= zone_control[zone]['home']
        match_params['away_shot_zones'][zone] *= zone_control[zone]['away']

    # 2. Player influence → event probability 조정
    for event in scenario.events:
        if event.actor == "Alexander Isak":
            # 사용자 rating 기반 influence (8.5) 반영!
            influence = player_influences["Alexander Isak"]["influence"]
            event.probability_boost *= (influence / 10.0)  # 0.85x

    # 시뮬레이션 실행
    result = engine.simulate(match_params, scenario)

# 수렴 확률 도출 (사용자 데이터가 반영된 결과!)
convergence_prob = {
    'away_win': 0.57,  # Liverpool 우세 (사용자 데이터 반영)
    'draw': 0.23,
    'home_win': 0.20
}
```

---

## 7. 전체 데이터 흐름 요약

```
┌─────────────────────────────────────────────────────────────┐
│ 사용자 Domain Input (EnrichedTeamInput)                     │
│                                                              │
│ ├─ derived_strengths (attack: 60.8, defense: 79.6)         │
│ ├─ formation ("4-3-3")                                      │
│ ├─ formation_tactics (style: "공격적", strengths/weaknesses)│
│ ├─ lineup (11명)                                            │
│ │   ├─ player.overall_rating (4.09)                        │
│ │   ├─ player.ratings (12개 속성)                          │
│ │   ├─ player.sub_position ("LW")                          │
│ │   └─ player.user_commentary ("창의적 윙어...")          │
│ └─ team_strategy_commentary ("측면 공격 선호...")          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Model 1: Poisson-Rating                                     │
│  사용: derived_strengths, formation_tactics                 │
│  출력: λ_home=1.03, λ_away=1.19, P(away_win)=47%          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Model 2: Zone Dominance (9구역)                             │
│  사용: lineup (11명 position + overall_rating)              │
│  출력: CA 62% away, xG_home=1.15, xG_away=1.56            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Model 3: Key Player                                         │
│  사용: lineup (overall_rating + ratings)                    │
│  출력: Isak 8.5 influence, Trossard 7.2                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Ensemble: 가중 평균 (0.4/0.3/0.3)                           │
│  출력: Home 24%, Draw 21%, Away 55%                         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ AI Scenario Generation                                      │
│  수학 결과 + user_commentary + team_strategy_commentary     │
│  출력: 2-5개 시나리오 (Away win 중심, 스토리 포함)         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Monte Carlo Validation (3000회)                             │
│  수학 모델 결과 반영 (zone_control, player_influence)       │
│  출력: 수렴 확률 (Away 57%, Draw 23%, Home 20%)            │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. 핵심 정리

### 사용자 데이터가 확률 계산에 사용되는 부분 (수학적)

| 데이터                          | 활용 모델      | 용도                        |
|---------------------------------|----------------|----------------------------|
| `derived_strengths.attack`      | Model 1        | Poisson λ 계산             |
| `derived_strengths.defense`     | Model 1        | Poisson λ 계산             |
| `formation_tactics.style`       | Model 1        | Formation compatibility    |
| `player.overall_rating`         | Model 2, 3     | Zone 지배율, Influence     |
| `player.sub_position`           | Model 2, 3     | Zone 매핑, Position weight |
| `player.ratings`                | Model 2, 3     | Key strengths, Zone 강도   |

### 사용자 데이터가 스토리 생성에 사용되는 부분 (narrative)

| 데이터                          | 활용 단계              | 용도                    |
|---------------------------------|------------------------|------------------------|
| `player.user_commentary`        | AI Scenario Generation | 선수별 스토리 생성     |
| `team_strategy_commentary`      | AI Scenario Generation | 팀 전략 narrative      |
| `formation_tactics.strengths`   | AI Scenario Generation | 전술 강점 설명         |
| `formation_tactics.weaknesses`  | AI Scenario Generation | 전술 약점 설명         |

### 100% 사용자 데이터 기반

```
✓ 확률: 사용자 선수 ratings → derived_strengths → Model 1-3 → 확률
✓ 스토리: 사용자 commentary → AI → narrative
✓ 검증: 확률 기반 시뮬레이션 → 수렴

NO MORE:
✗ EPL 평균 강제
✗ 7개 템플릿
✗ 편향 조정
```

---

## 9. 예시: Arsenal vs Liverpool

### 입력 (사용자 데이터)

```python
Arsenal:
  derived_strengths: attack=60.8, defense=79.6
  formation: "4-3-3"
  formation_tactics: style="공격적"
  lineup:
    - Trossard (LW): overall=4.09, speed_dribbling=4.5
    - commentary: "창의적 윙어"
  team_strategy: "측면 공격 선호"

Liverpool:
  derived_strengths: attack=80.5, defense=78.8
  lineup:
    - Isak (ST): overall=4.02, shooting_finishing=4.5
    - commentary: "마무리 뛰어남"
```

### 출력 (사용자 데이터 반영)

```python
Model 1: Away win 47% (공격력 차이 19.7 반영)
Model 2: xG_away 1.56 > xG_home 1.15 (선수 rating 반영)
Model 3: Isak 8.5 influence (rating 4.02 반영)
Ensemble: Away win 55% (데이터 기반!)

AI Scenarios:
  - "Isak 중앙 돌파 승리" (35%) ← 수학 + commentary
  - "박빙 무승부" (21%)
  - "Trossard 측면 역습" (15%) ← 수학 + commentary

Validation: Away 57% (수렴, 사용자 데이터 반영)
```

사용자 도메인 데이터가 **확률 계산**과 **스토리 생성** 양쪽에 모두 100% 반영됩니다!
