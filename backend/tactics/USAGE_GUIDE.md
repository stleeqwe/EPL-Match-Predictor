# 전술 프레임워크 사용 가이드

## 빠른 시작

### 1. 포메이션 분석

```python
from tactics.core.formations import FormationSystem

# 포메이션 시스템 초기화
fs = FormationSystem()

# 포메이션 목록
formations = fs.list_formations()
print(formations)  # ['4-3-3', '4-2-3-1', '4-4-2', '3-5-2', '4-1-4-1', '3-4-3']

# 특정 포메이션 정보
formation_433 = fs.get_formation("4-3-3")
print(formation_433['name_kr'])  # "4-3-3 하이 프레싱"
print(formation_433['philosophy'])  # "공을 높은 위치에서 되찾는다"

# 차단률 조회
blocking_rate = fs.get_blocking_rate("4-3-3", "central_penetration")
print(f"중앙 침투 차단률: {blocking_rate}%")  # 85%
```

### 2. 차단률 계산

```python
from tactics.analyzer.effectiveness_calculator import EffectivenessCalculator

calculator = EffectivenessCalculator()

# 기본 차단률 계산
result = calculator.calculate_blocking_rate(
    formation="4-3-3",
    goal_category="central_penetration",
    team_ability_coef=1.12,  # 맨시티급 (0.80-1.20)
    fatigue_coef=0.95,       # 중3일 피로도
    psychology_coef=1.00     # 정상 심리 상태
)

print(f"예측 차단률: {result['predicted_blocking_rate']}%")
print(f"기본 차단률: {result['base_rate']}%")
print(f"통합 계수: {result['combined_coefficient']}")
```

### 3. 팀 수비력 평가

```python
# 팀 종합 수비 점수
defense_score = calculator.calculate_team_defensive_score(
    formation="4-2-3-1",
    team_ability_coef=1.05
)

print(f"종합 수비 점수: {defense_score['overall_defensive_score']:.1f}/100")
print(f"등급: {defense_score['rating']}")
print("\n득점 경로별 차단률:")
for category, rate in defense_score['by_category'].items():
    cat_info = calculator.formation_system.get_goal_category_info(category)
    print(f"  {cat_info['name']}: {rate:.1f}%")
```

### 4. 상대 전술 대응

```python
# 상대 공격 스타일 정의
opponent_style = {
    'central_penetration': 0.40,  # 중앙 집중 공격 40%
    'cutback': 0.25,              # 컷백 25%
    'wide_penetration': 0.20,     # 측면 침투 20%
    'counter_fast': 0.15          # 고속 역습 15%
}

# 최적 포메이션 추천
recommendations = calculator.compare_formations_for_opponent(
    opponent_style,
    team_ability_coef=1.00
)

print("Top 3 추천 포메이션:")
for idx, rec in enumerate(recommendations[:3]):
    print(f"{idx+1}. {rec['formation_name']}: {rec['overall_score']:.1f}%")
```

### 5. 전술 매칭 분석

```python
# 맨시티 vs 리버풀 전술 분석
matchup = calculator.calculate_matchup_advantage(
    home_formation="4-3-3",
    away_formation="4-3-3",
    home_ability=1.12,  # 맨시티
    away_ability=1.10   # 리버풀
)

print(f"홈팀 수비력: {matchup['home_defensive_score']:.1f}")
print(f"원정팀 수비력: {matchup['away_defensive_score']:.1f}")
print(f"우위: {matchup['advantage']} (+{matchup['difference']:.1f})")

# 세부 분석
for category, analysis in matchup['analysis_by_category'].items():
    if abs(analysis['difference']) > 10:  # 10% 이상 차이
        print(f"{analysis['name']}: 홈 {analysis['home_blocking']:.1f}% vs 원정 {analysis['away_blocking']:.1f}%")
```

## 고급 사용법

### 1. 득점 경로 분류

```python
from tactics.analyzer.goal_path_classifier import GoalPathClassifier, GoalData

classifier = GoalPathClassifier()

# 골 데이터 정의
goal = GoalData(
    buildup_passes=2,        # 빌드업 패스 수
    buildup_duration=3.5,    # 빌드업 시간 (초)
    x_start=45,              # 시작 x좌표 (0-105m)
    y_start=34,              # 시작 y좌표 (0-68m)
    x_shot=92,               # 슈팅 x좌표
    y_shot=38,               # 슈팅 y좌표
    assist_type='through_ball'
)

# 분류
category, confidence = classifier.classify_goal(goal)
print(f"{category} (확신도: {confidence:.2f})")

# 일괄 분류
goals = [goal1, goal2, goal3, ...]
stats = classifier.classify_batch(goals)
print(stats)  # {'central_penetration': 45, 'wide_penetration': 32, ...}
```

### 2. 전술 스타일 커스터마이징

