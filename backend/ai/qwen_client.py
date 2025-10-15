"""
Qwen AI Client (Ollama)
Local AI client for development and testing
"""

import requests
import json
import logging
import re
from typing import Dict, Optional, Tuple
from datetime import datetime

from ai.base_client import BaseAIClient

logger = logging.getLogger(__name__)


class QwenClient(BaseAIClient):
    """
    Qwen AI client using Ollama.

    Connects to local Ollama server for zero-cost AI predictions.
    Perfect for development and testing.
    """

    def __init__(
        self,
        model: str = "qwen2.5:32b",
        base_url: str = "http://localhost:11434"
    ):
        """
        Initialize Qwen client.

        Args:
            model: Qwen model name (default: qwen2.5:32b)
            base_url: Ollama server URL
        """
        self.model = model
        self.base_url = base_url
        self.api_generate = f"{base_url}/api/generate"
        self.api_tags = f"{base_url}/api/tags"

        logger.info(f"QwenClient initialized: model={model}, url={base_url}")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Tuple[bool, Optional[str], Optional[Dict], Optional[str]]:
        """
        Generate AI response using Qwen via Ollama.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Tuple of (success, response_text, usage_data, error_message)
        """
        try:
            # Build full prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\nUser: {prompt}\n\nAssistant:"
            else:
                full_prompt = prompt

            # Make API call
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }

            logger.debug(f"Calling Ollama API: {self.api_generate}")
            response = requests.post(
                self.api_generate,
                json=payload,
                timeout=300  # 5 minutes timeout for complex tasks
            )

            if response.status_code != 200:
                error_msg = f"Ollama API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return False, None, None, error_msg

            # Parse response
            data = response.json()
            response_text = data.get('response', '')

            # Build usage data (Ollama doesn't provide token counts, we estimate)
            usage_data = {
                'input_tokens': len(full_prompt.split()) * 1.3,  # Rough estimate
                'output_tokens': len(response_text.split()) * 1.3,
                'total_tokens': (len(full_prompt.split()) + len(response_text.split())) * 1.3,
                'cost_usd': 0.0,  # Local model = free
                'model': self.model,
                'provider': 'qwen_local'
            }

            logger.info(f"Qwen generation successful (est. {usage_data['total_tokens']:.0f} tokens)")
            return True, response_text, usage_data, None

        except requests.exceptions.Timeout:
            error_msg = "Ollama request timeout (120s)"
            logger.error(error_msg)
            return False, None, None, error_msg

        except requests.exceptions.ConnectionError:
            error_msg = "Cannot connect to Ollama server. Is it running?"
            logger.error(error_msg)
            return False, None, None, error_msg

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return False, None, None, error_msg

    def simulate_match(
        self,
        home_team: str,
        away_team: str,
        data_context: Dict
    ) -> Tuple[bool, Optional[Dict], Optional[Dict], Optional[str]]:
        """
        Simulate a match using Qwen AI.

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

        # Generate prediction
        success, response_text, usage_data, error = self.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=4096
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
        """Parse Qwen response into structured prediction."""
        # Extract JSON from response
        # Qwen might add extra text, so we find the JSON object
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
        else:
            # Try to parse entire response as JSON
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
            'model': self.model,
            'provider': 'qwen_local'
        }

        return prediction

    def get_model_info(self) -> Dict:
        """Get Qwen model information."""
        return {
            'provider': 'Qwen (Local Ollama)',
            'model': self.model,
            'version': '2.5-32B',
            'capabilities': [
                'Match prediction',
                'Tactical analysis',
                'Statistical reasoning',
                'Free (no API costs)'
            ],
            'cost_per_1k_tokens': 0.0,
            'parameters': '32.8B',
            'quantization': 'Q4_K_M'
        }

    def health_check(self) -> Tuple[bool, Optional[str]]:
        """Check if Ollama server is healthy."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                model_names = [m['name'] for m in models]

                if self.model in model_names:
                    return True, None
                else:
                    return False, f"Model {self.model} not found. Available: {model_names}"
            else:
                return False, f"Ollama API returned {response.status_code}"

        except requests.exceptions.ConnectionError:
            return False, "Cannot connect to Ollama server (http://localhost:11434)"
        except Exception as e:
            return False, f"Health check failed: {str(e)}"


# Global client instance
_qwen_client = None


def get_qwen_client(model: str = "qwen2.5:32b") -> QwenClient:
    """Get global Qwen client instance (singleton)."""
    global _qwen_client
    if _qwen_client is None:
        _qwen_client = QwenClient(model=model)
    return _qwen_client
