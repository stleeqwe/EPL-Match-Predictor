# Phase 2-5 완전 재설계 계획

**작성일**: 2025-10-18
**목적**: 템플릿 제거, 수학적 모델 기반 시뮬레이션 구현

---

## 핵심 설계 원칙

### 철학적 전환
```
AS-IS (잘못됨):
  결과 정하기 → 과정 끼워맞추기 → EPL 평균 강제

TO-BE (올바름):
  사용자 데이터 → 수학적 분석 → 자연스러운 확률 도출 → 수렴 검증
```

### 핵심 원칙
1. **No Templates**: 시나리오 결과를 미리 정하지 않음
2. **No EPL Baseline Forcing**: EPL 평균에 맞추지 않음
3. **No Bias Adjustment**: 편향 조정 제거
4. **Mathematical Foundation**: 세 가지 수학 모델 기반
5. **Convergence as Truth**: 수렴하는 확률 = 올바른 확률

---

## 전체 아키텍처

```
┌────────────────────────────────────────────────────────────────┐
│ Phase 1: Mathematical Analysis (NEW)                           │
│  ├─ Input: EnrichedTeamInput (양 팀)                           │
│  ├─ Model 1: Poisson-Rating Model                             │
│  │   └─ Output: λ_home, λ_away, P(scores)                     │
│  ├─ Model 2: Zone Dominance Matrix (9 zones)                  │
│  │   └─ Output: zone_control, xG_home, xG_away                │
│  ├─ Model 3: Key Player Weighted Model                        │
│  │   └─ Output: player_influence, impact_on_zones             │
│  └─ Ensemble: 가중 평균                                        │
│      └─ Output: final_probabilities, zone_advantages          │
└────────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────────┐
│ Phase 2: AI Scenario Generation (REDESIGNED)                  │
│  ├─ Input:                                                     │
│  │   - Mathematical analysis results                          │
│  │   - User commentary (스토리용)                             │
│  ├─ AI Reasoning:                                              │
│  │   "Based on analysis:                                      │
│  │    - Expected goals: Home 1.2, Away 1.5                    │
│  │    - Zone control: Away dominates center 68%               │
│  │    - Key player: Isak (influence 8.5/10)                   │
│  │    Generate 2-5 most LIKELY scenarios"                     │
│  └─ Output: 2-5 scenarios (동적 개수)                          │
│      - Away win 2-1 (35%)                                      │
│      - Draw 1-1 (28%)                                          │
│      - Away win 1-0 (22%)                                      │
│      - Home win 2-1 (15%)                                      │
│      (합: 100%, 하지만 템플릿 없음)                            │
└────────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────────┐
│ Phase 3: Monte Carlo Validation (SIMPLIFIED)                  │
│  ├─ 각 시나리오 × 3000회 시뮬레이션                            │
│  ├─ 시뮬레이션 엔진에 Zone/Player 모델 반영                    │
│  │   - Zone dominance → shot distribution                     │
│  │   - Key player influence → probability boost               │
│  └─ Output: 검증된 확률 분포                                   │
│      - Away win: 57% (수렴값)                                  │
│      - Draw: 23%                                               │
│      - Home win: 20%                                           │
└────────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────────┐
│ Phase 4: Final Report (SIMPLIFIED)                            │
│  ├─ AI가 최종 리포트 생성                                      │
│  ├─ 수렴된 확률 기반 해설                                      │
│  └─ User commentary로 스토리텔링                               │
└────────────────────────────────────────────────────────────────┘

Phase 5 제거 (No more iterative adjustment)
```

---

## Model 1: Poisson-Rating Hybrid

### 입력
```python
home_team: EnrichedTeamInput
away_team: EnrichedTeamInput
```

