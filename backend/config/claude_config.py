"""
Claude API Configuration
AI Match Simulation v3.0

Manages Claude API settings, model selection, and tier-based configurations.
"""

import os
from typing import Dict, Optional


class ClaudeConfig:
    """Claude API configuration and model management."""

    def __init__(self):
        """Initialize Claude configuration from environment variables."""
        self.api_key = os.getenv('CLAUDE_API_KEY', '')

        # Model configurations by tier
        self.models = {
            'BASIC': {
                'model': 'claude-sonnet-3-5-20250219',
                'max_tokens': 4096,
                'temperature': 0.7,
                'system_prompt_length': 2000,
                'data_context_length': 3000
            },
            'PRO': {
                'model': 'claude-sonnet-4-5-20250514',
                'max_tokens': 8192,
                'temperature': 0.7,
                'system_prompt_length': 4000,
                'data_context_length': 6000
            }
        }

        # API settings
        self.timeout = int(os.getenv('CLAUDE_TIMEOUT', '30'))  # seconds
        self.max_retries = int(os.getenv('CLAUDE_MAX_RETRIES', '3'))

        # Cost tracking (per 1M tokens)
        self.costs = {
            'claude-sonnet-3-5-20250219': {
                'input': 3.00,
                'output': 15.00
            },
            'claude-sonnet-4-5-20250514': {
                'input': 3.00,
                'output': 15.00
            }
        }

        # Feature flags
        self.enabled = os.getenv('CLAUDE_ENABLED', 'true').lower() == 'true'
        self.cache_ttl = int(os.getenv('CLAUDE_CACHE_TTL', '3600'))  # 1 hour

    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate Claude API configuration.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.enabled:
            return True, "Claude API disabled"

        if not self.api_key:
            return False, "CLAUDE_API_KEY not set"

        return True, None

    def get_model_config(self, tier: str) -> Dict:
        """
        Get model configuration for subscription tier.

        Args:
            tier: Subscription tier ('BASIC' or 'PRO')

        Returns:
            Model configuration dictionary
        """
        return self.models.get(tier, self.models['BASIC'])

    def get_model_name(self, tier: str) -> str:
        """
        Get model name for tier.

        Args:
            tier: Subscription tier

        Returns:
            Claude model identifier
        """
        config = self.get_model_config(tier)
        return config['model']

    def get_max_tokens(self, tier: str) -> int:
        """
        Get max tokens for tier.

        Args:
            tier: Subscription tier

        Returns:
            Maximum tokens for response
        """
        config = self.get_model_config(tier)
        return config['max_tokens']

    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate API call cost in USD.

        Args:
            model: Claude model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD
        """
        if model not in self.costs:
            return 0.0

        cost_per_1m = self.costs[model]
        input_cost = (input_tokens / 1_000_000) * cost_per_1m['input']
        output_cost = (output_tokens / 1_000_000) * cost_per_1m['output']

        return input_cost + output_cost

    def get_tier_features(self, tier: str) -> Dict:
        """
        Get feature comparison for tier.

        Args:
            tier: Subscription tier

        Returns:
            Dictionary of tier features
        """
        config = self.get_model_config(tier)

        return {
            'tier': tier,
            'model': config['model'],
            'model_display': 'Claude Sonnet 3.5' if tier == 'BASIC' else 'Claude Sonnet 4.5',
            'max_tokens': config['max_tokens'],
            'temperature': config['temperature'],
            'features': [
                'AI-powered match analysis',
                'Team performance evaluation',
                'Tactical insights',
                'Win probability prediction'
            ] + (['Advanced statistical analysis', 'Sharp bookmaker integration', 'Extended context'] if tier == 'PRO' else [])
        }


# Global configuration instance
claude_config = ClaudeConfig()


def get_claude_config() -> ClaudeConfig:
    """Get global Claude configuration instance."""
    return claude_config
