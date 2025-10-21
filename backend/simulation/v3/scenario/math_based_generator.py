"""
Math-Based Scenario Generator V3

수학적 모델 결과를 기반으로 AI가 시나리오 생성:
1. Ensemble probabilities → AI input
2. User commentary → Narrative only
3. Dynamic scenario count (2-5개)
4. NO Templates, NO EPL forcing

100% 사용자 도메인 데이터 기반
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from dataclasses import dataclass
from typing import List, Dict, Optional
import json
import logging

from ai.enriched_data_models import EnrichedTeamInput
from simulation.v2.scenario import Scenario, ScenarioEvent, EventType

# Import AI client
from ai.ai_factory import get_ai_client

# Import ensemble
try:
    from ..models.model_ensemble import EnsembleResult
except ImportError:
    # For standalone execution
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "model_ensemble",
        os.path.join(os.path.dirname(__file__), '../models/model_ensemble.py')
    )
    model_ensemble = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model_ensemble)
    EnsembleResult = model_ensemble.EnsembleResult

logger = logging.getLogger(__name__)


@dataclass
class GeneratedScenarioResult:
    """AI 생성 시나리오 결과"""
    scenarios: List[Scenario]
    reasoning: str                  # AI의 reasoning (왜 이 시나리오들?)
    scenario_count: int             # 생성된 시나리오 개수
    raw_response: Dict              # AI 원본 응답 (디버깅용)


class MathBasedScenarioGenerator:
    """
    Math-Based Scenario Generator

    수학적 모델 (Ensemble) 결과를 AI에게 전달:
    1. Ensemble probabilities
    2. Expected goals
    3. Zone dominance
    4. Key player influences

    AI가 2-5개 시나리오를 동적으로 생성:
    - 확률은 수학 모델에서
    - 스토리는 user commentary에서
    """

    def __init__(self, ai_client=None):
        """
        Initialize Math-Based Scenario Generator

        Args:
            ai_client: AI client (Gemini, Claude, etc.)
        """
        self.ai_client = ai_client or get_ai_client()
        logger.info(f"[ScenarioGen] Initialized with {self.ai_client.__class__.__name__}")

    def generate(self,
                 home_team: EnrichedTeamInput,
                 away_team: EnrichedTeamInput,
                 ensemble_result: EnsembleResult) -> GeneratedScenarioResult:
        """
        수학 모델 기반 시나리오 생성

        Args:
            home_team: 홈팀 데이터
            away_team: 원정팀 데이터
            ensemble_result: Ensemble 결과 (확률, xG, zone, player)

        Returns:
            GeneratedScenarioResult with 2-5 scenarios
        """
        logger.info(f"[ScenarioGen] Generating scenarios for {home_team.name} vs {away_team.name}")

        # 1. Build AI prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(home_team, away_team, ensemble_result)

        logger.debug(f"[ScenarioGen] System prompt length: {len(system_prompt)} chars")
        logger.debug(f"[ScenarioGen] User prompt length: {len(user_prompt)} chars")

        # 2. Call AI
        logger.info("[ScenarioGen] Calling AI to generate scenarios...")

        try:
            # Call AI (returns tuple: success, response_text, usage, error)
            success, response_text, usage, error = self.ai_client.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.8,  # More creative
                max_tokens=4000
            )

            if not success:
                raise ValueError(f"AI generation failed: {error}")

            # Convert response to dict format
            response = {'content': response_text}

            logger.info("[ScenarioGen] AI response received")

        except Exception as e:
            logger.error(f"[ScenarioGen] AI call failed: {e}")
            raise

        # 3. Parse AI response
        scenarios, reasoning, scenario_count = self._parse_ai_response(
            response,
            home_team,
            away_team,
            ensemble_result
        )

        logger.info(f"[ScenarioGen] Generated {scenario_count} scenarios")

        return GeneratedScenarioResult(
            scenarios=scenarios,
            reasoning=reasoning,
            scenario_count=scenario_count,
            raw_response=response
        )

    def _build_system_prompt(self) -> str:
        """
        System prompt 생성

        Returns:
            System prompt (AI 역할 정의)
        """
        return """You are an expert football tactical analyst specializing in match prediction.

Your task: Generate 2-5 MOST LIKELY match scenarios based on mathematical analysis.

CRITICAL RULES:
1. Focus on HIGH PROBABILITY outcomes (>10%)
2. If one team is clearly stronger, generate fewer scenarios (2-3) focused on their win
3. If match is balanced, generate more scenarios (4-5) covering different outcomes
4. DO NOT force equal distribution of home/draw/away scenarios
5. DO NOT create unrealistic scenarios just to hit quotas
6. Use mathematical probabilities as PRIMARY guidance
7. Use user commentary for NARRATIVE ONLY (probabilities come from math)

