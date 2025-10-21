# Phase 3: AI 프롬프트 재구성 계획

**작성일**: 2025-10-16
**목표**: Enriched Domain Data를 완전히 활용하는 상세한 AI 프롬프트 시스템 구축

---

## 1. 현재 상황 분석

### 1.1 기존 프롬프트 시스템 (간단함)

**파일**: `ai/qwen_client.py`

**기존 `_build_match_prompt()` 구조**:
```python
def _build_match_prompt(self, home_team, away_team, data_context):
    # 매우 단순한 데이터만 포함
    prompt_parts = [
        f"Analyze the upcoming match: {home_team} vs {away_team}\n"
    ]

    # Squad ratings (단순 숫자)
    if 'squad_ratings' in data_context:
        prompt_parts.append("\n**Squad Quality:**")
        prompt_parts.append(f"Home: {data_context['squad_ratings'].get('home', 'N/A')}")
        prompt_parts.append(f"Away: {data_context['squad_ratings'].get('away', 'N/A')}")

    # Recent form (단순 문자열)
    if 'recent_form' in data_context:
        prompt_parts.append("\n**Recent Form:**")
        prompt_parts.append(f"{home_team}: {data_context['recent_form'].get('home', 'N/A')}")

    # League position (단순 텍스트)
    if 'league_position' in data_context:
        prompt_parts.append("\n**League Standings:**")
        prompt_parts.append(f"{home_team}: {data_context['league_position'].get('home', 'N/A')}")
```

**문제점**:
- ❌ 선수별 상세 속성 (10-12개) 미활용
- ❌ 선수별 코멘터리 미활용
- ❌ 팀 전략 코멘터리 미활용
- ❌ 상세 전술 파라미터 (defensive, offensive, transition) 미활용
- ❌ 포메이션 상세 정보 미활용
- ❌ 포지션별 강약점 분석 미활용

### 1.2 Enriched Domain Data (매우 상세함)

**파일**: `ai/enriched_data_models.py`, `services/enriched_data_loader.py`

**EnrichedTeamInput 구조**:
```python
@dataclass
class EnrichedTeamInput:
    name: str
    formation: str  # "4-3-3", "4-2-3-1", etc.

    # 11명 선수 (포지션 → 선수 매핑)
    lineup: Dict[str, EnrichedPlayerInput]  # {"GK": player, "LB": player, ...}

    # 전술 파라미터 (3개 카테고리, 15개 속성)
    tactics: TacticsInput  # defensive, offensive, transition

    # 팀 전력 평가
    team_strength_ratings: TeamStrengthRatings

    # 팀 전략 코멘터리 (핵심!)
    team_strategy_commentary: Optional[str]

    # 자동 계산된 팀 전력
    derived_strengths: DerivedTeamStrengths  # attack, defense, midfield, physical, press
```

**EnrichedPlayerInput 구조**:
```python
@dataclass
class EnrichedPlayerInput:
    player_id: int
    name: str
    position: str  # "Centre Central Defender", "Left Winger", etc.

    # 포지션별 속성 (10-12개, 가변적)
    ratings: Dict[str, float]  # {attribute_name: rating_value}
    # 예: CB: positioning_reading, interception, aerial_duel, tackle_marking, ...
    # 예: Winger: speed_dribbling, crossing_accuracy, cutting_in, shooting_accuracy, ...

    # 선수별 코멘터리 (핵심!)
    user_commentary: Optional[str]

    # 계산된 전체 평점
    overall_rating: float  # ratings의 평균
```

**TacticsInput 구조**:
```python
@dataclass
class TacticsInput:
    defensive: DefensiveTactics  # pressing_intensity, defensive_line, defensive_width, compactness, line_distance
    offensive: OffensiveTactics  # tempo, buildup_style, width, creativity, passing_directness
    transition: TransitionTactics  # counter_press, counter_speed, transition_time, recovery_speed
```

