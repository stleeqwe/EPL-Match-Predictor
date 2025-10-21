"""
Gemini AI Client (Google)
Production-ready AI client using Google Gemini 2.5 Flash with Thinking Mode
"""

import google.generativeai as genai
import json
import logging
import re
import os
from typing import Dict, Optional, Tuple
from datetime import datetime

from ai.base_client import BaseAIClient

logger = logging.getLogger(__name__)


class GeminiClient(BaseAIClient):
    """
    Gemini AI client using Google's Generative AI API.

    Supports:
    - Gemini 2.5 Flash with Thinking Mode
    - Configurable thinking budget (0-24576 tokens)
    - Fast response times (~5-20 seconds)
    - Production-grade quality
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.5-flash",
        thinking_budget: int = 8000
    ):
        """
        Initialize Gemini client.

        Args:
            api_key: Google AI API key (if None, reads from env GEMINI_API_KEY)
            model: Gemini model name (default: gemini-2.5-flash)
            thinking_budget: Thinking budget in tokens (0-24576, -1 for dynamic)
                           0 = thinking off, 8000 = high thinking
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.model_name = model
        self.thinking_budget = thinking_budget

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment or constructor")

        # Configure Gemini
        genai.configure(api_key=self.api_key)

        # Initialize model (use full model path if not already)
        if not self.model_name.startswith('models/'):
            full_model_name = f'models/{self.model_name}'
        else:
            full_model_name = self.model_name

        # Import safety settings
        from google.generativeai.types import HarmCategory, HarmBlockThreshold

        # Configure safety settings (must be set at model creation)
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        self.model = genai.GenerativeModel(
            full_model_name,
            safety_settings=safety_settings
        )

        logger.info(f"GeminiClient initialized: model={model}, thinking_budget={thinking_budget}")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        thinking_budget: Optional[int] = None
    ) -> Tuple[bool, Optional[str], Optional[Dict], Optional[str]]:
        """
        Generate AI response using Gemini.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt (will be prepended)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            thinking_budget: Override default thinking budget

        Returns:
            Tuple of (success, response_text, usage_data, error_message)
        """
        try:
            # Build full prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            else:
                full_prompt = prompt

            # Use provided thinking budget or default
            budget = thinking_budget if thinking_budget is not None else self.thinking_budget

            logger.debug(f"Calling Gemini API: model={self.model_name}, thinking_budget={budget}")

            # NOTE: Cannot use GenerationConfig object with safety_settings (causes blocking)
            # Instead, pass parameters directly to generate_content()

            # Generate content (safety_settings already set in model initialization)
            response = self.model.generate_content(
                full_prompt,
                # Pass generation parameters directly (NOT as GenerationConfig object)
                # to avoid conflict with safety_settings
            )

            # Extract response text with safety check
            if not response.candidates:
                return False, None, None, "No response candidates generated"

            candidate = response.candidates[0]
            if candidate.finish_reason != 1:  # 1 = STOP (normal completion)
                finish_reasons = {
                    2: "SAFETY (blocked by safety filters)",
                    3: "RECITATION",
                    4: "OTHER",
                    5: "MAX_TOKENS"
                }
                reason = finish_reasons.get(candidate.finish_reason, f"Unknown ({candidate.finish_reason})")
                return False, None, None, f"Generation stopped: {reason}"

            response_text = candidate.content.parts[0].text

            # Calculate usage (Gemini provides token counts)
            usage_metadata = response.usage_metadata
            input_tokens = usage_metadata.prompt_token_count
            output_tokens = usage_metadata.candidates_token_count
            total_tokens = usage_metadata.total_token_count

            # Calculate cost (Gemini 2.5 Flash pricing)
            # Input: $0.15/1M, Output: $0.60/1M, Thinking: $3.50/1M
            input_cost = input_tokens * 0.15 / 1_000_000

            # Estimate thinking vs regular output tokens
            # Gemini doesn't separate them, so we estimate
            if budget > 0:
                # Assume 30-40% of output is thinking
                estimated_thinking_tokens = min(output_tokens * 0.35, budget)
                regular_output_tokens = output_tokens - estimated_thinking_tokens

                thinking_cost = estimated_thinking_tokens * 3.50 / 1_000_000
                output_cost = regular_output_tokens * 0.60 / 1_000_000
                cost_usd = input_cost + thinking_cost + output_cost
            else:
                # No thinking mode
                output_cost = output_tokens * 0.60 / 1_000_000
                cost_usd = input_cost + output_cost

            # Build usage data
            usage_data = {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': total_tokens,
                'cost_usd': cost_usd,
                'model': self.model_name,
                'provider': 'gemini',
                'thinking_budget': budget
            }

            logger.info(f"Gemini generation successful ({total_tokens} tokens, ${cost_usd:.4f})")
            return True, response_text, usage_data, None

        except Exception as e:
            error_msg = f"Gemini API error: {str(e)}"
            logger.error(error_msg)
            return False, None, None, error_msg

    def simulate_match(
        self,
        home_team: str,
        away_team: str,
        data_context: Dict
    ) -> Tuple[bool, Optional[Dict], Optional[Dict], Optional[str]]:
        """
        Simulate a match using Gemini AI.

        Args:
            home_team: Home team name
            away_team: Away team name
            data_context: Context data

        Returns:
            Tuple of (success, prediction_dict, usage_data, error_message)
        """
        # Build system prompt
        system_prompt = self._build_system_prompt()

        # Build user prompt
        user_prompt = self._build_match_prompt(home_team, away_team, data_context)

        # Generate prediction (use moderate thinking for match prediction)
        success, response_text, usage_data, error = self.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=4096,
            thinking_budget=2000  # Moderate thinking for match prediction
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
            logger.error(f"Raw response: {response_text[:500]}")
            return False, None, usage_data, error_msg

    def _build_system_prompt(self) -> str:
        """Build system prompt for match prediction."""
        return """You are an expert football match analyst with deep knowledge of the English Premier League.

Your role is to analyze matches and provide realistic predictions based on:
- Team form and recent performance
- Squad quality and player ratings
- Head-to-head history
- Tactical considerations

IMPORTANT: You MUST respond with a valid JSON object. Do not include any text before or after the JSON.

Format your response EXACTLY like this:
{
  "prediction": {
    "home_win_probability": 0.45,
    "draw_probability": 0.30,
    "away_win_probability": 0.25,
    "predicted_score": "2-1",
    "confidence": "medium",
    "expected_goals": {
      "home": 1.8,
      "away": 1.2
    }
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

    def _build_match_prompt(
        self,
        home_team: str,
        away_team: str,
        data_context: Dict
    ) -> str:
        """Build user prompt for match simulation."""
        prompt_parts = [
            f"Analyze the upcoming match: {home_team} vs {away_team}\n"
        ]

        # Add data context
        if 'squad_ratings' in data_context:
            prompt_parts.append("\n**Squad Quality:**")
            prompt_parts.append(f"Home ({home_team}): {data_context['squad_ratings'].get('home', 'N/A')}")
            prompt_parts.append(f"Away ({away_team}): {data_context['squad_ratings'].get('away', 'N/A')}")

        if 'recent_form' in data_context:
            prompt_parts.append("\n**Recent Form:**")
            prompt_parts.append(f"{home_team}: {data_context['recent_form'].get('home', 'N/A')}")
            prompt_parts.append(f"{away_team}: {data_context['recent_form'].get('away', 'N/A')}")

        if 'league_position' in data_context:
            prompt_parts.append("\n**League Standings:**")
            prompt_parts.append(f"{home_team}: {data_context['league_position'].get('home', 'N/A')}")
            prompt_parts.append(f"{away_team}: {data_context['league_position'].get('away', 'N/A')}")

        # Add weights reminder
        if 'weights' in data_context:
            weights = data_context['weights']
            user_pct = int(weights.get('user_value', 0.65) * 100)
            prompt_parts.append(f"\n**Data Weighting**: User analysis is weighted at {user_pct}% - this is the primary factor.")

        prompt_parts.append("\nProvide your prediction in the JSON format specified above. ONLY return the JSON, nothing else.")

        return "\n".join(prompt_parts)

    def _parse_match_prediction(
        self,
        response_text: str,
        home_team: str,
        away_team: str
    ) -> Dict:
        """Parse Gemini response into structured prediction."""
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            json_str = response_text.strip()

        try:
            prediction = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.error(f"Attempted to parse: {json_str[:500]}")
            # Return a default prediction if parsing fails
            prediction = {
                "prediction": {
                    "home_win_probability": 0.40,
                    "draw_probability": 0.30,
                    "away_win_probability": 0.30,
                    "predicted_score": "1-1",
                    "confidence": "low"
                },
                "analysis": {
                    "key_factors": ["Unable to parse AI response"],
                    "home_team_strengths": [],
                    "away_team_strengths": [],
                    "tactical_insight": "Analysis unavailable"
                },
                "summary": "Prediction based on default values due to parsing error."
            }

        # Add metadata
        prediction['metadata'] = {
            'home_team': home_team,
            'away_team': away_team,
            'generated_at': datetime.utcnow().isoformat(),
            'model': self.model_name,
            'provider': 'gemini'
        }

        return prediction

    def get_model_info(self) -> Dict:
        """Get Gemini model information."""
        return {
            'provider': 'Google Gemini',
            'model': self.model_name,
            'version': '2.5-Flash',
            'capabilities': [
                'Match prediction',
                'Tactical analysis',
                'Thinking mode (advanced reasoning)',
                'Fast response (~5-20s)',
                'Production-ready'
            ],
            'cost_per_1k_tokens': {
                'input': 0.00015,  # $0.15/1M
                'output': 0.00060,  # $0.60/1M
                'thinking': 0.00350  # $3.50/1M
            },
            'thinking_budget': self.thinking_budget,
            'context_window': '1M tokens'
        }

    def health_check(self) -> Tuple[bool, Optional[str]]:
        """Check if Gemini API is accessible."""
        try:
            # Test with a simple prompt using our generate method
            success, response_text, usage, error = self.generate(
                prompt="Reply with exactly: OK",
                temperature=0.1,
                max_tokens=10,
                thinking_budget=0
            )

            if success and response_text:
                return True, None
            else:
                return False, f"Health check failed: {error or 'No response'}"

        except Exception as e:
            return False, f"Gemini API health check failed: {str(e)}"


# Global client instance
_gemini_client = None


def get_gemini_client(
    model: str = "gemini-2.5-flash",
    thinking_budget: Optional[int] = None
) -> GeminiClient:
    """
    Get global Gemini client instance (singleton).

    Args:
        model: Gemini model name
        thinking_budget: Override thinking budget from env
    """
    global _gemini_client

    # Read thinking budget from env if not provided
    if thinking_budget is None:
        thinking_budget = int(os.getenv('GEMINI_THINKING_BUDGET', '8000'))

    if _gemini_client is None:
        _gemini_client = GeminiClient(
            model=model,
            thinking_budget=thinking_budget
        )

    return _gemini_client