Output Format: JSON with the following structure:
{
  "reasoning": "Why these specific scenarios were chosen based on mathematical analysis",
  "scenario_count": 3,
  "scenarios": [
    {
      "id": "MATH_001",
      "name": "Descriptive scenario name",
      "expected_probability": 0.35,
      "reasoning": "Why this scenario is likely based on math (zone control, xG, player influence)",
      "events": [
        {
          "minute_range": [15, 25],
          "type": "central_penetration",
          "team": "away",
          "actor": "Player Name",
          "probability_boost": 2.4,
          "reason": "Mathematical advantage (zone 62% control) + player quality (user commentary)"
        }
      ],
      "parameter_adjustments": {
        "shot_frequency_home": 1.0,
        "shot_frequency_away": 1.2
      }
    }
  ]
}

Event types available:
- goal
- shot_on_target
- shot_off_target
- central_penetration
- wing_attack
- set_piece
- counter_attack
- tactical_foul
- defensive_block
- possession_dominance
- pressing_intensity

Remember: Probabilities come from MATHEMATICAL MODELS, not templates!
"""

    def _build_user_prompt(self,
                           home_team: EnrichedTeamInput,
                           away_team: EnrichedTeamInput,
                           ensemble_result: EnsembleResult) -> str:
        """
        User prompt 생성 (수학 분석 + user commentary)

        Args:
            home_team: 홈팀 데이터
            away_team: 원정팀 데이터
            ensemble_result: Ensemble 결과

        Returns:
            User prompt
        """
        # Mathematical Analysis Section
        math_section = self._format_mathematical_analysis(ensemble_result, home_team, away_team)

        # User Domain Knowledge Section
        domain_section = self._format_user_domain_knowledge(home_team, away_team, ensemble_result)

        # Task Section
        task_section = self._format_task_instructions(ensemble_result)

        # Combine
        user_prompt = f"""# Match Analysis: {home_team.name} vs {away_team.name}

{math_section}

{domain_section}

{task_section}
"""

        return user_prompt

    def _format_mathematical_analysis(self,
                                       ensemble_result: EnsembleResult,
                                       home_team: EnrichedTeamInput,
                                       away_team: EnrichedTeamInput) -> str:
        """수학적 분석 결과 포맷팅"""

        probs = ensemble_result.ensemble_probabilities
        xG = ensemble_result.expected_goals

        output = f"""## Mathematical Analysis Results

### Ensemble Probabilities (Weighted 0.4/0.3/0.3)
- **Home win**: {probs['home_win']:.1%}
- **Draw**: {probs['draw']:.1%}
- **Away win**: {probs['away_win']:.1%}

### Expected Goals (Weighted Average)
- **Home ({home_team.name})**: {xG['home']:.2f}
- **Away ({away_team.name})**: {xG['away']:.2f}
"""

        # Zone Dominance
        zone_summary = ensemble_result.zone_dominance_summary
        if zone_summary['home_strengths'] or zone_summary['away_strengths']:
            output += f"""
### Zone Dominance (9 zones)
- **Home dominant zones**: {', '.join(zone_summary['home_strengths']) if zone_summary['home_strengths'] else 'None'}
- **Away dominant zones**: {', '.join(zone_summary['away_strengths']) if zone_summary['away_strengths'] else 'None'}
- **Attack control**: Home {zone_summary['attack_control']['home']:.1%}, Away {zone_summary['attack_control']['away']:.1%}
"""

        # Key Players
        if ensemble_result.key_player_impacts:
            output += "\n### Key Player Influences\n"
            for impact in ensemble_result.key_player_impacts:
                output += f"- **{impact['player']}** ({impact['team']}): influence {impact['influence']:.1f}/10\n"

        # Tactical Insights
        insights = ensemble_result.tactical_insights
        output += f"""
### Tactical Insights
- **Formation matchup**: {insights['formation_matchup']}
- **Critical zones**: {insights['critical_zones']}
- **Key matchup**: {insights['key_matchup']}
"""

        return output

    def _format_user_domain_knowledge(self,
                                       home_team: EnrichedTeamInput,
                                       away_team: EnrichedTeamInput,
                                       ensemble_result: EnsembleResult) -> str:
        """User domain knowledge 포맷팅 (스토리용)"""

        output = """## User Domain Knowledge (for narrative only)