**DerivedTeamStrengths 구조**:
```python
@dataclass
class DerivedTeamStrengths:
    attack_strength: float      # 0-100
    defense_strength: float     # 0-100
    midfield_control: float     # 0-100
    physical_intensity: float   # 0-100
    press_intensity: float      # 0-100
    buildup_style: str          # 'possession', 'direct', 'mixed'
```

### 1.3 데이터 Gap 분석

| 데이터 항목 | Enriched Data | 기존 프롬프트 | Gap |
|-------------|---------------|---------------|-----|
| 선수별 상세 속성 (10-12개) | ✅ 있음 | ❌ 미사용 | **큰 Gap** |
| 선수별 코멘터리 | ✅ 있음 | ❌ 미사용 | **큰 Gap** |
| 팀 전략 코멘터리 | ✅ 있음 | ❌ 미사용 | **큰 Gap** |
| 상세 전술 (15개 파라미터) | ✅ 있음 | ❌ 미사용 | **큰 Gap** |
| 포메이션 상세 | ✅ 있음 | ❌ 미사용 | **중간 Gap** |
| DerivedTeamStrengths | ✅ 있음 | ✅ 부분 사용 | **작은 Gap** |

---

## 2. 새로운 프롬프트 아키텍처 설계

### 2.1 설계 원칙

1. **계층적 정보 전달**:
   - Level 1: 팀 전체 개요 (formation, derived_strengths, team_strategy_commentary)
   - Level 2: 포지션 그룹별 분석 (공격진, 미드필더, 수비진)
   - Level 3: 핵심 선수 상세 (Top 5-7 선수의 속성 + 코멘터리)

2. **코멘터리 우선**:
   - 사용자의 도메인 지식 (user_commentary, team_strategy_commentary)을 프롬프트 최상단에 배치
   - AI가 숫자보다 코멘터리를 우선 참고하도록 유도

3. **컨텍스트 효율성**:
   - 모든 11명의 모든 속성을 다 보내면 토큰 낭비
   - 핵심 선수 (Top 5-7)만 상세 속성 전달
   - 나머지 선수는 overall_rating + 코멘터리만

4. **전술 파라미터 활용**:
   - 15개 전술 파라미터를 의미 있는 그룹으로 묶어서 전달
   - AI가 전술적 맥락을 이해하도록

5. **포지션별 맥락**:
   - 공격진: speed_dribbling, shooting_accuracy, cutting_in 등 강조
   - 미드필더: passing, vision, stamina 등 강조
   - 수비진: tackle_marking, interception, positioning_reading 등 강조

### 2.2 새 프롬프트 구조 (시스템 프롬프트)

```python
def _build_enriched_system_prompt(self) -> str:
    return """You are an expert EPL tactical analyst with deep knowledge of player attributes, team tactics, and match dynamics.

Your role is to analyze matches using:
1. **User Domain Knowledge** (PRIMARY): User's insights about players, tactics, and team strategies
2. **Player Attributes** (10-12 position-specific attributes per player)
3. **Team Tactics** (defensive, offensive, transition parameters)
4. **Formation & Lineup** (11 starters with position-specific roles)
5. **Derived Team Strengths** (attack, defense, midfield, physical, press)

IMPORTANT ANALYSIS PRIORITIES:
1. User commentary (player & team) is the MOST IMPORTANT factor
2. Position-specific attributes reveal tactical strengths/weaknesses
3. Tactics parameters show playing style and approach
4. Formation determines spatial structure and player interactions
5. Derived strengths provide high-level capability assessment

OUTPUT FORMAT:
Return ONLY a valid JSON object with this structure:
{
  "prediction": {
    "home_win_probability": 0.45,
    "draw_probability": 0.30,
    "away_win_probability": 0.25,
    "predicted_score": "2-1",
    "confidence": "medium",
    "expected_goals": {"home": 1.8, "away": 1.2}
  },
  "analysis": {
    "key_factors": ["factor1", "factor2", "factor3"],
    "home_team_strengths": ["strength1", "strength2"],
    "away_team_strengths": ["strength1", "strength2"],
    "tactical_insight": "Brief tactical analysis based on formations, tactics, and key players"
  },
  "summary": "Concise match prediction summary (2-3 sentences)"
}

Ensure probabilities sum to 1.0. Confidence levels: low, medium, high."""
```