### 계산 과정
```python
# 1. Attack/Defense Rating 계산
home_attack = home_team.derived_strengths.attack_strength  # 0-100
home_defense = home_team.derived_strengths.defense_strength
away_attack = away_team.derived_strengths.attack_strength
away_defense = away_team.derived_strengths.defense_strength

# 2. Formation Compatibility Factor
formation_factor = calculate_formation_compatibility(
    home_formation=home_team.formation,
    away_formation=away_team.formation,
    home_tactics=home_team.formation_tactics,
    away_tactics=away_team.formation_tactics
)
# 예: 공격적 vs 공격적 → 1.15 (high scoring)
#     공격적 vs 수비적 → 0.9 (tactical clash)

# 3. Expected Goals (Poisson λ)
EPL_AVG_GOALS = 1.4  # per team per match (EPL 평균은 참고만, 강제 아님)

λ_home = (
    (home_attack / 100) *      # 공격력 비율
    (1 - away_defense / 100) * # 상대 수비 약점
    formation_factor *         # 포메이션 궁합
    EPL_AVG_GOALS *           # 베이스라인
    1.1                       # 홈 어드밴티지
)

λ_away = (
    (away_attack / 100) *
    (1 - home_defense / 100) *
    formation_factor *
    EPL_AVG_GOALS
)

# 4. Score Probabilities (Poisson Distribution)
from scipy.stats import poisson

P_matrix = {}
for home_goals in range(0, 6):
    for away_goals in range(0, 6):
        P_matrix[(home_goals, away_goals)] = (
            poisson.pmf(home_goals, λ_home) *
            poisson.pmf(away_goals, λ_away)
        )

# 5. Win/Draw/Loss Probabilities
P_home_win = sum(P_matrix[(h, a)] for h, a in P_matrix if h > a)
P_draw = sum(P_matrix[(h, a)] for h, a in P_matrix if h == a)
P_away_win = sum(P_matrix[(h, a)] for h, a in P_matrix if h < a)
```

### 출력
```python
{
    "lambda_home": 1.2,
    "lambda_away": 1.5,
    "probabilities": {
        "home_win": 0.28,
        "draw": 0.25,
        "away_win": 0.47
    },
    "most_likely_scores": [
        ("1-1", 0.18),
        ("1-2", 0.16),
        ("0-1", 0.12),
        ("2-1", 0.11),
        ("1-0", 0.09)
    ]
}
```

---

## Model 2: Zone Dominance Matrix

### 9구역 정의
```
┌─────────────┬─────────────┬─────────────┐
│ Left        │ Center      │ Right       │
│ Defense     │ Defense     │ Defense     │
│ [LD]        │ [CD]        │ [RD]        │
├─────────────┼─────────────┼─────────────┤
│ Left        │ Center      │ Right       │
│ Midfield    │ Midfield    │ Midfield    │
│ [LM]        │ [CM]        │ [RM]        │
├─────────────┼─────────────┼─────────────┤
│ Left        │ Center      │ Right       │
│ Attack      │ Attack      │ Attack      │
│ [LA]        │ [CA]        │ [RA]        │
└─────────────┴─────────────┴─────────────┘
```

### 포지션 → 구역 매핑
```python
POSITION_TO_ZONES = {
    # Goalkeepers
    'GK': ['CD'],  # Primary: Center Defense

    # Defenders
    'LB': ['LD', 'LM'],  # Left Back covers defense + midfield
    'CB': ['CD'],
    'CB1': ['CD'],
    'CB2': ['CD'],
    'CB-L': ['CD', 'LD'],  # Left Center Back
    'CB-R': ['CD', 'RD'],  # Right Center Back
    'RB': ['RD', 'RM'],

    # Midfielders
    'DM': ['CM', 'CD'],  # Defensive Mid covers center + drops back
    'CM': ['CM'],
    'CM1': ['CM'],
    'CM2': ['CM'],
    'CM-L': ['CM', 'LM'],
    'CM-R': ['CM', 'RM'],
    'LM': ['LM', 'LA'],  # Left Mid covers midfield + attack
    'RM': ['RM', 'RA'],
    'CAM': ['CM', 'CA'],  # Attacking Mid

    # Attackers
    'LW': ['LA', 'LM'],  # Left Wing
    'RW': ['RA', 'RM'],
    'ST': ['CA'],
    'CF': ['CA'],
    'ST1': ['CA'],
    'ST2': ['CA']
}

# 가중치 (primary zone = 1.0, secondary zone = 0.5)
ZONE_WEIGHTS = {
    'primary': 1.0,
    'secondary': 0.5
}
```