### Team Strategies
"""

        # Team strategies
        if home_team.team_strategy_commentary:
            output += f"**{home_team.name}**: {home_team.team_strategy_commentary}\n\n"
        if away_team.team_strategy_commentary:
            output += f"**{away_team.name}**: {away_team.team_strategy_commentary}\n\n"

        # Key players commentary
        output += "### Key Players Commentary\n"

        # Top home players
        home_top_players = sorted(
            home_team.lineup.values(),
            key=lambda p: p.overall_rating,
            reverse=True
        )[:3]

        for player in home_top_players:
            if player.user_commentary:
                output += f"**{player.name}** ({player.sub_position or player.position}, {home_team.name}):\n"
                output += f"{player.user_commentary}\n\n"

        # Top away players
        away_top_players = sorted(
            away_team.lineup.values(),
            key=lambda p: p.overall_rating,
            reverse=True
        )[:3]

        for player in away_top_players:
            if player.user_commentary:
                output += f"**{player.name}** ({player.sub_position or player.position}, {away_team.name}):\n"
                output += f"{player.user_commentary}\n\n"

        # Formation tactics
        output += "### Formation Tactics\n"
        if home_team.formation_tactics:
            output += f"**{home_team.name} ({home_team.formation})**:\n"
            output += f"- **Strengths**: {', '.join(home_team.formation_tactics.strengths)}\n"
            output += f"- **Weaknesses**: {', '.join(home_team.formation_tactics.weaknesses)}\n\n"

        if away_team.formation_tactics:
            output += f"**{away_team.name} ({away_team.formation})**:\n"
            output += f"- **Strengths**: {', '.join(away_team.formation_tactics.strengths)}\n"
            output += f"- **Weaknesses**: {', '.join(away_team.formation_tactics.weaknesses)}\n\n"

        return output

    def _format_task_instructions(self, ensemble_result: EnsembleResult) -> str:
        """Task instructions 포맷팅"""

        probs = ensemble_result.ensemble_probabilities

        # Determine dominant outcome
        max_prob = max(probs.values())
        dominant_outcome = [k for k, v in probs.items() if v == max_prob][0]

        output = f"""## Task

Generate 2-5 scenarios focusing on MOST LIKELY outcomes based on mathematical analysis.

### Guidelines:
1. **Primary focus**: {dominant_outcome.replace('_', ' ').title()} ({max_prob:.1%} probability)
   - Create 1-2 scenarios for this outcome with different narratives