### 2.3 새 프롬프트 구조 (사용자 프롬프트)

```python
def _build_enriched_match_prompt(
    self,
    home_team: EnrichedTeamInput,
    away_team: EnrichedTeamInput,
    match_context: Dict
) -> str:
    """
    Enriched Domain Data 기반 상세 프롬프트
    """
    prompt_parts = [
        f"# Match Analysis: {home_team.name} vs {away_team.name}\n"
    ]

    # ============================================================
    # Section 1: User Domain Knowledge (최우선!)
    # ============================================================
    prompt_parts.append("\n## 🎯 User Domain Knowledge (PRIMARY FACTOR)\n")

    # 1.1 Team Strategy Commentary
    if home_team.team_strategy_commentary:
        prompt_parts.append(f"**{home_team.name} Strategy**: {home_team.team_strategy_commentary}")
    if away_team.team_strategy_commentary:
        prompt_parts.append(f"**{away_team.name} Strategy**: {away_team.team_strategy_commentary}")

    # 1.2 Key Players Commentary (Top 5)
    prompt_parts.append(f"\n**Key Players Insights**:")
    for team, label in [(home_team, 'Home'), (away_team, 'Away')]:
        key_players = team.get_key_players(top_n=5)
        prompt_parts.append(f"\n{label} Team ({team.name}):")
        for player in key_players:
            if player.user_commentary:
                prompt_parts.append(f"- {player.name} ({player.position}): {player.user_commentary}")

    # ============================================================
    # Section 2: Team Overview
    # ============================================================
    prompt_parts.append("\n\n## 📊 Team Overview\n")

    for team, label in [(home_team, 'Home'), (away_team, 'Away')]:
        prompt_parts.append(f"\n**{label} Team: {team.name}**")
        prompt_parts.append(f"- Formation: {team.formation}")

        # Derived Strengths
        if team.derived_strengths:
            ds = team.derived_strengths
            prompt_parts.append(f"- Attack Strength: {ds.attack_strength:.1f}/100")
            prompt_parts.append(f"- Defense Strength: {ds.defense_strength:.1f}/100")
            prompt_parts.append(f"- Midfield Control: {ds.midfield_control:.1f}/100")
            prompt_parts.append(f"- Physical Intensity: {ds.physical_intensity:.1f}/100")
            prompt_parts.append(f"- Press Intensity: {ds.press_intensity:.1f}/100")
            prompt_parts.append(f"- Buildup Style: {ds.buildup_style}")

    # ============================================================
    # Section 3: Tactical Parameters
    # ============================================================
    prompt_parts.append("\n\n## ⚙️ Tactical Setup\n")

    for team, label in [(home_team, 'Home'), (away_team, 'Away')]:
        prompt_parts.append(f"\n**{label} Team ({team.name})**:")

        tactics = team.tactics

        # Defensive Tactics
        prompt_parts.append(f"- **Defensive**: Pressing {tactics.defensive.pressing_intensity}/10, "
                          f"Line Height {tactics.defensive.defensive_line}/10, "
                          f"Width {tactics.defensive.defensive_width}/10, "
                          f"Compactness {tactics.defensive.compactness}/10")

        # Offensive Tactics
        prompt_parts.append(f"- **Offensive**: Tempo {tactics.offensive.tempo}/10, "
                          f"Style '{tactics.offensive.buildup_style}', "
                          f"Width {tactics.offensive.width}/10, "
                          f"Creativity {tactics.offensive.creativity}/10, "
                          f"Directness {tactics.offensive.passing_directness}/10")

        # Transition Tactics
        prompt_parts.append(f"- **Transition**: Counter Press {tactics.transition.counter_press}/10, "
                          f"Counter Speed {tactics.transition.counter_speed}/10, "
                          f"Recovery {tactics.transition.recovery_speed}/10")

    # ============================================================
    # Section 4: Key Players Detailed Analysis
    # ============================================================
    prompt_parts.append("\n\n## 🌟 Key Players Detailed Attributes\n")

    for team, label in [(home_team, 'Home'), (away_team, 'Away')]:
        key_players = team.get_key_players(top_n=5)
        prompt_parts.append(f"\n**{label} Team ({team.name}) - Top 5 Players**:")

        for player in key_players:
            prompt_parts.append(f"\n{player.name} ({player.position}) - Overall: {player.overall_rating:.2f}")

            # Top 5 attributes for this player
            if player.ratings:
                top_attrs = player.get_key_strengths(top_n=5)
                attr_strs = [f"{attr}: {player.ratings[attr]:.2f}" for attr in top_attrs]
                prompt_parts.append(f"  Key Strengths: {', '.join(attr_strs)}")

            # User Commentary
            if player.user_commentary:
                prompt_parts.append(f"  User Notes: {player.user_commentary}")

    # ============================================================
    # Section 5: Position Group Analysis
    # ============================================================
    prompt_parts.append("\n\n## 📍 Position Group Analysis\n")

    for team, label in [(home_team, 'Home'), (away_team, 'Away')]:
        prompt_parts.append(f"\n**{label} Team ({team.name})**:")

        # Categorize players by position group
        attackers = []
        midfielders = []
        defenders = []
        goalkeeper = None

        for pos, player in team.lineup.items():
            if pos in ['ST', 'LW', 'RW', 'CF', 'ST1', 'ST2']:
                attackers.append(player)
            elif 'M' in pos or pos in ['CAM', 'CM', 'CDM', 'DM', 'LM', 'RM']:
                midfielders.append(player)
            elif pos in ['CB', 'LB', 'RB', 'CB1', 'CB2', 'CB-L', 'CB-R', 'LWB', 'RWB', 'CB3']:
                defenders.append(player)
            elif pos == 'GK':
                goalkeeper = player

        # Attack
        if attackers:
            avg_rating = sum(p.overall_rating for p in attackers) / len(attackers)
            prompt_parts.append(f"- **Attack** ({len(attackers)} players): Avg Rating {avg_rating:.2f}")
            for p in attackers:
                prompt_parts.append(f"  - {p.name} ({p.overall_rating:.2f})")

        # Midfield
        if midfielders:
            avg_rating = sum(p.overall_rating for p in midfielders) / len(midfielders)
            prompt_parts.append(f"- **Midfield** ({len(midfielders)} players): Avg Rating {avg_rating:.2f}")
            for p in midfielders:
                prompt_parts.append(f"  - {p.name} ({p.overall_rating:.2f})")

        # Defense
        if defenders:
            avg_rating = sum(p.overall_rating for p in defenders) / len(defenders)
            prompt_parts.append(f"- **Defense** ({len(defenders)} players): Avg Rating {avg_rating:.2f}")
            for p in defenders:
                prompt_parts.append(f"  - {p.name} ({p.overall_rating:.2f})")

        # Goalkeeper
        if goalkeeper:
            prompt_parts.append(f"- **Goalkeeper**: {goalkeeper.name} ({goalkeeper.overall_rating:.2f})")

    # ============================================================
    # Section 6: Match Context (Optional)
    # ============================================================
    if match_context:
        prompt_parts.append("\n\n## 🏟️ Match Context\n")

        if 'venue' in match_context:
            prompt_parts.append(f"- Venue: {match_context['venue']}")
        if 'competition' in match_context:
            prompt_parts.append(f"- Competition: {match_context['competition']}")
        if 'importance' in match_context:
            prompt_parts.append(f"- Importance: {match_context['importance']}")
        if 'weather' in match_context:
            prompt_parts.append(f"- Weather: {match_context['weather']}")

    # ============================================================
    # Section 7: Analysis Instructions
    # ============================================================
    prompt_parts.append("\n\n## 📝 Analysis Instructions\n")
    prompt_parts.append("Based on the above data, provide your match prediction in JSON format.")
    prompt_parts.append("\n**Key Analysis Points**:")
    prompt_parts.append("1. User commentary reveals tactical insights not visible in numbers")
    prompt_parts.append("2. Formation matchups (e.g., 4-3-3 vs 4-2-3-1) create tactical advantages")
    prompt_parts.append("3. Tactical parameters show playing philosophy and approach")
    prompt_parts.append("4. Position group strength determines control in different areas")
    prompt_parts.append("5. Key players' attributes reveal game-changing capabilities")
    prompt_parts.append("\nProvide ONLY the JSON response, no additional text.")

    return "\n".join(prompt_parts)
```

