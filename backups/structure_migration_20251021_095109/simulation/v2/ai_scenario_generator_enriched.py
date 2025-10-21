"""
Enriched AI Multi-Scenario Generator
Enriched Domain Data를 활용한 5-7개 다중 시나리오 생성

AIScenarioGenerator와 동일한 역할이지만 EnrichedTeamInput을 사용
"""

import json
import logging
import re
from typing import Dict, List, Optional, Tuple

from ai.ai_factory import get_ai_client
from ai.enriched_data_models import EnrichedTeamInput
from .scenario import Scenario, ScenarioEvent, EventType

logger = logging.getLogger(__name__)


class EnrichedAIScenarioGenerator:
    """
    AI 기반 다중 시나리오 생성기 (Enriched Domain Data, 100% 사용자 입력 기반)

    Generate 5-7 distinct scenarios using enriched team data:
    - 11 players × 10-12 attributes
    - User commentary (PRIMARY FACTOR)
    - Derived team strengths (계산값)
    - Formation & Lineup
    """

    def __init__(self, model: str = None):
        """
        Args:
            model: AI model name (optional, uses AI_PROVIDER from .env if not specified)
        """
        self.ai_client = get_ai_client()  # Uses AI_PROVIDER from .env
        model_info = self.ai_client.get_model_info()
        logger.info(f"EnrichedAIScenarioGenerator initialized with {model_info['provider']}: {model_info['model']}")

    def generate_scenarios_enriched(
        self,
        home_team: EnrichedTeamInput,
        away_team: EnrichedTeamInput,
        match_context: Optional[Dict] = None
    ) -> Tuple[bool, Optional[List[Scenario]], Optional[str]]:
        """
        5-7개 다중 시나리오 생성 (Enriched Domain Data 기반)

        Args:
            home_team: 홈팀 Enriched Domain Data
            away_team: 원정팀 Enriched Domain Data
            match_context: 매치 컨텍스트 (optional)

        Returns:
            Tuple of (success, scenarios_list, error_message)
        """
        try:
            # 1. Build prompts
            system_prompt = self._build_enriched_system_prompt_for_scenarios()
            user_prompt = self._build_enriched_scenario_generation_prompt(
                home_team=home_team,
                away_team=away_team,
                match_context=match_context or {}
            )

            # 2. Call AI
            logger.info("Calling AI for enriched scenario generation...")
            success, response_text, usage_data, error = self.ai_client.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.8,  # Higher creativity for diverse scenarios
                max_tokens=4000
            )

            if not success:
                logger.error(f"AI generation failed: {error}")
                return False, None, error

            logger.info(f"AI response received ({usage_data['total_tokens']:.0f} tokens)")

            # 3. Parse JSON response
            scenarios = self._parse_scenarios(response_text)

            if not scenarios:
                return False, None, "Failed to parse scenarios from AI response"

            # 4. Validate scenarios
            is_valid, validation_error = self._validate_scenarios(scenarios)
            if not is_valid:
                logger.warning(f"Validation warning: {validation_error}")
                # Continue anyway - AI will refine in Phase 3

            logger.info(f"✓ Generated {len(scenarios)} enriched scenarios")
            return True, scenarios, None

        except Exception as e:
            error_msg = f"Enriched scenario generation error: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg

    def _build_enriched_system_prompt_for_scenarios(self) -> str:
        """
        Enriched Domain Data 기반 시나리오 생성 시스템 프롬프트

        Returns:
            시나리오 생성용 시스템 프롬프트
        """
        return """You are an EPL tactical simulation expert.

Your role is to generate 5-7 DISTINCT match scenarios based on enriched domain data.

INPUT DATA PRIORITY (100% User Input Based):
1. **User Domain Knowledge** (HIGHEST PRIORITY): User commentary on players and team strategies
2. **Player Attributes** (10-12 position-specific attributes per player)
3. **Formation & Formation Tactics** (11 players with positional roles + tactical approach)
4. **Derived Team Strengths** (attack, defense, midfield, physical)

SCENARIO GENERATION RULES:
1. Generate EXACTLY 5-7 distinct scenarios
2. Each scenario must tell a DIFFERENT story:
   - Scenario 1: Dominant home win (early goal → control)
   - Scenario 2: Close home win (tight match → late winner)
   - Scenario 3: Draw (balanced match → shared points)
   - Scenario 4: Close away win (resilient defense → counter-attack)
   - Scenario 5: Dominant away win (away control)
   - Scenario 6: High-scoring draw (both teams attack) [optional]
   - Scenario 7: Low-scoring draw (defensive battle) [optional]
3. Each scenario must have:
   - Unique narrative based on user insights
   - 3-8 ScenarioEvents with specific timing and probability boosts
   - Parameter adjustments reflecting tactical changes
   - Expected probability (sum of all scenarios ≈ 1.0)

OUTPUT FORMAT:
Return ONLY a valid JSON object (no markdown, no explanations):

{
  "scenarios": [
    {
      "id": "SYNTH_001",
      "name": "시나리오 이름 (한글)",
      "reasoning": "Why this scenario is relevant based on user insights and data",
      "events": [
        {
          "minute_range": [10, 25],
          "type": "wing_breakthrough",
          "team": "home",
          "actor": "Player Name",
          "method": "wing_attack",
          "probability_boost": 2.5,
          "reason": "Specific reason from user commentary or attributes",
          "trigger": null,
          "to": null
        }
      ],
      "parameter_adjustments": {
        "home_attack_modifier": 1.15,
        "away_left_defense_modifier": 0.85
      },
      "expected_probability": 0.18
    }
  ],
  "total_probability": 0.98,
  "confidence": 0.85,
  "reasoning": "Overall reasoning for scenario distribution"
}

AVAILABLE EVENT TYPES:
- wing_breakthrough: Winger beats defender on flank
- central_penetration: Through-ball or dribble through middle
- goal: Goal scored (most important event)
- shot_on_target: Shot saved or blocked
- shot_off_target: Shot misses target
- corner: Corner kick awarded
- formation_change: Tactical formation switch (include "to" field)
- substitution: Player substitution
- foul: Foul committed
- yellow_card: Caution
- red_card: Sending off

VALIDATION REQUIREMENTS:
1. Number of scenarios: 5-7 (exactly)
2. Probability sum: 0.9 - 1.1
3. probability_boost range: 1.0 - 3.0
4. minute_range: [start, end] where 0 ≤ start ≤ end ≤ 90
5. Each scenario must have unique name
6. Events must be logically sequenced (early events before late events)

IMPORTANT: Return ONLY the JSON object. No markdown code blocks, no explanations."""

    def _build_enriched_scenario_generation_prompt(
        self,
        home_team: EnrichedTeamInput,
        away_team: EnrichedTeamInput,
        match_context: Dict
    ) -> str:
        """
        Enriched Domain Data 기반 시나리오 생성 프롬프트 (100% 사용자 입력 기반)

        6 Sections:
        1. User Domain Knowledge (PRIMARY)
        2. Team Overview
        3. Key Players Detailed Attributes
        4. Position Group Analysis
        5. Match Context (optional)
        6. Scenario Generation Instructions
        """
        prompt_parts = [
            f"# Match Scenario Generation: {home_team.name} vs {away_team.name}\n"
        ]

        # ============================================================
        # Section 1: User Domain Knowledge (최우선!)
        # ============================================================
        prompt_parts.append("\n## 🎯 User Domain Knowledge (PRIMARY FACTOR)\n")
        prompt_parts.append("Use this knowledge as the PRIMARY BASIS for scenario generation.\n")

        # Team Strategy Commentary
        if home_team.team_strategy_commentary:
            prompt_parts.append(f"\n**{home_team.name} Strategy**: {home_team.team_strategy_commentary}")
        if away_team.team_strategy_commentary:
            prompt_parts.append(f"\n**{away_team.name} Strategy**: {away_team.team_strategy_commentary}")

        # Key Players Commentary (Top 5)
        prompt_parts.append(f"\n\n**Key Players Insights**:")

        for team, label in [(home_team, 'Home'), (away_team, 'Away')]:
            key_players = team.get_key_players(top_n=5)
            prompt_parts.append(f"\n\n{label} Team ({team.name}):")

            for player in key_players:
                if player.user_commentary:
                    prompt_parts.append(f"- **{player.name}** ({player.position}): {player.user_commentary}")

        # ============================================================
        # Section 2: Team Overview
        # ============================================================
        prompt_parts.append("\n\n## 📊 Team Overview\n")

        for team, label in [(home_team, 'Home'), (away_team, 'Away')]:
            prompt_parts.append(f"\n**{label} Team: {team.name}**")
            prompt_parts.append(f"- Formation: {team.formation}")

            # Formation Tactics (사용자 선택 기반 전술 방향)
            if team.formation_tactics:
                ft = team.formation_tactics
                prompt_parts.append(f"- Formation Style: {ft.name} ({ft.style})")
                prompt_parts.append(f"  - Buildup: {ft.buildup}")
                prompt_parts.append(f"  - Pressing: {ft.pressing}")
                prompt_parts.append(f"  - Space Utilization: {ft.space_utilization}")
                prompt_parts.append(f"  - Strengths: {', '.join(ft.strengths)}")
                prompt_parts.append(f"  - Weaknesses: {', '.join(ft.weaknesses)}")

            if team.derived_strengths:
                ds = team.derived_strengths
                prompt_parts.append(f"- Attack Strength: {ds.attack_strength:.1f}/100 (derived from player attributes)")
                prompt_parts.append(f"- Defense Strength: {ds.defense_strength:.1f}/100 (derived from player attributes)")
                prompt_parts.append(f"- Midfield Control: {ds.midfield_control:.1f}/100 (derived from player attributes)")
                prompt_parts.append(f"- Physical Intensity: {ds.physical_intensity:.1f}/100 (derived from player attributes)")

        # ============================================================
        # Section 3: Key Players Detailed Attributes
        # ============================================================
        prompt_parts.append("\n\n## 🌟 Key Players Detailed Attributes\n")

        for team, label in [(home_team, 'Home'), (away_team, 'Away')]:
            key_players = team.get_key_players(top_n=5)
            prompt_parts.append(f"\n**{label} Team ({team.name}) - Top 5 Players**:")

            for player in key_players:
                prompt_parts.append(f"\n{player.name} ({player.position}) - Overall: {player.overall_rating:.2f}")

                if player.ratings:
                    top_attrs = player.get_key_strengths(top_n=5)
                    attr_strs = [f"{attr}: {player.ratings[attr]:.2f}" for attr in top_attrs]
                    prompt_parts.append(f"  Key Strengths: {', '.join(attr_strs)}")

                if player.user_commentary:
                    prompt_parts.append(f"  User Notes: {player.user_commentary}")

        # ============================================================
        # Section 4: Position Group Analysis
        # ============================================================
        prompt_parts.append("\n\n## 📍 Position Group Analysis\n")

        for team, label in [(home_team, 'Home'), (away_team, 'Away')]:
            prompt_parts.append(f"\n**{label} Team ({team.name})**:")

            # Categorize by position
            attackers = [p for pos, p in team.lineup.items() if pos in ['ST', 'LW', 'RW', 'CF', 'ST1', 'ST2']]
            midfielders = [p for pos, p in team.lineup.items() if 'M' in pos or pos in ['CAM', 'CM', 'CDM', 'DM']]
            defenders = [p for pos, p in team.lineup.items() if pos in ['CB', 'LB', 'RB', 'CB1', 'CB2', 'CB-L', 'CB-R']]

            if attackers:
                avg = sum(p.overall_rating for p in attackers) / len(attackers)
                prompt_parts.append(f"- **Attack** ({len(attackers)} players): Avg {avg:.2f}")

            if midfielders:
                avg = sum(p.overall_rating for p in midfielders) / len(midfielders)
                prompt_parts.append(f"- **Midfield** ({len(midfielders)} players): Avg {avg:.2f}")

            if defenders:
                avg = sum(p.overall_rating for p in defenders) / len(defenders)
                prompt_parts.append(f"- **Defense** ({len(defenders)} players): Avg {avg:.2f}")

        # ============================================================
        # Section 5: Match Context (Optional)
        # ============================================================
        if match_context:
            prompt_parts.append("\n\n## 🏟️ Match Context\n")
            for key, value in match_context.items():
                prompt_parts.append(f"- {key.capitalize()}: {value}")

        # ============================================================
        # Section 6: Scenario Generation Instructions
        # ============================================================
        prompt_parts.append("\n\n## 📝 Scenario Generation Instructions\n")
        prompt_parts.append("Generate 5-7 DISTINCT scenarios exploring different match outcomes.\n")
        prompt_parts.append("**CRITICAL**: Each scenario must tell a DIFFERENT story:\n")
        prompt_parts.append("1. **Dominant Home Win**: Home team controls match, scores early, maintains lead")
        prompt_parts.append("2. **Close Home Win**: Tight match, home team wins by 1 goal, tense finish")
        prompt_parts.append("3. **Draw**: Balanced match, both teams create chances, shared points")
        prompt_parts.append("4. **Close Away Win**: Away team resilient, scores on counter-attack or set-piece")
        prompt_parts.append("5. **Dominant Away Win**: Away team controls, superior tactics/execution")
        prompt_parts.append("6. **High-Scoring Draw** (optional): Both teams attack, 2-2 or 3-3")
        prompt_parts.append("7. **Low-Scoring Draw** (optional): Defensive battle, 0-0 or 1-1\n")
        prompt_parts.append("**Key Considerations**:")
        prompt_parts.append("- User commentary is the MOST IMPORTANT factor")
        prompt_parts.append("- Use player attributes to justify probability boosts")
        prompt_parts.append("- Consider tactical matchups (formation vs formation)")
        prompt_parts.append("- **Formation tactics** define each team's buildup, pressing, and space utilization - use this to predict likely scenarios")
        prompt_parts.append("- Exploit tactical weaknesses (e.g., if a team is weak on wings, create wing_breakthrough scenarios)")
        prompt_parts.append("- Include key moments (goals, formation changes, cards)")
        prompt_parts.append("- Ensure events are logically sequenced within minute_range\n")
        prompt_parts.append("**Return ONLY the JSON object, no markdown blocks, no explanations.**")

        return "\n".join(prompt_parts)

    def _parse_scenarios(
        self,
        response_text: str
    ) -> Optional[List[Scenario]]:
        """
        AI 응답을 Scenario 객체 리스트로 파싱

        Returns:
            List[Scenario] or None if parsing fails
        """
        try:
            # Extract JSON (handle markdown code blocks)
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response_text.strip()

            # Parse JSON
            data = json.loads(json_str)

            # Convert to Scenario objects
            scenarios = []
            for scenario_data in data.get('scenarios', []):
                scenario = self._dict_to_scenario(scenario_data)
                scenarios.append(scenario)

            logger.info(f"Parsed {len(scenarios)} scenarios from AI response")
            return scenarios

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.error(f"Response: {response_text[:500]}")
            return None
        except Exception as e:
            logger.error(f"Scenario parsing error: {e}")
            return None

    def _dict_to_scenario(self, data: Dict) -> Scenario:
        """딕셔너리를 Scenario 객체로 변환"""
        # Parse events
        events = []
        for event_data in data.get('events', []):
            try:
                event = ScenarioEvent(
                    minute_range=tuple(event_data['minute_range']),
                    type=EventType(event_data['type']),
                    team=event_data['team'],
                    actor=event_data.get('actor'),
                    method=event_data.get('method'),
                    probability_boost=event_data.get('probability_boost', 1.0),
                    reason=event_data.get('reason', ''),
                    trigger=event_data.get('trigger'),
                    to=event_data.get('to')
                )
                events.append(event)
            except Exception as e:
                logger.warning(f"Failed to parse event: {e}")
                continue

        # Create scenario
        scenario = Scenario(
            id=data['id'],
            name=data['name'],
            reasoning=data.get('reasoning', ''),
            events=events,
            parameter_adjustments=data.get('parameter_adjustments', {}),
            expected_probability=data.get('expected_probability', 0.0),
            base_narrative=data.get('base_narrative')
        )

        return scenario

    def _validate_scenarios(
        self,
        scenarios: List[Scenario]
    ) -> Tuple[bool, Optional[str]]:
        """
        시나리오 검증

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check count
        if not (5 <= len(scenarios) <= 7):
            return False, f"Expected 5-7 scenarios, got {len(scenarios)}"

        # Check probability sum
        total_prob = sum(s.expected_probability for s in scenarios)
        if not (0.9 <= total_prob <= 1.1):
            return False, f"Total probability {total_prob:.2f} outside range [0.9, 1.1]"

        # Check distinctness
        names = [s.name for s in scenarios]
        if len(names) != len(set(names)):
            return False, "Duplicate scenario names detected"

        return True, None


# Global instance
_enriched_scenario_generator = None


def get_enriched_scenario_generator(model: str = None) -> EnrichedAIScenarioGenerator:
    """Get global enriched scenario generator instance (singleton)."""
    global _enriched_scenario_generator
    if _enriched_scenario_generator is None:
        _enriched_scenario_generator = EnrichedAIScenarioGenerator(model=model)
    return _enriched_scenario_generator
