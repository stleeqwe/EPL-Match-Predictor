"""
AI Factory
Factory pattern for selecting AI provider dynamically
"""

import os
import logging
from typing import Optional

from ai.base_client import BaseAIClient

logger = logging.getLogger(__name__)


class AIFactory:
    """
    Factory for creating AI clients.

    Supports multiple providers:
    - gemini (Google) - Production (Gemini 2.5 Flash)
    - claude (Anthropic) - Production alternative
    - openai (OpenAI) - Production alternative (future)
    """

    @staticmethod
    def create_client(provider: Optional[str] = None) -> BaseAIClient:
        """
        Create AI client based on provider.

        Args:
            provider: AI provider name ('gemini', 'claude', 'openai')
                     If None, reads from AI_PROVIDER env variable

        Returns:
            BaseAIClient instance

        Raises:
            ValueError: If provider is invalid or not configured
        """
        # Get provider from env if not specified
        if provider is None:
            provider = os.getenv('AI_PROVIDER', 'gemini').lower()

        logger.info(f"Creating AI client: provider={provider}")

        if provider == 'gemini':
            return AIFactory._create_gemini_client()
        elif provider == 'claude':
            return AIFactory._create_claude_client()
        elif provider == 'openai':
            return AIFactory._create_openai_client()
        else:
            raise ValueError(
                f"Unknown AI provider: {provider}. "
                f"Supported: gemini, claude, openai"
            )

    @staticmethod
    def _create_gemini_client() -> BaseAIClient:
        """Create Gemini client (Google API)."""
        try:
            from ai.gemini_client import get_gemini_client

            model = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
            thinking_budget = int(os.getenv('GEMINI_THINKING_BUDGET', '8000'))

            logger.info(f"Initializing Gemini client: model={model}, thinking_budget={thinking_budget}")
            client = get_gemini_client(model=model, thinking_budget=thinking_budget)

            # Health check
            is_healthy, error = client.health_check()
            if not is_healthy:
                logger.error(f"Gemini client health check failed: {error}")
                raise ConnectionError(f"Gemini API not available: {error}")

            logger.info("Gemini client initialized successfully")
            return client

        except ImportError as e:
            raise ImportError("Gemini client not available. Install: pip install google-generativeai")
        except Exception as e:
            raise ConnectionError(f"Gemini client initialization failed: {e}")

    @staticmethod
    def _create_claude_client() -> BaseAIClient:
        """Create Claude client (Anthropic API)."""
        # This will be implemented when switching to production
        try:
            from ai.claude_client import get_claude_client
            logger.info("Initializing Claude client")
            return get_claude_client()
        except ImportError as e:
            raise ImportError("Claude client not available. Install anthropic package.")
        except Exception as e:
            raise ConnectionError(f"Claude client initialization failed: {e}")

    @staticmethod
    def _create_openai_client() -> BaseAIClient:
        """Create OpenAI client (future implementation)."""
        raise NotImplementedError(
            "OpenAI client not yet implemented. "
            "Use 'gemini' or 'claude' for production."
        )

    @staticmethod
    def get_available_providers() -> list:
        """Get list of available AI providers."""
        providers = []

        # Check Gemini
        try:
            gemini_key = os.getenv('GEMINI_API_KEY')
            if gemini_key:
                providers.append('gemini')
        except:
            pass

        # Check Claude
        try:
            claude_key = os.getenv('CLAUDE_API_KEY')
            if claude_key:
                providers.append('claude')
        except:
            pass

        # Check OpenAI
        try:
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key:
                providers.append('openai')
        except:
            pass

        return providers


# Global AI client instance
_ai_client = None


def get_ai_client(provider: Optional[str] = None) -> BaseAIClient:
    """
    Get global AI client instance (singleton).

    Args:
        provider: Optional provider override

    Returns:
        BaseAIClient instance
    """
    global _ai_client

    # If provider is specified and different from current, recreate
    current_provider = os.getenv('AI_PROVIDER', 'gemini')
    if provider and provider != current_provider:
        logger.info(f"Switching AI provider: {current_provider} -> {provider}")
        _ai_client = None
        os.environ['AI_PROVIDER'] = provider

    # Create client if not exists
    if _ai_client is None:
        _ai_client = AIFactory.create_client(provider)

    return _ai_client


def reset_ai_client():
    """Reset global AI client (useful for testing)."""
    global _ai_client
    _ai_client = None