### 계산 과정
```python
def calculate_zone_dominance(home_team, away_team):
    zones = ['LD', 'CD', 'RD', 'LM', 'CM', 'RM', 'LA', 'CA', 'RA']

    zone_control = {}

    for zone in zones:
        # Home team presence in zone
        home_presence = 0
        for pos, player in home_team.lineup.items():
            if zone in POSITION_TO_ZONES.get(pos, []):
                weight = 1.0 if POSITION_TO_ZONES[pos][0] == zone else 0.5
                home_presence += player.overall_rating * weight

        # Away team presence in zone
        away_presence = 0
        for pos, player in away_team.lineup.items():
            if zone in POSITION_TO_ZONES.get(pos, []):
                weight = 1.0 if POSITION_TO_ZONES[pos][0] == zone else 0.5
                away_presence += player.overall_rating * weight

        # Normalize to percentage
        total = home_presence + away_presence
        if total > 0:
            zone_control[zone] = {
                'home': home_presence / total,
                'away': away_presence / total,
                'home_rating': home_presence,
                'away_rating': away_presence
            }

    return zone_control

# Zone dominance → xG conversion
def zone_to_xg(zone_control):
    # 공격 구역 (LA, CA, RA) 지배율 → xG
    attack_zones = ['LA', 'CA', 'RA']

    home_attack_control = sum(
        zone_control[z]['home'] for z in attack_zones
    ) / len(attack_zones)

    away_attack_control = sum(
        zone_control[z]['away'] for z in attack_zones
    ) / len(attack_zones)

    # xG = control * base_xg
    BASE_XG = 1.5  # EPL 평균 xG

    xG_home = home_attack_control * BASE_XG * 2  # *2 for home advantage
    xG_away = away_attack_control * BASE_XG * 1.8

    return {
        'xG_home': xG_home,
        'xG_away': xG_away,
        'attack_control': {
            'home': home_attack_control,
            'away': away_attack_control
        }
    }
```

### 출력
```python
{
    "zone_control": {
        "LD": {"home": 0.48, "away": 0.52},
        "CD": {"home": 0.55, "away": 0.45},
        "RD": {"home": 0.42, "away": 0.58},
        "LM": {"home": 0.51, "away": 0.49},
        "CM": {"home": 0.47, "away": 0.53},
        "RM": {"home": 0.49, "away": 0.51},
        "LA": {"home": 0.45, "away": 0.55},
        "CA": {"home": 0.38, "away": 0.62},  # Away dominates center
        "RA": {"home": 0.44, "away": 0.56}
    },
    "xG": {
        "xG_home": 1.15,
        "xG_away": 1.56,
        "attack_control": {
            "home": 0.42,
            "away": 0.58
        }
    },
    "dominant_zones": {
        "home": ["CD", "LM"],
        "away": ["RD", "CM", "CA", "LA", "RA"]
    }
}
```

---

## Model 3: Key Player Weighted