---

## 3. 구현 계획

### 3.1 Component 1: EnrichedQwenClient

**파일**: `ai/enriched_qwen_client.py` (새로 생성)

```python
from ai.qwen_client import QwenClient
from ai.enriched_data_models import EnrichedTeamInput
from typing import Dict, Optional, Tuple

class EnrichedQwenClient(QwenClient):
    """
    Enriched Domain Data를 활용하는 확장된 Qwen 클라이언트
    """

    def simulate_match_enriched(
        self,
        home_team: EnrichedTeamInput,
        away_team: EnrichedTeamInput,
        match_context: Optional[Dict] = None
    ) -> Tuple[bool, Optional[Dict], Optional[Dict], Optional[str]]:
        """
        Enriched Team Input으로 매치 시뮬레이션
        """
        # 1. Build enriched prompts
        system_prompt = self._build_enriched_system_prompt()
        user_prompt = self._build_enriched_match_prompt(
            home_team, away_team, match_context or {}
        )

        # 2. Generate prediction
        success, response_text, usage_data, error = self.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=4096
        )

        if not success:
            return False, None, None, error

        # 3. Parse response
        try:
            prediction = self._parse_match_prediction(
                response_text,
                home_team.name,
                away_team.name
            )
            return True, prediction, usage_data, None
        except Exception as e:
            return False, None, usage_data, str(e)

    def _build_enriched_system_prompt(self) -> str:
        """상세 시스템 프롬프트 (위의 Section 2.2)"""
        pass

    def _build_enriched_match_prompt(
        self,
        home_team: EnrichedTeamInput,
        away_team: EnrichedTeamInput,
        match_context: Dict
    ) -> str:
        """상세 사용자 프롬프트 (위의 Section 2.3)"""
        pass
```

