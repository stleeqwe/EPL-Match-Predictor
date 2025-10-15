"""
AI Multi-Scenario Generator
설계 문서 Section 3 (Phase 1) 정확 구현

5-7개 다중 시나리오 생성
"""

import json
import logging
import re
from typing import Dict, List, Optional, Tuple

from ai.qwen_client import get_qwen_client
from .scenario import Scenario, ScenarioEvent, EventType

logger = logging.getLogger(__name__)


class AIScenarioGenerator:
    """
    AI 기반 다중 시나리오 생성기
    설계 문서 Section 3 구현

    Qwen AI를 사용해 5-7개의 구체적 시나리오 생성
    각 시나리오는 이벤트 시퀀스와 확률 부스트 포함
    """

    def __init__(self, model: str = "qwen2.5:32b"):
        """
        Args:
            model: Qwen model name
        """
        self.ai_client = get_qwen_client(model=model)
        logger.info(f"AIScenarioGenerator initialized with {model}")

    def generate_scenarios(
        self,
        match_context: Dict,
        player_stats: Optional[Dict] = None,
        tactics: Optional[Dict] = None,
        domain_knowledge: Optional[str] = None,
        matched_narratives: Optional[List] = None
    ) -> Tuple[bool, Optional[List[Scenario]], Optional[str]]:
        """
        5-7개 다중 시나리오 생성

        Args:
            match_context: {"home_team": "Tottenham", "away_team": "Arsenal", ...}
            player_stats: {"Son": {"speed": 92, ...}, ...}
            tactics: {"Tottenham": {"formation": "4-3-3", ...}, ...}
            domain_knowledge: "손흥민은 빅매치에서 강하다. 아스날 좌측 수비 약함."
            matched_narratives: 서사 라이브러리 템플릿 (현재 미사용)

        Returns:
            Tuple of (success, scenarios_list, error_message)
        """
        try:
            # 1. Build prompt
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_scenario_generation_prompt(
                match_context,
                player_stats,
                tactics,
                domain_knowledge,
                matched_narratives
            )

            # 2. Call AI
            logger.info("Calling Qwen AI for scenario generation...")
            success, response_text, usage_data, error = self.ai_client.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.8,  # Higher creativity for diverse scenarios
                max_tokens=4000  # Reduced for faster generation
            )

            if not success:
                logger.error(f"AI generation failed: {error}")
                return False, None, error

            logger.info(f"AI response received ({usage_data['total_tokens']:.0f} tokens)")

            # 3. Parse JSON response
            scenarios = self._parse_scenarios(response_text, match_context)

            if not scenarios:
                return False, None, "Failed to parse scenarios from AI response"

            # 4. Validate scenarios
            is_valid, validation_error = self._validate_scenarios(scenarios)
            if not is_valid:
                logger.warning(f"Validation warning: {validation_error}")
                # Continue anyway - AI will refine in Phase 3

            logger.info(f"✓ Generated {len(scenarios)} scenarios")
            return True, scenarios, None

        except Exception as e:
            error_msg = f"Scenario generation error: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg

    def _build_system_prompt(self) -> str:
        """
        시스템 프롬프트 (설계 문서 기반)
        """
        return """You are an expert EPL tactical simulation AI.

Your role is to generate realistic match scenarios based on user insights.

IMPORTANT RULES:
1. You MUST respond with ONLY a valid JSON object
2. Generate exactly 5-7 distinct scenarios
3. Each scenario must have a unique narrative
4. probability_boost must be between 1.0 and 3.0
5. Sum of expected_probability should be 0.9-1.1
6. minute_range must be [start, end] where 0 <= start <= end <= 90

Output format:
{
  "scenarios": [
    {
      "id": "SYNTH_001",
      "name": "Scenario name in Korean",
      "reasoning": "Why this scenario is relevant",
      "events": [
        {
          "minute_range": [10, 25],
          "type": "wing_breakthrough",
          "team": "home",
          "actor": "Son",
          "method": "wing_attack",
          "probability_boost": 2.5,
          "reason": "Son's pace vs weak left defense",
          "trigger": null,
          "to": null
        }
      ],
      "parameter_adjustments": {
        "Son_speed_modifier": 1.15,
        "Arsenal_left_defense_modifier": 0.75
      },
      "expected_probability": 0.18
    }
  ],
  "total_probability": 0.98,
  "confidence": 0.85
}

Available event types:
- wing_breakthrough
- central_penetration
- goal
- shot_on_target
- shot_off_target
- corner
- formation_change
- substitution
- foul
- yellow_card
- red_card

ONLY return the JSON. No explanations before or after."""

    def _build_scenario_generation_prompt(
        self,
        match_context: Dict,
        player_stats: Optional[Dict],
        tactics: Optional[Dict],
        domain_knowledge: Optional[str],
        matched_narratives: Optional[List]
    ) -> str:
        """
        사용자 프롬프트 생성 (설계 문서 Section 3)
        """
        home_team = match_context.get('home_team', 'Home Team')
        away_team = match_context.get('away_team', 'Away Team')

        prompt_parts = [
            f"# Match: {home_team} vs {away_team}\n",
            "Generate 5-7 realistic match scenarios.\n"
        ]

        # Add domain knowledge (most important)
        if domain_knowledge:
            prompt_parts.append(f"\n## User Domain Knowledge (PRIMARY FACTOR):")
            prompt_parts.append(f"{domain_knowledge}\n")
            prompt_parts.append("Convert this knowledge into concrete event sequences with probability_boost.\n")

        # Add player stats
        if player_stats:
            prompt_parts.append(f"\n## Key Players:")
            for player_name, stats in list(player_stats.items())[:5]:  # Top 5 players
                stats_str = ", ".join([f"{k}={v}" for k, v in stats.items()])
                prompt_parts.append(f"- {player_name}: {stats_str}")

        # Add tactics
        if tactics:
            prompt_parts.append(f"\n## Tactics:")
            for team, tactic in tactics.items():
                prompt_parts.append(f"- {team}: {json.dumps(tactic, ensure_ascii=False)}")

        # Add matched narratives (if available)
        if matched_narratives:
            prompt_parts.append(f"\n## Matched Narrative Templates:")
            for narrative in matched_narratives[:3]:
                prompt_parts.append(f"- {narrative}")

        # Instructions
        prompt_parts.append("\n## Requirements:")
        prompt_parts.append("1. Create 5-7 DISTINCT scenarios (different outcomes)")
        prompt_parts.append("2. Each scenario should tell a different story")
        prompt_parts.append("3. Use minute_range to specify when events occur")
        prompt_parts.append("4. Use probability_boost (1.0-3.0) to reflect user insights")
        prompt_parts.append("5. Include parameter_adjustments for player/team modifiers")
        prompt_parts.append("6. Sum of expected_probability should be ~1.0")

        prompt_parts.append("\n## Examples of diverse scenarios:")
        prompt_parts.append("- Scenario 1: Early goal → defensive play → hold lead")
        prompt_parts.append("- Scenario 2: Slow start → late comeback")
        prompt_parts.append("- Scenario 3: Dominant performance → big win")
        prompt_parts.append("- Scenario 4: Tight match → draw")
        prompt_parts.append("- Scenario 5: Counter-attack master class → away win")

        prompt_parts.append("\nGenerate scenarios in the JSON format above. ONLY JSON, nothing else.")

        return "\n".join(prompt_parts)

    def _parse_scenarios(
        self,
        response_text: str,
        match_context: Dict
    ) -> Optional[List[Scenario]]:
        """
        AI 응답을 Scenario 객체 리스트로 파싱
        """
        try:
            # Extract JSON
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
        """
        딕셔너리를 Scenario 객체로 변환
        """
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

        # Check distinctness (basic check)
        names = [s.name for s in scenarios]
        if len(names) != len(set(names)):
            return False, "Duplicate scenario names detected"

        # All checks passed
        return True, None


# Global instance
_scenario_generator = None


def get_scenario_generator(model: str = "qwen2.5:32b") -> AIScenarioGenerator:
    """Get global scenario generator instance (singleton)."""
    global _scenario_generator
    if _scenario_generator is None:
        _scenario_generator = AIScenarioGenerator(model=model)
    return _scenario_generator