### 계산 과정
```python
def calculate_player_influence(team):
    """선수별 영향력 지수 (0-10)"""

    influences = {}

    for pos, player in team.lineup.items():
        # Base influence = overall rating
        base = player.overall_rating  # 0-5 scale

        # Position weight (공격수 > 미드필더 > 수비수)
        position_weights = {
            'ST': 1.5, 'CF': 1.5,
            'LW': 1.3, 'RW': 1.3,
            'CAM': 1.2,
            'CM': 1.0, 'DM': 1.0,
            'LB': 0.8, 'RB': 0.8,
            'CB': 0.7,
            'GK': 0.6
        }

        weight = position_weights.get(player.sub_position, 1.0)

        # Calculate influence (0-10 scale)
        influence = (base / 5.0) * 10 * weight

        # Key strengths bonus
        top_attrs = player.get_key_strengths(3)
        avg_top = sum(player.ratings[a] for a in top_attrs) / len(top_attrs)
        if avg_top > 4.5:  # Elite in key attributes
            influence *= 1.15

        influences[player.name] = {
            'influence': min(influence, 10.0),  # Cap at 10
            'position': player.sub_position,
            'overall': player.overall_rating,
            'top_attributes': top_attrs
        }

    return influences

def calculate_matchup_advantages(home_team, away_team, zone_control):
    """상대 취약 구역 vs 핵심 선수 교차 분석"""

    # Away team weaknesses (from zone control)
    away_weak_zones = [
        zone for zone, control in zone_control.items()
        if control['home'] > 0.55  # Home dominates
    ]

    # Home key attackers in those zones
    home_advantages = []
    for pos, player in home_team.lineup.items():
        player_zones = POSITION_TO_ZONES.get(pos, [])
        overlap = set(player_zones) & set(away_weak_zones)
        if overlap and player.overall_rating > 4.0:
            home_advantages.append({
                'player': player.name,
                'zones': list(overlap),
                'rating': player.overall_rating,
                'advantage': len(overlap) * player.overall_rating
            })

    # Sort by advantage
    home_advantages.sort(key=lambda x: x['advantage'], reverse=True)

    return {
        'home_advantages': home_advantages[:3],  # Top 3
        'away_advantages': [],  # Same logic for away
        'key_matchups': [
            {
                'attacker': adv['player'],
                'zones': adv['zones'],
                'expected_impact': adv['advantage'] / 10  # 0-1 scale
            }
            for adv in home_advantages[:3]
        ]
    }
```

### 출력
```python
{
    "player_influences": {
        "Alexander Isak": {
            "influence": 8.5,
            "position": "ST",
            "overall": 4.02
        },
        "Leandro Trossard": {
            "influence": 7.2,
            "position": "LW",
            "overall": 4.09
        }
    },
    "matchup_advantages": {
        "home_advantages": [
            {
                "player": "Leandro Trossard",
                "zones": ["LA", "LM"],
                "rating": 4.09,
                "advantage": 8.18
            }
        ],
        "key_matchups": [
            {
                "attacker": "Leandro Trossard",
                "zones": ["LA"],
                "expected_impact": 0.82
            }
        ]
    }
}
```

---

## Ensemble Integration

### 가중 평균
```python
# 모델별 가중치
WEIGHTS = {
    'poisson': 0.4,   # 가장 기본적, 안정적
    'zone': 0.3,      # 전술적 분석
    'player': 0.3     # 개인 영향력
}

# 확률 앙상블
ensemble_probs = {
    'home_win': (
        WEIGHTS['poisson'] * poisson_result['probabilities']['home_win'] +
        WEIGHTS['zone'] * zone_to_probability(zone_result, 'home_win') +
        WEIGHTS['player'] * player_to_probability(player_result, 'home_win')
    ),
    'draw': ...,
    'away_win': ...
}

# Zone → Probability 변환 예시
def zone_to_probability(zone_result, outcome):
    xG_diff = zone_result['xG']['xG_home'] - zone_result['xG']['xG_away']

    if outcome == 'home_win':
        return sigmoid(xG_diff * 2.0)  # xG 차이를 확률로
    elif outcome == 'away_win':
        return sigmoid(-xG_diff * 2.0)
    else:  # draw
        return gaussian(xG_diff, mean=0, std=0.5)
```