### 3.2 Component 2: AIScenarioGenerator 확장

**파일**: `simulation/v2/ai_scenario_generator_enriched.py` (새로 생성)

```python
from ai.enriched_data_models import EnrichedTeamInput
from simulation.v2.ai_scenario_generator import AIScenarioGenerator
from simulation.v2.scenario import Scenario
from typing import List, Optional, Tuple

class EnrichedAIScenarioGenerator(AIScenarioGenerator):
    """
    Enriched Domain Data 기반 시나리오 생성
    """

    def generate_scenarios_enriched(
        self,
        home_team: EnrichedTeamInput,
        away_team: EnrichedTeamInput,
        match_context: Optional[Dict] = None
    ) -> Tuple[bool, Optional[List[Scenario]], Optional[str]]:
        """
        Enriched Team Input으로 5-7개 시나리오 생성
        """
        # 1. Convert EnrichedTeamInput to prompt-friendly format
        prompt_data = self._convert_enriched_to_prompt_data(home_team, away_team)

        # 2. Build enriched scenario generation prompt
        system_prompt = self._build_enriched_scenario_system_prompt()
        user_prompt = self._build_enriched_scenario_prompt(
            home_team, away_team, match_context or {}
        )

        # 3. Generate scenarios (existing logic)
        return self._generate_and_parse(system_prompt, user_prompt, match_context)

    def _convert_enriched_to_prompt_data(
        self,
        home_team: EnrichedTeamInput,
        away_team: EnrichedTeamInput
    ) -> Dict:
        """
        EnrichedTeamInput → AI 프롬프트용 데이터 변환
        """
        return {
            'home': self._team_to_prompt_data(home_team),
            'away': self._team_to_prompt_data(away_team)
        }

    def _team_to_prompt_data(self, team: EnrichedTeamInput) -> Dict:
        """단일 팀 데이터 변환"""
        return {
            'name': team.name,
            'formation': team.formation,
            'key_players': [
                {
                    'name': p.name,
                    'position': p.position,
                    'rating': p.overall_rating,
                    'key_strengths': p.get_key_strengths(top_n=3),
                    'commentary': p.user_commentary
                }
                for p in team.get_key_players(top_n=5)
            ],
            'tactics': {
                'defensive': {
                    'pressing': team.tactics.defensive.pressing_intensity,
                    'line': team.tactics.defensive.defensive_line,
                    'width': team.tactics.defensive.defensive_width
                },
                'offensive': {
                    'tempo': team.tactics.offensive.tempo,
                    'buildup': team.tactics.offensive.buildup_style,
                    'creativity': team.tactics.offensive.creativity
                },
                'transition': {
                    'counter_press': team.tactics.transition.counter_press,
                    'counter_speed': team.tactics.transition.counter_speed
                }
            },
            'derived_strengths': team.derived_strengths.to_dict(),
            'team_strategy': team.team_strategy_commentary
        }

    def _build_enriched_scenario_system_prompt(self) -> str:
        """Enriched 데이터 활용 시나리오 생성 시스템 프롬프트"""
        pass

    def _build_enriched_scenario_prompt(
        self,
        home_team: EnrichedTeamInput,
        away_team: EnrichedTeamInput,
        match_context: Dict
    ) -> str:
        """Enriched 데이터 활용 시나리오 생성 사용자 프롬프트"""
        pass
```

