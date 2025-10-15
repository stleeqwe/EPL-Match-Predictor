"""
Qwen Match Analyzer
AI-powered match analysis using local Qwen 2.5 32B model

Phase 1 MVP: Focus on analysis quality
- Uses existing Qwen client infrastructure
- Generates probability adjustments based on tactical insights
- Provides structured match analysis
"""

import json
import logging
import re
from typing import Dict, Optional, Tuple

from ai.ai_factory import get_ai_client

logger = logging.getLogger(__name__)


class QwenMatchAnalyzer:
    """
    AI-powered match analyzer using Qwen 2.5 32B.

    Features:
    - Tactical analysis based on team profiles
    - Player quality assessment
    - Form and momentum evaluation
    - Probability weight generation for statistical engine
    - Natural language match insights
    """

    def __init__(self):
        """Initialize Qwen analyzer."""
        self.ai_client = get_ai_client()
        logger.info("QwenMatchAnalyzer initialized")

    def analyze_match(
        self,
        home_team_data: Dict,
        away_team_data: Dict,
        additional_context: Optional[Dict] = None
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Analyze match using Qwen AI.

        Args:
            home_team_data: Home team data
                Format: {
                    'name': str,
                    'overall_rating': float,
                    'tactical_profile': dict,
                    'recent_form': str (optional),
                    'key_players': list (optional)
                }
            away_team_data: Away team data (same format)
            additional_context: Optional additional context
                Format: {
                    'user_insights': str,
                    'injuries': list,
                    'weather': str,
                    etc.
                }

        Returns:
            Tuple of (success, analysis_dict, error_message)
            analysis_dict format:
            {
                'probability_weights': {
                    'home_win_boost': float,
                    'draw_boost': float,
                    'away_win_boost': float
                },
                'key_factors': [str, str, str],
                'tactical_insight': str,
                'confidence': str,
                'reasoning': str
            }
        """
        logger.info(f"Analyzing {home_team_data['name']} vs {away_team_data['name']}")

        # Build analysis prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_analysis_prompt(
            home_team_data,
            away_team_data,
            additional_context
        )

        # Get AI analysis
        success, response_text, usage_data, error = self.ai_client.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.6,  # Slightly lower for more consistent analysis
            max_tokens=2048
        )

        if not success:
            logger.error(f"AI analysis failed: {error}")
            return False, None, error

        # Parse AI response
        try:
            analysis = self._parse_analysis(response_text, home_team_data, away_team_data)
            logger.info(f"Analysis complete: {analysis['probability_weights']}")
            return True, analysis, None
        except Exception as e:
            error_msg = f"Failed to parse analysis: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Raw response: {response_text[:500]}")
            return False, None, error_msg

    def _build_system_prompt(self) -> str:
        """Build system prompt for AI analyzer."""
        return """You are an expert football tactical analyst specializing in the English Premier League.

Your role is to analyze matches and provide:
1. Tactical insights based on team profiles and playing styles
2. Probability adjustments (boost factors) for match outcomes
3. Key factors that will influence the result
4. Clear reasoning for your assessment

IMPORTANT: You MUST respond with a valid JSON object. Do not include any text before or after the JSON.

Format your response EXACTLY like this:
{
  "probability_weights": {
    "home_win_boost": 1.2,
    "draw_boost": 0.9,
    "away_win_boost": 0.8
  },
  "key_factors": [
    "Factor 1 description",
    "Factor 2 description",
    "Factor 3 description"
  ],
  "tactical_insight": "Brief tactical analysis (2-3 sentences)",
  "confidence": "high",
  "reasoning": "Detailed explanation of your analysis (3-4 sentences)"
}

Notes:
- Probability boosts range from 0.5 to 1.5 (1.0 = neutral, >1.0 = favor, <1.0 = disfavor)
- The boosts should reflect relative advantages, not absolute probabilities
- Confidence levels: low, medium, high
- Focus on tactical matchups, team strengths/weaknesses, and playing styles"""

    def _build_analysis_prompt(
        self,
        home_team_data: Dict,
        away_team_data: Dict,
        additional_context: Optional[Dict]
    ) -> str:
        """Build user prompt for AI analysis."""
        prompt_parts = [
            f"Analyze this EPL match: {home_team_data['name']} (Home) vs {away_team_data['name']} (Away)\n"
        ]

        # Add team ratings
        prompt_parts.append("\n**Team Quality:**")
        prompt_parts.append(f"{home_team_data['name']}: Overall {home_team_data.get('overall_rating', 'N/A')}/100")
        prompt_parts.append(f"{away_team_data['name']}: Overall {away_team_data.get('overall_rating', 'N/A')}/100")

        # Add tactical profiles
        if 'tactical_profile' in home_team_data:
            prompt_parts.append(f"\n**{home_team_data['name']} Tactical Profile:**")
            for key, value in home_team_data['tactical_profile'].items():
                formatted_key = key.replace('_', ' ').title()
                prompt_parts.append(f"  - {formatted_key}: {value:.1f}/100")

        if 'tactical_profile' in away_team_data:
            prompt_parts.append(f"\n**{away_team_data['name']} Tactical Profile:**")
            for key, value in away_team_data['tactical_profile'].items():
                formatted_key = key.replace('_', ' ').title()
                prompt_parts.append(f"  - {formatted_key}: {value:.1f}/100")

        # Add recent form if available
        if 'recent_form' in home_team_data or 'recent_form' in away_team_data:
            prompt_parts.append("\n**Recent Form:**")
            if 'recent_form' in home_team_data:
                prompt_parts.append(f"{home_team_data['name']}: {home_team_data['recent_form']}")
            if 'recent_form' in away_team_data:
                prompt_parts.append(f"{away_team_data['name']}: {away_team_data['recent_form']}")

        # Add key players if available
        if 'key_players' in home_team_data:
            prompt_parts.append(f"\n**{home_team_data['name']} Key Players:**")
            for player in home_team_data['key_players'][:3]:  # Top 3
                prompt_parts.append(f"  - {player}")

        if 'key_players' in away_team_data:
            prompt_parts.append(f"\n**{away_team_data['name']} Key Players:**")
            for player in away_team_data['key_players'][:3]:  # Top 3
                prompt_parts.append(f"  - {player}")

        # Add additional context
        if additional_context:
            if 'user_insights' in additional_context and additional_context['user_insights']:
                prompt_parts.append(f"\n**User Insights:**")
                prompt_parts.append(additional_context['user_insights'])

            if 'injuries' in additional_context and additional_context['injuries']:
                prompt_parts.append(f"\n**Injuries:**")
                for injury in additional_context['injuries']:
                    prompt_parts.append(f"  - {injury}")

            if 'weather' in additional_context:
                prompt_parts.append(f"\n**Weather Conditions:** {additional_context['weather']}")

        prompt_parts.append("\n**Task:**")
        prompt_parts.append("Provide tactical analysis and probability adjustments in JSON format.")
        prompt_parts.append("Focus on how tactical profiles and playing styles will affect the outcome.")
        prompt_parts.append("ONLY return the JSON, nothing else.")

        return "\n".join(prompt_parts)

    def _parse_analysis(
        self,
        response_text: str,
        home_team_data: Dict,
        away_team_data: Dict
    ) -> Dict:
        """Parse AI response into structured analysis."""
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = response_text.strip()

        try:
            analysis = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing failed: {e}")
            # Return default analysis if parsing fails
            analysis = self._get_default_analysis(home_team_data, away_team_data)

        # Validate and normalize probability weights
        if 'probability_weights' not in analysis:
            analysis['probability_weights'] = {
                'home_win_boost': 1.0,
                'draw_boost': 1.0,
                'away_win_boost': 1.0
            }
        else:
            weights = analysis['probability_weights']
            # Clamp boosts to reasonable range (0.5 - 1.5)
            weights['home_win_boost'] = max(0.5, min(1.5, weights.get('home_win_boost', 1.0)))
            weights['draw_boost'] = max(0.5, min(1.5, weights.get('draw_boost', 1.0)))
            weights['away_win_boost'] = max(0.5, min(1.5, weights.get('away_win_boost', 1.0)))

        # Ensure required fields exist
        if 'key_factors' not in analysis or not analysis['key_factors']:
            analysis['key_factors'] = ["Analysis based on team ratings", "Tactical profile comparison", "Home advantage"]

        if 'tactical_insight' not in analysis:
            analysis['tactical_insight'] = "Match analysis based on team profiles and current form."

        if 'confidence' not in analysis:
            analysis['confidence'] = 'medium'

        if 'reasoning' not in analysis:
            analysis['reasoning'] = "Probability adjustments based on tactical analysis and team strengths."

        # Add metadata
        analysis['metadata'] = {
            'analyzer': 'QwenMatchAnalyzer',
            'model': 'qwen2.5:32b',
            'home_team': home_team_data['name'],
            'away_team': away_team_data['name']
        }

        return analysis

    def _get_default_analysis(
        self,
        home_team_data: Dict,
        away_team_data: Dict
    ) -> Dict:
        """Get default analysis when AI parsing fails."""
        # Calculate simple boost based on rating difference
        home_rating = home_team_data.get('overall_rating', 75.0)
        away_rating = away_team_data.get('overall_rating', 75.0)
        rating_diff = home_rating - away_rating

        # Simple boost: +0.1 for every 10 rating points
        home_boost = 1.0 + (rating_diff / 100.0)
        away_boost = 1.0 - (rating_diff / 100.0)
        home_boost = max(0.5, min(1.5, home_boost))
        away_boost = max(0.5, min(1.5, away_boost))

        return {
            'probability_weights': {
                'home_win_boost': round(home_boost, 2),
                'draw_boost': 1.0,
                'away_win_boost': round(away_boost, 2)
            },
            'key_factors': [
                f"Team quality difference: {home_team_data['name']} {home_rating:.1f} vs {away_team_data['name']} {away_rating:.1f}",
                "Home advantage in the Premier League",
                "Standard tactical setup analysis"
            ],
            'tactical_insight': f"Default analysis based on team ratings. {home_team_data['name']} rated {home_rating:.1f}/100 vs {away_team_data['name']} at {away_rating:.1f}/100.",
            'confidence': 'low',
            'reasoning': 'Analysis generated from default algorithm due to AI parsing error.'
        }

    def analyze_with_user_insight(
        self,
        home_team_data: Dict,
        away_team_data: Dict,
        user_insight: str
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Analyze match with user-provided insights.

        This gives higher weight to user domain knowledge as per MVP requirements.

        Args:
            home_team_data: Home team data
            away_team_data: Away team data
            user_insight: User's match analysis/insights

        Returns:
            Tuple of (success, analysis_dict, error_message)
        """
        additional_context = {
            'user_insights': user_insight
        }

        return self.analyze_match(home_team_data, away_team_data, additional_context)


# Global analyzer instance
_qwen_analyzer = None


def get_qwen_analyzer() -> QwenMatchAnalyzer:
    """Get global Qwen analyzer instance (singleton)."""
    global _qwen_analyzer
    if _qwen_analyzer is None:
        _qwen_analyzer = QwenMatchAnalyzer()
    return _qwen_analyzer