2. **Secondary outcomes**: Include other outcomes if probability > 15%
3. **Total scenarios**: 2-5 (fewer if match is one-sided, more if balanced)
4. **Probabilities**: Should reflect mathematical analysis (don't force equal distribution!)

### Each scenario needs:
- **Events** reflecting mathematical advantages (zone control, key players, xG)
- **probability_boost** based on zone/player advantages (1.0-3.0 range)
- **Narrative** using user commentary for storytelling
- **parameter_adjustments** to guide simulation engine

### Important:
- If away_win > 50%, create 2-3 away win scenarios with DIFFERENT narratives
- If home_win and away_win are close (<10% difference), create balanced set
- Include lower probability scenarios ONLY if >10% and realistic

Return valid JSON following the exact format specified in system prompt.
"""

        return output

    def _parse_ai_response(self,
                           response: Dict,
                           home_team: EnrichedTeamInput,
                           away_team: EnrichedTeamInput,
                           ensemble_result: EnsembleResult) -> tuple:
        """
        AI 응답 파싱 → Scenario 객체 생성

        Args:
            response: AI raw response
            home_team: 홈팀
            away_team: 원정팀
            ensemble_result: Ensemble 결과

        Returns:
            (scenarios: List[Scenario], reasoning: str, count: int)
        """
        try:
            # Extract JSON from response
            content = response.get('content', '')

            # Try to extract JSON from markdown code blocks
            if '```json' in content:
                json_start = content.find('```json') + 7
                json_end = content.find('```', json_start)
                json_str = content[json_start:json_end].strip()
            elif '```' in content:
                json_start = content.find('```') + 3
                json_end = content.find('```', json_start)
                json_str = content[json_start:json_end].strip()
            else:
                json_str = content.strip()

            # Parse JSON
            data = json.loads(json_str)

            reasoning = data.get('reasoning', 'No reasoning provided')
            scenario_count = data.get('scenario_count', 0)
            scenarios_data = data.get('scenarios', [])

            logger.info(f"[ScenarioGen] Parsed {len(scenarios_data)} scenarios from AI response")

            # Convert to Scenario objects
            scenarios = []
            for scenario_data in scenarios_data:
                scenario = self._create_scenario_from_data(
                    scenario_data,
                    home_team,
                    away_team
                )
                scenarios.append(scenario)

            return scenarios, reasoning, scenario_count

        except Exception as e:
            logger.error(f"[ScenarioGen] Failed to parse AI response: {e}")
            logger.error(f"[ScenarioGen] Response content: {response.get('content', '')[:500]}")
            raise ValueError(f"Failed to parse AI response: {e}")

    def _create_scenario_from_data(self,
                                    data: Dict,
                                    home_team: EnrichedTeamInput,
                                    away_team: EnrichedTeamInput) -> Scenario:
        """
        JSON data → Scenario 객체 변환

        Args:
            data: AI scenario data
            home_team: 홈팀
            away_team: 원정팀

        Returns:
            Scenario object
        """
        # Create events
        events = []
        for event_data in data.get('events', []):
            # Convert string type to EventType enum
            event_type_str = event_data['type'].lower()
            event_type = self._parse_event_type(event_type_str)

            event = ScenarioEvent(
                minute_range=tuple(event_data['minute_range']),
                type=event_type,
                team=event_data['team'],
                actor=event_data.get('actor', None),
                method=event_data.get('method', None),
                probability_boost=event_data.get('probability_boost', 1.0),
                reason=event_data.get('reason', ''),
                trigger=event_data.get('trigger', None),
                to=event_data.get('to', None)
            )
            events.append(event)

        # Create scenario
        scenario = Scenario(
            id=data['id'],
            name=data['name'],
            expected_probability=data['expected_probability'],
            events=events,
            parameter_adjustments=data.get('parameter_adjustments', {}),
            reasoning=data.get('reasoning', '')
        )

        return scenario

    def _parse_event_type(self, event_type_str: str) -> EventType:
        """
        String → EventType enum 변환

        Args:
            event_type_str: Event type string (e.g., "goal", "central_penetration")

        Returns:
            EventType enum
        """
        # Normalize
        event_type_str = event_type_str.lower().replace('-', '_')

        # Map common variations
        type_mapping = {
            'goal': EventType.GOAL,
            'shot_on_target': EventType.SHOT_ON_TARGET,
            'shot_off_target': EventType.SHOT_OFF_TARGET,
            'central_penetration': EventType.CENTRAL_PENETRATION,
            'wing_attack': EventType.WING_BREAKTHROUGH,
            'wing_breakthrough': EventType.WING_BREAKTHROUGH,
            'corner': EventType.CORNER,
            'set_piece': EventType.CORNER,  # Map to corner
            'formation_change': EventType.FORMATION_CHANGE,
            'substitution': EventType.SUBSTITUTION,
            'foul': EventType.FOUL,
            'tactical_foul': EventType.FOUL,
            'yellow_card': EventType.YELLOW_CARD,
            'red_card': EventType.RED_CARD,
        }

        if event_type_str in type_mapping:
            return type_mapping[event_type_str]

        # Default to SHOT_ON_TARGET if unknown
        logger.warning(f"[ScenarioGen] Unknown event type: {event_type_str}, defaulting to SHOT_ON_TARGET")
        return EventType.SHOT_ON_TARGET


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)

    from services.enriched_data_loader import EnrichedDomainDataLoader

    # Import ensemble
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "model_ensemble",
        "/Users/stlee/Desktop/EPL-Match-Predictor/backend/simulation/v3/models/model_ensemble.py"
    )
    model_ensemble = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model_ensemble)

    loader = EnrichedDomainDataLoader()
    arsenal = loader.load_team_data("Arsenal")
    liverpool = loader.load_team_data("Liverpool")

    # Run ensemble
    ensemble = model_ensemble.ModelEnsemble()
    ensemble_result = ensemble.calculate(arsenal, liverpool)

    # Generate scenarios
    generator = MathBasedScenarioGenerator()
    result = generator.generate(arsenal, liverpool, ensemble_result)

    print("\n" + "="*80)
    print("Math-Based Scenario Generation Test")
    print("="*80)
    print(f"\nReasoning: {result.reasoning}")
    print(f"Scenario count: {result.scenario_count}")
    print(f"\nScenarios:")
    for scenario in result.scenarios:
        print(f"\n  {scenario.id}: {scenario.name}")
        print(f"    Probability: {scenario.expected_probability:.1%}")
        print(f"    Events: {len(scenario.events)}")
        print(f"    Reasoning: {scenario.reasoning[:100]}...")
    print()