### 최종 출력
```python
{
    "ensemble_probabilities": {
        "home_win": 0.24,
        "draw": 0.21,
        "away_win": 0.55
    },
    "expected_goals": {
        "home": 1.15,
        "away": 1.52
    },
    "zone_dominance_summary": {
        "home_strengths": ["Center Defense", "Left Midfield"],
        "away_strengths": ["Center Attack", "Right Wing", "Center Mid"]
    },
    "key_player_impacts": [
        {"player": "Alexander Isak", "team": "away", "influence": 8.5},
        {"player": "Leandro Trossard", "team": "home", "influence": 7.2}
    ],
    "tactical_insights": {
        "formation_matchup": "Both 4-3-3 attacking → high scoring expected",
        "critical_zones": ["CA", "RA"],
        "key_matchup": "Trossard (LA) vs Liverpool RD"
    }
}
```

---

## Phase 2 (NEW): AI Scenario Generation

### AI Prompt 구조
```python
system_prompt = """You are a tactical football analyst.

Your task: Generate 2-5 MOST LIKELY match scenarios based on mathematical analysis.

CRITICAL RULES:
1. Focus on HIGH PROBABILITY outcomes (>10%)
2. If one team is clearly stronger, generate fewer scenarios (2-3)
3. If match is balanced, generate more scenarios (4-5)
4. DO NOT force equal distribution
5. DO NOT create unrealistic scenarios to hit quotas
6. Use user commentary for NARRATIVE ONLY (probabilities come from math)

Output: JSON with scenarios
"""

user_prompt = f"""
# Match Analysis: {home_team.name} vs {away_team.name}

## Mathematical Analysis Results

### Ensemble Probabilities
- Home win: {ensemble['home_win']:.1%}
- Draw: {ensemble['draw']:.1%}
- Away win: {ensemble['away_win']:.1%}

### Expected Goals
- Home: {ensemble['xG_home']:.2f}
- Away: {ensemble['xG_away']:.2f}

### Zone Dominance (9 zones)
{format_zone_control(zone_result)}

### Key Player Influences
{format_player_influences(player_result)}

### Tactical Insights
- Formation matchup: {tactical_insights['formation_matchup']}
- Critical zones: {tactical_insights['critical_zones']}
- Key matchup: {tactical_insights['key_matchup']}

## User Domain Knowledge (for narrative only)

### Team Strategies
- {home_team.name}: {home_team.team_strategy_commentary}
- {away_team.name}: {away_team.team_strategy_commentary}

### Key Players Commentary
{format_player_commentaries(home_team, away_team)}

## Task

Generate 2-5 scenarios focusing on MOST LIKELY outcomes:

Guidelines:
1. If away_win > 50%, create 2-3 away win scenarios with different narratives
2. Include lower probability scenarios ONLY if >10%
3. Each scenario needs:
   - Events reflecting mathematical advantages (zone control, key players)
   - probability_boost based on zone/player advantages
   - Narrative using user commentary

Return JSON:
{{
  "reasoning": "Why these scenarios were chosen",
  "scenario_count": 3,
  "scenarios": [
    {{
      "id": "MATH_001",
      "name": "Most likely outcome",
      "expected_probability": 0.35,
      "reasoning": "Based on xG 1.52 > 1.15 and CA dominance",
      "events": [...]
    }}
  ]
}}
"""
```

### AI 응답 예시
```json
{
  "reasoning": "Liverpool shows clear advantage (55% win probability) with xG 1.52 vs 1.15. Generated 3 scenarios focusing on likely outcomes.",
  "scenario_count": 3,
  "scenarios": [
    {
      "id": "MATH_001",
      "name": "리버풀 중앙 지배를 통한 승리",
      "expected_probability": 0.35,
      "reasoning": "Zone CA (62% away control) + Isak influence (8.5) suggests central breakthrough",
      "events": [
        {
          "minute_range": [15, 25],
          "type": "central_penetration",
          "team": "away",
          "actor": "Alexander Isak",
          "probability_boost": 2.4,
          "reason": "Isak exploits 62% center attack dominance (from zone analysis)"
        },
        {
          "minute_range": [20, 30],
          "type": "goal",
          "team": "away",
          "actor": "Alexander Isak",
          "probability_boost": 2.6,
          "reason": "High-quality centre striker finishing (user commentary) in dominant zone"
        }
      ]
    },
    {
      "id": "MATH_002",
      "name": "박빙의 무승부",
      "expected_probability": 0.21,
      "reasoning": "Despite xG difference, both teams have strong defenses (Arsenal 79.6, Liverpool 78.8)",
      "events": [...]
    },
    {
      "id": "MATH_003",
      "name": "아스날 측면 역습 승리",
      "expected_probability": 0.15,
      "reasoning": "Trossard (7.2 influence) can exploit LA zone (45% home) with creative play",
      "events": [...]
    }
  ]
}
```