```python
from tactics.core.tactical_styles import (
    TacticalStyle,
    DefensiveParameters,
    OffensiveParameters,
    TransitionParameters,
    TacticalPresets
)

# 커스텀 전술 생성
custom_tactics = TacticalStyle(
    name="Custom High Press",
    defensive=DefensiveParameters(
        pressing_intensity=8,
        defensive_line=7,
        defensive_width=7,
        compactness=7,
        line_distance=11.0
    ),
    offensive=OffensiveParameters(
        tempo=8,
        buildup_style="short_passing",
        width=7,
        creativity=7
    ),
    transition=TransitionParameters(
        counter_press=9,
        counter_speed=8,
        transition_time=2.5,
        recovery_speed=8
    )
)

# 프리셋 사용
tiki_taka = TacticalPresets.get_tiki_taka()
gegenpressing = TacticalPresets.get_gegenpressing()
```

### 3. 기존 프로젝트와 통합

```python
from tactics.integration import TacticsIntegration

integration = TacticsIntegration()

# 선수 능력치에 전술 적용
player = {
    'id': 1,
    'name': 'Rodri',
    'position': 'DM',
    'stamina': 85,
    'technical_attributes': {
        'tackling': 88,
        'interceptions': 90,
        'passing': 92
    }
}

tactics = {
    'pressing_intensity': 9,
    'defensive_line': 8
}

adjusted_player = integration.apply_tactics_to_player(player, tactics, 'DM')
print(f"전술 적합도: {adjusted_player['tactical_fit_score']:.1f}/100")

# 팀 스쿼드 전술 적합도
squad = [player1, player2, ..., player11]
team_score = integration.calculate_team_tactical_score(
    squad=squad,
    formation="4-3-3",
    tactics=tactics
)
print(f"팀 전술 적합도: {team_score:.1f}/100")

# 경기 결과 예측
home_team = {
    'formation': '4-3-3',
    'squad': home_squad,
    'team_ability': 1.12
}
away_team = {
    'formation': '4-2-3-1',
    'squad': away_squad,
    'team_ability': 1.08
}

prediction = integration.predict_match_outcome(home_team, away_team)
print(f"홈 승: {prediction['home_win_probability']:.1f}%")
print(f"무승부: {prediction['draw_probability']:.1f}%")
print(f"원정 승: {prediction['away_win_probability']:.1f}%")
```

## 데이터 구조

### 포메이션 데이터 (formations.json)

```json
{
  "formations": {
    "4-3-3": {
      "name": "4-3-3 High Press",
      "name_kr": "4-3-3 하이 프레싱",
      "philosophy": "공을 높은 위치에서 되찾는다",
      "positions": {...},
      "default_tactics": {
        "pressing_intensity": 9,
        "defensive_line": 8,
        ...
      },
      "blocking_rates": {
        "central_penetration": 85,
        "wide_penetration": 78,
        ...
      }
    }
  }
}
```

### 득점 경로 카테고리

- `buildup_gradual`: 빌드업 점진적 (5+ 패스)
- `buildup_medium`: 중속 전개 (3-4 패스)
- `counter_fast`: 고속 역습 (0-5초)
- `counter_normal`: 일반 역습 (6-15초)
- `central_penetration`: 중앙 침투
- `wide_penetration`: 측면 침투
- `cutback`: 컷백
- `cross_finish`: 크로스→마무리
- `halfspace`: 하프스페이스
- `corner`: 코너킥
- `freekick`: 프리킥
- `penalty`: 페널티킥

## 파라미터 범위

### 능력 계수

- **team_ability_coef**: 0.80 ~ 1.20 (기본 1.0)
  - 1.15-1.20: 맨시티, 리버풀 (최상위)
  - 1.05-1.10: 아스날, 첼시 (상위권)
  - 0.95-1.00: 중위권
  - 0.80-0.90: 하위권

- **fatigue_coef**: 0.80 ~ 1.00 (기본 1.0)
  - 1.00: 7일 이상 휴식
  - 0.95: 4-6일 휴식
  - 0.90: 3일 휴식 (중3일)
  - 0.85: 2일 이하 휴식

- **psychology_coef**: 0.88 ~ 1.05 (기본 1.0)
  - 1.05: 리드 중 (수비 강화)
  - 1.00: 정상
  - 0.88: 패배 중 (공격 강화, 수비 약화)

### 전술 파라미터 (1-10 스케일)

- **pressing_intensity**: 압박 강도 (1=낮음, 10=최고)
- **defensive_line**: 수비 라인 높이 (1=20m, 10=50m)
- **tempo**: 템포 (1=느림, 10=빠름)
- **width**: 공격 폭 (1=중앙, 10=측면 활용)

## 테스트

```bash
cd backend/tactics
python3 tests/test_basic.py
```

## 참고

- 전체 문서: `README.md`
- 통합 가이드: `integration.py`
- 데이터: `data/formations.json`

## 라이선스

MIT License
