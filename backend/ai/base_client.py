"""
Base AI Client Interface
Provides abstract interface for AI providers (Qwen, Claude, OpenAI, etc.)
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class BaseAIClient(ABC):
    """
    Abstract base class for AI clients.

    All AI providers must implement this interface to ensure
    consistent behavior across different models.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Tuple[bool, Optional[str], Optional[Dict], Optional[str]]:
        """
        Generate AI response.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Tuple of (success, response_text, usage_data, error_message)
            usage_data format: {
                'input_tokens': int,
                'output_tokens': int,
                'total_tokens': int,
                'cost_usd': float,
                'model': str
            }
        """
        pass

    @abstractmethod
    def simulate_match(
        self,
        home_team: str,
        away_team: str,
        data_context: Dict
    ) -> Tuple[bool, Optional[Dict], Optional[Dict], Optional[str]]:
        """
        Simulate a match using AI.

        Args:
            home_team: Home team name
            away_team: Away team name
            data_context: Context data (squad info, form, odds, etc.)

        Returns:
            Tuple of (success, prediction_dict, usage_data, error_message)
            prediction_dict format: {
                'prediction': {
                    'home_win_probability': float,
                    'draw_probability': float,
                    'away_win_probability': float,
                    'predicted_score': str,
                    'confidence': str
                },
                'analysis': {...},
                'summary': str
            }
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict:
        """
        Get model information.

        Returns:
            Dictionary with model details:
            {
                'provider': str,
                'model': str,
                'version': str,
                'capabilities': [str],
                'cost_per_1k_tokens': float
            }
        """
        pass

    @abstractmethod
    def health_check(self) -> Tuple[bool, Optional[str]]:
        """
        Check if AI service is healthy.

        Returns:
            Tuple of (is_healthy, error_message)
        """
        pass
