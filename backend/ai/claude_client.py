"""
Claude API Client
AI Match Simulation v3.0

Wrapper for Anthropic Claude API with tier-based model selection and token tracking.
"""

import anthropic
from typing import Dict, Optional, Tuple, List
import logging
import time
from datetime import datetime

from config.claude_config import get_claude_config


# Configure logging
logger = logging.getLogger(__name__)


class ClaudeError(Exception):
    """Base exception for Claude API errors."""
    pass


class ClaudeAPIError(ClaudeError):
    """Error from Claude API."""
    pass


class ClaudeRateLimitError(ClaudeError):
    """Rate limit exceeded."""
    pass


class ClaudeClient:
    """
    Claude API client wrapper.

    Features:
    - Tier-based model selection (BASIC: Sonnet 3.5, PRO: Sonnet 4.5)
    - Automatic retries with exponential backoff
    - Token usage tracking
    - Cost calculation
    - Error handling
    """

    def __init__(self):
        """Initialize Claude client."""
        self.config = get_claude_config()

        # Validate configuration
        is_valid, error = self.config.validate()
        if not is_valid:
            logger.error(f"Claude configuration invalid: {error}")
            raise ClaudeError(f"Configuration error: {error}")

        # Initialize Anthropic client
        self.client = anthropic.Anthropic(api_key=self.config.api_key)

    # ============================================================================
    # CORE API METHODS
    # ============================================================================

    def generate(self, prompt: str, tier: str, system_prompt: Optional[str] = None,
                temperature: Optional[float] = None,
                max_tokens: Optional[int] = None) -> Tuple[bool, Optional[str], Optional[Dict], Optional[str]]:
        """
        Generate AI response using Claude.

        Args:
            prompt: User prompt
            tier: Subscription tier ('BASIC' or 'PRO')
            system_prompt: Optional system prompt
            temperature: Optional temperature override
            max_tokens: Optional max_tokens override

        Returns:
            Tuple of (success, response_text, usage_data, error_message)
            usage_data contains: {input_tokens, output_tokens, cost_usd}
        """
        if not self.config.enabled:
            return False, None, None, "Claude API is disabled"

        # Get model configuration
        model_config = self.config.get_model_config(tier)
        model = model_config['model']
        max_tokens = max_tokens or model_config['max_tokens']
        temperature = temperature or model_config['temperature']

        # Prepare messages
        messages = [
            {"role": "user", "content": prompt}
        ]

        # Retry logic
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                # Make API call
                response = self.client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_prompt if system_prompt else "You are an expert football analyst.",
                    messages=messages
                )

                # Extract response text
                response_text = response.content[0].text

                # Calculate usage and cost
                usage_data = {
                    'input_tokens': response.usage.input_tokens,
                    'output_tokens': response.usage.output_tokens,
                    'total_tokens': response.usage.input_tokens + response.usage.output_tokens,
                    'cost_usd': self.config.calculate_cost(
                        model,
                        response.usage.input_tokens,
                        response.usage.output_tokens
                    ),
                    'model': model,
                    'tier': tier
                }

                logger.info(f"Claude API call successful (tier={tier}, tokens={usage_data['total_tokens']}, cost=${usage_data['cost_usd']:.6f})")
                return True, response_text, usage_data, None

            except anthropic.RateLimitError as e:
                last_error = f"Rate limit exceeded: {str(e)}"
                logger.warning(f"Rate limit hit (attempt {attempt + 1}/{self.config.max_retries})")

                if attempt < self.config.max_retries - 1:
                    # Exponential backoff
                    wait_time = (2 ** attempt) * 1.0
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue

                return False, None, None, last_error

            except anthropic.APIError as e:
                last_error = f"API error: {str(e)}"
                logger.error(last_error)
                return False, None, None, last_error

            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                logger.error(last_error)
                return False, None, None, last_error

        return False, None, None, last_error

    def generate_streaming(self, prompt: str, tier: str, system_prompt: Optional[str] = None):
        """
        Generate streaming AI response (for future use).

        Args:
            prompt: User prompt
            tier: Subscription tier
            system_prompt: Optional system prompt

        Yields:
            Text chunks
        """
        if not self.config.enabled:
            raise ClaudeError("Claude API is disabled")

        model_config = self.config.get_model_config(tier)
        model = model_config['model']

        with self.client.messages.stream(
            model=model,
            max_tokens=model_config['max_tokens'],
            temperature=model_config['temperature'],
            system=system_prompt if system_prompt else "You are an expert football analyst.",
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            for text in stream.text_stream:
                yield text

    # ============================================================================
    # MATCH SIMULATION SPECIFIC
    # ============================================================================

    def simulate_match(self, home_team: str, away_team: str, tier: str,
                      data_context: Dict) -> Tuple[bool, Optional[Dict], Optional[Dict], Optional[str]]:
        """
        Simulate a match using Claude AI.

        Args:
            home_team: Home team name
            away_team: Away team name
            tier: User subscription tier
            data_context: Context data (squad info, form, odds, etc.)

        Returns:
            Tuple of (success, prediction_dict, usage_data, error_message)
        """
        # Build system prompt based on tier
        if tier == 'PRO':
            system_prompt = self._build_pro_system_prompt()
        else:
            system_prompt = self._build_basic_system_prompt()

        # Build user prompt with context
        user_prompt = self._build_match_prompt(home_team, away_team, data_context, tier)

        # Generate prediction
        success, response_text, usage_data, error = self.generate(
            prompt=user_prompt,
            tier=tier,
            system_prompt=system_prompt
        )

        if not success:
            return False, None, None, error

        # Parse response into structured prediction
        try:
            prediction = self._parse_match_prediction(response_text, home_team, away_team)
            return True, prediction, usage_data, None
        except Exception as e:
            error_msg = f"Failed to parse prediction: {str(e)}"
            logger.error(error_msg)
            return False, None, usage_data, error_msg

    # ============================================================================
    # PROMPT ENGINEERING
    # ============================================================================

    def _build_basic_system_prompt(self) -> str:
        """Build system prompt for BASIC tier."""
        return """You are an expert football match analyst with deep knowledge of the English Premier League.

Your role is to analyze matches and provide realistic predictions based on:
- Team form and recent performance
- Squad quality and player ratings
- Head-to-head history
- Tactical considerations

Provide balanced, data-driven analysis. Focus on the most important factors affecting match outcomes.

Format your response as JSON with the following structure:
{
  "prediction": {
    "home_win_probability": 0.45,
    "draw_probability": 0.30,
    "away_win_probability": 0.25,
    "predicted_score": "2-1",
    "confidence": "medium"
  },
  "analysis": {
    "key_factors": ["factor1", "factor2", "factor3"],
    "home_team_strengths": ["strength1", "strength2"],
    "away_team_strengths": ["strength1", "strength2"],
    "tactical_insight": "Brief tactical analysis"
  },
  "summary": "Concise match prediction summary (2-3 sentences)"
}

Ensure probabilities sum to 1.0. Confidence levels: low, medium, high."""

    def _build_pro_system_prompt(self) -> str:
        """Build system prompt for PRO tier."""
        return """You are an elite football match analyst with expertise in the English Premier League and professional sports betting analysis.

Your role is to provide comprehensive match predictions using:
- Advanced statistical analysis
- Team form and momentum
- Squad quality and key player availability
- Tactical matchups and style compatibility
- Head-to-head records
- Sharp bookmaker insights (when provided)
- Expected goals (xG) and other advanced metrics

Provide sophisticated, multi-layered analysis that considers both quantitative data and qualitative factors. Your predictions should align with sharp bookmaker consensus while adding unique analytical insights.

Format your response as JSON with the following structure:
{
  "prediction": {
    "home_win_probability": 0.45,
    "draw_probability": 0.30,
    "away_win_probability": 0.25,
    "predicted_score": "2-1",
    "confidence": "high",
    "expected_goals": {
      "home": 1.8,
      "away": 1.2
    }
  },
  "analysis": {
    "key_factors": ["detailed factor1", "detailed factor2", "detailed factor3"],
    "home_team_strengths": ["strength1", "strength2", "strength3"],
    "home_team_weaknesses": ["weakness1", "weakness2"],
    "away_team_strengths": ["strength1", "strength2", "strength3"],
    "away_team_weaknesses": ["weakness1", "weakness2"],
    "tactical_insight": "Detailed tactical analysis including formations and key battles",
    "sharp_alignment": "How prediction compares to sharp bookmaker lines",
    "value_assessment": "Betting value assessment"
  },
  "summary": "Comprehensive match prediction summary (3-4 sentences)",
  "recommendation": "Actionable recommendation for users"
}

Ensure probabilities sum to 1.0. Confidence levels: low, medium, high, very_high."""

    def _build_match_prompt(self, home_team: str, away_team: str,
                          data_context: Dict, tier: str) -> str:
        """Build user prompt for match simulation."""
        prompt_parts = [
            f"Analyze the upcoming match: {home_team} vs {away_team}\n"
        ]

        # Add data source weights prominently
        if 'weights' in data_context:
            weights = data_context['weights']
            user_pct = int(weights.get('user_value', 0.65) * 100)
            odds_pct = int(weights.get('odds', 0.20) * 100)
            stats_pct = int(weights.get('stats', 0.15) * 100)

            prompt_parts.append("\n**⚠️ CRITICAL: Data Source Weighting**")
            prompt_parts.append("You MUST prioritize data sources according to these weights:")
            prompt_parts.append(f"  🎯 User Player Ratings & Tactics: {user_pct}% (PRIMARY - Most Important)")
            prompt_parts.append(f"  📊 Bookmaker Odds Data: {odds_pct}%")
            prompt_parts.append(f"  📈 Statistical Data (Form, FPL): {stats_pct}%")
            prompt_parts.append("\nThe User Player Ratings are the MOST IMPORTANT factor. Give them significantly more weight in your analysis.\n")

        # Add data context based on what's available
        if 'squad_ratings' in data_context:
            prompt_parts.append("\n**Squad Quality:**")
            prompt_parts.append(f"Home ({home_team}): {data_context['squad_ratings'].get('home', 'N/A')}")
            prompt_parts.append(f"Away ({away_team}): {data_context['squad_ratings'].get('away', 'N/A')}")

        if 'recent_form' in data_context:
            prompt_parts.append("\n**Recent Form:**")
            prompt_parts.append(f"{home_team}: {data_context['recent_form'].get('home', 'N/A')}")
            prompt_parts.append(f"{away_team}: {data_context['recent_form'].get('away', 'N/A')}")

        if 'head_to_head' in data_context and tier == 'PRO':
            prompt_parts.append("\n**Head-to-Head:**")
            prompt_parts.append(str(data_context['head_to_head']))

        if 'sharp_odds' in data_context and tier == 'PRO':
            prompt_parts.append("\n**Sharp Bookmaker Odds (Pinnacle):**")
            prompt_parts.append(str(data_context['sharp_odds']))

        if 'league_position' in data_context:
            prompt_parts.append("\n**League Standings:**")
            prompt_parts.append(f"{home_team}: {data_context['league_position'].get('home', 'N/A')}")
            prompt_parts.append(f"{away_team}: {data_context['league_position'].get('away', 'N/A')}")

        # Remind about weights at the end
        if 'weights' in data_context:
            weights = data_context['weights']
            user_pct = int(weights.get('user_value', 0.65) * 100)
            prompt_parts.append(f"\n**REMINDER**: Your prediction must heavily reflect the User Player Ratings ({user_pct}%). This is the user's expert analysis and should be the foundation of your prediction.")

        prompt_parts.append("\nProvide your prediction in the specified JSON format.")

        return "\n".join(prompt_parts)

    def _parse_match_prediction(self, response_text: str, home_team: str,
                               away_team: str) -> Dict:
        """Parse Claude response into structured prediction."""
        import json
        import re

        # Extract JSON from response (handle markdown code blocks)
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON object directly
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise ValueError("No JSON found in response")

        # Parse JSON
        prediction = json.loads(json_str)

        # Add metadata
        prediction['metadata'] = {
            'home_team': home_team,
            'away_team': away_team,
            'generated_at': datetime.utcnow().isoformat(),
            'raw_response': response_text
        }

        return prediction


# Global client instance
_claude_client = None


def get_claude_client() -> ClaudeClient:
    """Get global Claude client instance (singleton)."""
    global _claude_client
    if _claude_client is None:
        _claude_client = ClaudeClient()
    return _claude_client
