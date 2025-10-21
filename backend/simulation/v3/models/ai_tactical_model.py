"""
AI Tactical Model

AI의 tactical reasoning을 활용한 4번째 앙상블 모델:
1. User commentary 실질 반영 (심리, 폼, 맥락)
2. Tactical nuance 포착 (수학 모델이 놓친 것)
3. 매번 다른 insight 제공 (현실적 variation)

수학 모델(Poisson/Zone/Player)과 동등한 weight로 Ensemble에 통합
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from dataclasses import dataclass
from typing import Dict, List, Optional
import json
import logging

from ai.enriched_data_models import EnrichedTeamInput
from ai.ai_factory import get_ai_client

logger = logging.getLogger(__name__)


@dataclass
class AITacticalResult:
    """AI Tactical 모델 출력"""
    probabilities: Dict[str, float]      # {home_win, draw, away_win}
    reasoning: str                        # AI의 tactical reasoning
    key_insights: List[str]               # 핵심 인사이트 (3-5개)
    confidence: float                     # AI 자신의 confidence (0-1)
    context_factors: Dict[str, str]       # 맥락 요소들


class AITacticalModel:
    """
    AI Tactical Model

    AI가 user commentary와 tactical context를 분석하여 확률 생성:
    - 수학 모델이 놓친 tactical nuance
    - User commentary의 실질적 반영
    - 심리적/맥락적 요소 고려

    매번 다른 결과를 생성할 수 있음 (temperature=0.7) → 현실적 variation
    """

    def __init__(self, ai_client=None):
        """
        Initialize AI Tactical Model

        Args:
            ai_client: AI client (Gemini, Claude, etc.)
        """
        self.ai_client = ai_client or get_ai_client()
        logger.info(f"[AI Tactical] Initialized with {self.ai_client.__class__.__name__}")

    def calculate(self,
                  home_team: EnrichedTeamInput,
                  away_team: EnrichedTeamInput,
                  math_reference: Optional[Dict[str, float]] = None) -> AITacticalResult:
        """
        AI Tactical 분석

        Args:
            home_team: 홈팀 데이터
            away_team: 원정팀 데이터
            math_reference: 수학 모델 확률 (reference로만 사용)

        Returns:
            AITacticalResult with probabilities and reasoning
        """
        logger.info(f"[AI Tactical] Analyzing {home_team.name} vs {away_team.name}")

        # Build AI prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(home_team, away_team, math_reference)

        # Call AI
        logger.debug("[AI Tactical] Calling AI for tactical analysis...")

        try:
            success, response_text, usage, error = self.ai_client.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.7,  # Allow variation (realistic)
                max_tokens=2000
            )

            if not success:
                raise ValueError(f"AI generation failed: {error}")

            logger.info(f"[AI Tactical] AI response received ({usage['total_tokens']} tokens)")

            # Parse response
            result = self._parse_response(response_text)

            logger.info(f"[AI Tactical] Probabilities: "
                       f"Home {result.probabilities['home_win']:.1%}, "
                       f"Draw {result.probabilities['draw']:.1%}, "
                       f"Away {result.probabilities['away_win']:.1%}")

            return result

        except Exception as e:
            logger.error(f"[AI Tactical] Error: {e}")
            # Fallback: return neutral probabilities
            return AITacticalResult(
                probabilities={'home_win': 0.33, 'draw': 0.34, 'away_win': 0.33},
                reasoning=f"AI tactical analysis failed: {str(e)}",
                key_insights=["Analysis unavailable"],
                confidence=0.0,
                context_factors={}
            )

    def _build_system_prompt(self) -> str:
        """Build system prompt for AI tactical analysis"""
        return """You are an expert football tactical analyst with deep understanding of the game.

Your role: Analyze matches from a tactical and psychological perspective, considering factors that mathematical models cannot capture.

Focus on:
- Tactical matchups and formations
- Psychological factors (form, pressure, motivation)
- Player form and injury concerns
- Team dynamics and morale
- Recent performance context
- Home advantage nuances

IMPORTANT: You MUST respond with ONLY a valid JSON object. No text before or after.