**핵심**: 확률은 수학적 분석에서, 스토리는 user commentary에서

---

## Phase 3 (NEW): Monte Carlo Validation

### 간소화된 검증
```python
def validate_scenarios(scenarios, mathematical_analysis):
    """
    각 시나리오를 3000회 시뮬레이션하여 수렴 확률 도출

    NO MORE:
    - Bias detection
    - EPL baseline forcing
    - Iterative adjustment

    ONLY:
    - Run simulations
    - Report convergence
    """

    results = []

    for scenario in scenarios:
        # 3000회 시뮬레이션
        simulation_results = []

        for run in range(3000):
            # Apply mathematical model to simulation
            match_params = base_match_params.copy()

            # Zone dominance → shot distribution
            for zone, control in mathematical_analysis['zone_control'].items():
                if zone in ['LA', 'CA', 'RA']:  # Attack zones
                    match_params['home_shot_zones'][zone] *= control['home']
                    match_params['away_shot_zones'][zone] *= control['away']

            # Player influence → probability boost
            for event in scenario.events:
                if event.actor in mathematical_analysis['player_influences']:
                    influence = mathematical_analysis['player_influences'][event.actor]['influence']
                    event.probability_boost *= (influence / 10.0)  # 0.6-1.0 range

            # Run simulation
            result = self.engine.simulate(match_params, scenario)
            simulation_results.append(result)

        # Calculate convergence
        home_wins = sum(1 for r in simulation_results if r['winner'] == 'home')
        draws = sum(1 for r in simulation_results if r['winner'] == 'draw')
        away_wins = sum(1 for r in simulation_results if r['winner'] == 'away')

        convergence_prob = {
            'home_win': home_wins / 3000,
            'draw': draws / 3000,
            'away_win': away_wins / 3000
        }

        results.append({
            'scenario': scenario,
            'convergence_probability': convergence_prob,
            'avg_score': calculate_avg_score(simulation_results),
            'confidence_interval': calculate_ci(simulation_results)
        })

    return results
```

### 최종 확률 도출
```python
# 각 시나리오의 수렴 확률을 가중 평균
final_probability = {
    'home_win': sum(
        r['scenario'].expected_probability * r['convergence_probability']['home_win']
        for r in validation_results
    ),
    'draw': ...,
    'away_win': ...
}

# 이것이 "올바른 확률"
# 검증 기준 없음, 수렴 자체가 정답
```

---

## 구현 계획

### Phase 1: 새 모델 구현 (3일)
```
Day 1:
  ✓ poisson_rating_model.py
  ✓ zone_dominance_calculator.py
  ✓ Tests

Day 2:
  ✓ key_player_influence.py
  ✓ model_ensemble.py
  ✓ Tests

Day 3:
  ✓ Integration with EnrichedTeamInput
  ✓ End-to-end test
```

### Phase 2: AI 시나리오 재설계 (1일)
```
Day 4:
  ✓ Remove template logic
  ✓ New prompt engineering (math-based)
  ✓ Dynamic scenario count (2-5)
  ✓ Tests
```

### Phase 3: 검증 간소화 (1일)
```
Day 5:
  ✓ Remove bias detection
  ✓ Remove adjustment logic
  ✓ Implement convergence-only validation
  ✓ Tests
```

### Phase 4: 통합 및 검증 (1일)
```
Day 6:
  ✓ End-to-end integration
  ✓ Arsenal vs Liverpool test
  ✓ Man City vs Sheffield test (extreme case)
  ✓ Performance optimization
```