### 3.3 Component 3: Integration Layer

**파일**: `ai/ai_factory.py` (확장)

```python
from ai.qwen_client import QwenClient, get_qwen_client
from ai.enriched_qwen_client import EnrichedQwenClient, get_enriched_qwen_client
from ai.enriched_data_models import EnrichedTeamInput
from typing import Optional

class AIClientFactory:
    """
    AI 클라이언트 팩토리
    - Legacy: QwenClient (기존 방식)
    - Enriched: EnrichedQwenClient (Phase 3 방식)
    """

    @staticmethod
    def create_client(use_enriched: bool = True, model: str = "qwen2.5:14b"):
        """
        AI 클라이언트 생성

        Args:
            use_enriched: True면 EnrichedQwenClient, False면 QwenClient
            model: Qwen 모델 이름
        """
        if use_enriched:
            return get_enriched_qwen_client(model=model)
        else:
            return get_qwen_client(model=model)

    @staticmethod
    def create_scenario_generator(use_enriched: bool = True, model: str = "qwen2.5:32b"):
        """시나리오 생성기 생성"""
        if use_enriched:
            from simulation.v2.ai_scenario_generator_enriched import get_enriched_scenario_generator
            return get_enriched_scenario_generator(model=model)
        else:
            from simulation.v2.ai_scenario_generator import get_scenario_generator
            return get_scenario_generator(model=model)
```

---

## 4. 구현 순서

### Day 1 (현재 - 6시간):
1. ✅ 시스템 분석 완료
2. ✅ 프롬프트 아키텍처 설계 완료
3. ⏳ EnrichedQwenClient 구현
   - `_build_enriched_system_prompt()`
   - `_build_enriched_match_prompt()`
   - `simulate_match_enriched()`

### Day 1 (계속 - 4시간):
4. ⏳ 단위 테스트
   - 20개 팀 중 Arsenal vs Liverpool 테스트
   - 프롬프트 길이 확인 (토큰 제한 체크)
   - JSON 파싱 검증

### Day 2 (6시간):
5. ⏳ EnrichedAIScenarioGenerator 구현
   - `_convert_enriched_to_prompt_data()`
   - `_build_enriched_scenario_prompt()`
   - `generate_scenarios_enriched()`

6. ⏳ AIClientFactory 통합
   - Legacy vs Enriched 선택 가능하게