Output format:
{
  "probabilities": {
    "home_win": 0.45,
    "draw": 0.30,
    "away_win": 0.25
  },
  "reasoning": "Detailed tactical reasoning (2-3 sentences)",
  "key_insights": [
    "Insight 1",
    "Insight 2",
    "Insight 3"
  ],
  "confidence": 0.75,
  "context_factors": {
    "psychological": "Description",
    "tactical": "Description",
    "form": "Description"
  }
}

Requirements:
- Probabilities MUST sum to 1.0 (±0.01)
- confidence: 0.0-1.0
- key_insights: 3-5 items
- Consider user commentary seriously (they know the teams)
- Be realistic, not biased

ONLY return the JSON. Nothing else."""

    def _build_user_prompt(self,
                           home_team: EnrichedTeamInput,
                           away_team: EnrichedTeamInput,
                           math_reference: Optional[Dict[str, float]]) -> str:
        """Build user prompt with team data and commentary"""

        prompt_parts = [
            f"# Tactical Analysis: {home_team.name} vs {away_team.name}\n"
        ]

        # Math reference (for context only)
        if math_reference:
            prompt_parts.append("## Mathematical Models Reference (for context)")
            prompt_parts.append(f"- Poisson/Zone/Player models predict: "
                              f"Home {math_reference.get('home_win', 0):.1%}, "
                              f"Draw {math_reference.get('draw', 0):.1%}, "
                              f"Away {math_reference.get('away_win', 0):.1%}")
            prompt_parts.append("(You can agree or disagree based on tactical analysis)\n")

        # Team strengths
        prompt_parts.append("## Team Strengths (Derived from user input)")
        prompt_parts.append(f"**{home_team.name} (Home)**:")
        prompt_parts.append(f"- Attack: {home_team.derived_strengths.attack_strength:.1f}/100")
        prompt_parts.append(f"- Defense: {home_team.derived_strengths.defense_strength:.1f}/100")
        prompt_parts.append(f"- Midfield: {home_team.derived_strengths.midfield_control:.1f}/100")
        prompt_parts.append(f"- Physical: {home_team.derived_strengths.physical_intensity:.1f}/100\n")

        prompt_parts.append(f"**{away_team.name} (Away)**:")
        prompt_parts.append(f"- Attack: {away_team.derived_strengths.attack_strength:.1f}/100")
        prompt_parts.append(f"- Defense: {away_team.derived_strengths.defense_strength:.1f}/100")
        prompt_parts.append(f"- Midfield: {away_team.derived_strengths.midfield_control:.1f}/100")
        prompt_parts.append(f"- Physical: {away_team.derived_strengths.physical_intensity:.1f}/100\n")

        # User commentary (CRITICAL)
        prompt_parts.append("## User Commentary (CRITICAL - User knows these teams well)")

        if home_team.team_strategy_commentary:
            prompt_parts.append(f"\n**{home_team.name} Strategy**:")
            prompt_parts.append(home_team.team_strategy_commentary)

        if away_team.team_strategy_commentary:
            prompt_parts.append(f"\n**{away_team.name} Strategy**:")
            prompt_parts.append(away_team.team_strategy_commentary)

        # Key players with commentary
        prompt_parts.append("\n**Key Players & User Insights**:")

        # Top 3 home players
        home_top_players = sorted(
            home_team.lineup.values(),
            key=lambda p: p.overall_rating,
            reverse=True
        )[:3]

        for player in home_top_players:
            prompt_parts.append(f"\n{player.name} ({player.sub_position or player.position}, {home_team.name}):")
            prompt_parts.append(f"  Rating: {player.overall_rating:.2f}/5")
            if player.user_commentary:
                prompt_parts.append(f"  User: {player.user_commentary}")

        # Top 3 away players
        away_top_players = sorted(
            away_team.lineup.values(),
            key=lambda p: p.overall_rating,
            reverse=True
        )[:3]

        for player in away_top_players:
            prompt_parts.append(f"\n{player.name} ({player.sub_position or player.position}, {away_team.name}):")
            prompt_parts.append(f"  Rating: {player.overall_rating:.2f}/5")
            if player.user_commentary:
                prompt_parts.append(f"  User: {player.user_commentary}")

        # Formation tactics
        prompt_parts.append("\n## Tactical Setup")

        if home_team.formation_tactics:
            prompt_parts.append(f"\n**{home_team.name} ({home_team.formation})**:")
            prompt_parts.append(f"- Style: {home_team.formation_tactics.style}")
            prompt_parts.append(f"- Strengths: {', '.join(home_team.formation_tactics.strengths)}")
            prompt_parts.append(f"- Weaknesses: {', '.join(home_team.formation_tactics.weaknesses)}")

        if away_team.formation_tactics:
            prompt_parts.append(f"\n**{away_team.name} ({away_team.formation})**:")
            prompt_parts.append(f"- Style: {away_team.formation_tactics.style}")
            prompt_parts.append(f"- Strengths: {', '.join(away_team.formation_tactics.strengths)}")
            prompt_parts.append(f"- Weaknesses: {', '.join(away_team.formation_tactics.weaknesses)}")

        # Task
        prompt_parts.append("\n## Your Task")
        prompt_parts.append("Analyze this match from a tactical and psychological perspective.")
        prompt_parts.append("Consider:")
        prompt_parts.append("1. Formation matchup and tactical advantages")
        prompt_parts.append("2. Key player matchups and form")
        prompt_parts.append("3. Team morale and psychological factors (from user commentary)")
        prompt_parts.append("4. Home advantage impact")
        prompt_parts.append("5. Tactical weaknesses to exploit")
        prompt_parts.append("\nProvide your probability assessment in the JSON format above.")
        prompt_parts.append("ONLY return JSON. No other text.")

        return "\n".join(prompt_parts)

    def _parse_response(self, response_text: str) -> AITacticalResult:
        """Parse AI response to AITacticalResult"""

        try:
            # Extract JSON
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                json_str = response_text[json_start:json_end].strip()
            elif '```' in response_text:
                json_start = response_text.find('```') + 3
                json_end = response_text.find('```', json_start)
                json_str = response_text[json_start:json_end].strip()
            else:
                json_str = response_text.strip()

            # Parse JSON
            data = json.loads(json_str)

            # Extract fields
            probabilities = data.get('probabilities', {})
            reasoning = data.get('reasoning', 'No reasoning provided')
            key_insights = data.get('key_insights', [])
            confidence = data.get('confidence', 0.5)
            context_factors = data.get('context_factors', {})

            # Validate probabilities
            prob_sum = sum(probabilities.values())
            if not (0.99 <= prob_sum <= 1.01):
                logger.warning(f"[AI Tactical] Probability sum {prob_sum:.3f} != 1.0, normalizing...")
                # Normalize
                probabilities = {
                    k: v / prob_sum for k, v in probabilities.items()
                }

            return AITacticalResult(
                probabilities=probabilities,
                reasoning=reasoning,
                key_insights=key_insights,
                confidence=confidence,
                context_factors=context_factors
            )

        except Exception as e:
            logger.error(f"[AI Tactical] Failed to parse response: {e}")
            logger.error(f"[AI Tactical] Response: {response_text[:500]}")
            raise ValueError(f"Failed to parse AI tactical response: {e}")


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)

    from services.enriched_data_loader import EnrichedDomainDataLoader

    loader = EnrichedDomainDataLoader()
    arsenal = loader.load_team_data("Arsenal")
    liverpool = loader.load_team_data("Liverpool")

    model = AITacticalModel()

    # Math reference (예시)
    math_reference = {
        'home_win': 0.28,
        'draw': 0.255,
        'away_win': 0.465
    }

    result = model.calculate(arsenal, liverpool, math_reference)

    print("\n" + "="*80)
    print("AI Tactical Model Test")
    print("="*80)
    print(f"\nProbabilities:")
    print(f"  Home win: {result.probabilities['home_win']:.1%}")
    print(f"  Draw:     {result.probabilities['draw']:.1%}")
    print(f"  Away win: {result.probabilities['away_win']:.1%}")
    print(f"\nConfidence: {result.confidence:.1%}")
    print(f"\nReasoning:")
    print(f"  {result.reasoning}")
    print(f"\nKey Insights:")
    for i, insight in enumerate(result.key_insights, 1):
        print(f"  {i}. {insight}")
    print(f"\nContext Factors:")
    for factor, desc in result.context_factors.items():
        print(f"  {factor}: {desc}")
    print()