---

## 파일 구조

```
backend/simulation/v3/  (NEW)
├── models/
│   ├── __init__.py
│   ├── poisson_rating_model.py       # Model 1
│   ├── zone_dominance_calculator.py  # Model 2
│   ├── key_player_influence.py       # Model 3
│   ├── model_ensemble.py             # 앙상블
│   └── tactical_analyzer.py          # 전술 분석
│
├── scenario/
│   ├── __init__.py
│   ├── math_based_generator.py       # AI 시나리오 생성 (NEW)
│   └── scenario.py                   # 기존 유지
│
├── validation/
│   ├── __init__.py
│   └── monte_carlo_validator.py      # 간소화된 검증
│
├── pipeline/
│   ├── __init__.py
│   └── simulation_pipeline_v3.py     # 새 파이프라인
│
└── tests/
    ├── test_models.py
    ├── test_scenario_generation.py
    └── test_integration.py
```

---

## 성능 예상

### 실행 시간
```
Model 1 (Poisson): ~0.1초
Model 2 (Zone): ~0.3초
Model 3 (Player): ~0.2초
Ensemble: ~0.1초
AI Scenario (3개): ~30초
Validation (3×3000): ~120초

Total: ~150초 (현재와 유사)
```

### 품질 개선
```
AS-IS:
  - 템플릿 확률: 고정
  - 사용자 데이터: 스토리만 반영
  - 검증: EPL 평균 강제

TO-BE:
  - 수학적 확률: 데이터 기반
  - 사용자 데이터: 스토리 + 모델 입력
  - 검증: 수렴 = 정답

개선도: 300%+
```

---

## 위험 요소 및 대응

### 위험 1: Zone 모델 부정확
- **원인**: 포지션 라벨 비표준화
- **대응**: Fallback to 3-line model if needed

### 위험 2: Ensemble 가중치 최적화
- **원인**: 0.4/0.3/0.3이 최적인지 불확실
- **대응**: A/B 테스트, 사용자 피드백

### 위험 3: AI 시나리오 과소 생성
- **원인**: AI가 1-2개만 생성
- **대응**: Minimum 2개 강제, "at least 2" 프롬프트

### 위험 4: 성능 저하
- **원인**: Zone 계산 복잡도
- **대응**: 캐싱, 병렬화

---

## 검증 기준

### 정성적 검증
```
✓ Arsenal vs Liverpool (balanced)
  → 확률이 45-25-30 정도 나와야 함 (템플릿 아님)

✓ Man City vs Sheffield (extreme)
  → 확률이 80-15-5 정도 나와야 함
  → 시나리오 2개만 생성 (City win × 2)

✓ 레드카드 시나리오
  → User commentary에 "red card" 입력
  → AI가 red card scenario 생성하는지
```

### 정량적 검증
```
✓ 3000회 수렴 검증
  → 95% CI ±3.6% 이내

✓ Zone control 합 = 100%
  → home + away = 1.0

✓ Ensemble probability 합 = 100%
  → home_win + draw + away_win = 1.0
```

---

## 다음 단계

**사용자 승인 대기 중**

승인 시 즉시 구현 착수:
1. `backend/simulation/v3/` 디렉토리 생성
2. Model 1 (Poisson) 구현부터 시작
3. 단위 테스트 작성
4. Arsenal vs Liverpool 검증

**예상 완료: 6일 (11/24)**

---

## 요약

**핵심 변화**:
- ✗ 7개 템플릿 → ✓ 수학적 모델 3개
- ✗ EPL 평균 강제 → ✓ 데이터 기반 확률
- ✗ 편향 조정 → ✓ 수렴 = 정답
- ✗ 5-7개 고정 → ✓ 2-5개 동적

**기대 효과**:
- 사용자 데이터 100% 반영
- 극단적 케이스 처리 가능
- "AI-Driven" 명실상부
- 검증 가능한 수학적 기반