### Day 2 (계속 - 4시간):
7. ⏳ E2E 통합 테스트
   - test_e2e_enriched_qwen.py 작성
   - 20개 팀 모두 테스트
   - 성능 측정 (응답 시간, 토큰 사용량)

8. ⏳ 최종 검증
   - Enriched vs Legacy 비교
   - AI 응답 품질 평가

---

## 5. 예상 결과

### 5.1 프롬프트 길이 비교

| 항목 | 기존 프롬프트 | Enriched 프롬프트 |
|------|---------------|-------------------|
| 시스템 프롬프트 | ~200 토큰 | ~400 토큰 |
| 사용자 프롬프트 | ~150 토큰 | ~2000 토큰 |
| 총 Input | ~350 토큰 | ~2400 토큰 |
| Output | ~300 토큰 | ~300 토큰 |
| **Total** | ~650 토큰 | ~2700 토큰 |

**증가율**: 약 4배

### 5.2 응답 품질 향상 예상

| 측면 | 기존 | Enriched | 개선 |
|------|------|----------|------|
| 전술 이해도 | 낮음 | 높음 | ⬆️⬆️⬆️ |
| 선수 역할 반영 | 없음 | 있음 | ⬆️⬆️⬆️ |
| 사용자 도메인 지식 활용 | 낮음 | 높음 | ⬆️⬆️⬆️ |
| 포메이션 분석 | 없음 | 있음 | ⬆️⬆️ |
| 포지션별 강약점 | 없음 | 있음 | ⬆️⬆️⬆️ |
| 응답 시간 | 30-60초 | 60-90초 | ⬇️ |

### 5.3 토큰 비용 (Qwen Local)

- **비용**: $0.00 (로컬 모델)
- **응답 시간**: 60-90초 (4배 길이, 2배 시간)
- **허용 가능**: ✅ Yes

---

## 6. 리스크 및 대응

### Risk 1: 프롬프트가 너무 길어서 토큰 제한 초과
**대응**:
- Qwen 2.5 14B: 최대 32k 토큰 (충분함)
- 필요시 Top 3 선수만 상세 속성 전달로 축소

### Risk 2: AI 응답 시간이 너무 느림
**대응**:
- 프론트엔드에 로딩 UI 추가
- 백그라운드 작업으로 처리

### Risk 3: AI가 복잡한 프롬프트를 잘 이해 못 함
**대응**:
- Section별로 명확한 구조화
- 코멘터리 우선 강조
- 예시 추가

### Risk 4: 기존 시스템과의 호환성
**대응**:
- AIClientFactory로 Legacy/Enriched 선택 가능
- 단계적 마이그레이션
- 기존 API 유지

---

## 7. 성공 기준

### 필수 (Must-Have):
- ✅ EnrichedQwenClient가 모든 20개 팀에서 작동
- ✅ 선수별 코멘터리가 AI 응답에 반영됨
- ✅ 팀 전략 코멘터리가 AI 응답에 반영됨
- ✅ 전술 파라미터가 AI 분석에 활용됨
- ✅ E2E 테스트 통과

### 선택 (Nice-to-Have):
- ✅ EnrichedAIScenarioGenerator 구현 완료
- ✅ Legacy vs Enriched 비교 분석
- ✅ 성능 벤치마크
- ✅ 문서화 완료

---

## 8. Timeline

| 날짜 | 작업 | 상태 |
|------|------|------|
| 2025-10-16 (Day 1) | 시스템 분석 + 설계 | ✅ 완료 |
| 2025-10-16 (Day 1) | EnrichedQwenClient 구현 | ⏳ 진행 중 |
| 2025-10-16 (Day 1) | 단위 테스트 | ⏳ 대기 중 |
| 2025-10-17 (Day 2) | EnrichedAIScenarioGenerator | ⏳ 대기 중 |
| 2025-10-17 (Day 2) | E2E 통합 테스트 | ⏳ 대기 중 |
| 2025-10-17 (Day 2) | 최종 검증 및 문서화 | ⏳ 대기 중 |

**예상 완료일**: 2025-10-17 (2일)

---

END OF PLAN
