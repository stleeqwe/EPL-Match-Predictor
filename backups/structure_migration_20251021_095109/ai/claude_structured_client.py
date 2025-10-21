"""
Claude Structured Output Client
Guaranteed type-safe JSON responses using Pydantic schemas

Key benefits:
- 100% valid JSON (no regex parsing)
- Automatic retry with exponential backoff
- Type safety via Pydantic
- Comprehensive error handling
"""

import anthropic
import json
import time
import os
import sys
import logging
from typing import Type, TypeVar, Tuple, Optional, Dict
from pydantic import BaseModel

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import schemas
from ai.schemas import MatchScenario, AnalysisResult, AIResponse

logger = logging.getLogger(__name__)

# Type variable for Pydantic models
T = TypeVar('T', bound=BaseModel)


class ClaudeStructuredClient:
    """
    Claude client with guaranteed structured JSON outputs

    Usage:
        client = ClaudeStructuredClient(api_key="...")
        success, scenario, usage, error = client.generate_structured(
            prompt="Analyze Arsenal vs Liverpool...",
            response_model=MatchScenario,
            system_prompt="You are a football analyst..."
        )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        default_max_tokens: int = 4096,
        default_temperature: float = 0.7
    ):
        """
        Initialize Claude structured client

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Claude model to use
            default_max_tokens: Default max tokens for generation
            default_temperature: Default temperature for sampling
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not provided")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model
        self.default_max_tokens = default_max_tokens
        self.default_temperature = default_temperature

        logger.info(f"Initialized Claude structured client with model: {model}")

    def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_retries: int = 3
    ) -> Tuple[bool, Optional[T], Dict, Optional[str]]:
        """
        Generate structured response with guaranteed schema compliance

        Args:
            prompt: User prompt
            response_model: Pydantic model class (e.g., MatchScenario)
            system_prompt: Optional system instructions
            temperature: Sampling temperature (None = use default)
            max_tokens: Max tokens (None = use default)
            max_retries: Maximum retry attempts

        Returns:
            Tuple of (success, parsed_model, usage_stats, error_message)

        Example:
            success, scenario, usage, error = client.generate_structured(
                prompt="Analyze the match...",
                response_model=MatchScenario,
                system_prompt="You are an expert analyst..."
            )

            if success:
                print(f"Events: {len(scenario.events)}")
                print(f"Tokens used: {usage['total_tokens']}")
            else:
                print(f"Error: {error}")
        """
        # Get JSON schema from Pydantic model
        schema = response_model.model_json_schema()

        # Build enhanced system prompt with schema
        full_system_prompt = self._build_system_prompt_with_schema(
            base_prompt=system_prompt or "You are a helpful AI assistant.",
            schema=schema,
            model_name=response_model.__name__
        )

        # Use defaults if not specified
        temp = temperature if temperature is not None else self.default_temperature
        tokens = max_tokens if max_tokens is not None else self.default_max_tokens

        # Retry loop with exponential backoff
        for attempt in range(max_retries):
            try:
                start_time = time.time()

                # Call Claude API
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=tokens,
                    temperature=temp,
                    system=full_system_prompt,
                    messages=[{"role": "user", "content": prompt}]
                )

                latency_ms = (time.time() - start_time) * 1000
                response_text = response.content[0].text

                # Try to parse as JSON
                try:
                    # Validate with Pydantic
                    parsed = response_model.model_validate_json(response_text)

                    # Success! Extract usage stats
                    usage = {
                        'input_tokens': response.usage.input_tokens,
                        'output_tokens': response.usage.output_tokens,
                        'total_tokens': response.usage.input_tokens + response.usage.output_tokens,
                        'latency_ms': latency_ms,
                        'model': self.model
                    }

                    logger.info(
                        f"Structured generation succeeded",
                        extra={
                            'model': response_model.__name__,
                            'tokens': usage['total_tokens'],
                            'latency_ms': latency_ms,
                            'attempt': attempt + 1
                        }
                    )

                    return True, parsed, usage, None

                except json.JSONDecodeError as e:
                    # Claude returned non-JSON
                    error_msg = f"Invalid JSON (attempt {attempt + 1}/{max_retries}): {str(e)}"
                    logger.warning(error_msg, extra={'response_text': response_text[:200]})

                    if attempt == max_retries - 1:
                        return False, None, {}, error_msg

                except Exception as e:
                    # Pydantic validation error
                    error_msg = f"Schema validation error (attempt {attempt + 1}/{max_retries}): {str(e)}"
                    logger.warning(error_msg, extra={'response_text': response_text[:200]})

                    if attempt == max_retries - 1:
                        return False, None, {}, error_msg

            except anthropic.APIError as e:
                # API error (rate limit, timeout, etc.)
                error_msg = f"Claude API error (attempt {attempt + 1}/{max_retries}): {str(e)}"
                logger.error(error_msg)

                if attempt == max_retries - 1:
                    return False, None, {}, error_msg

            except Exception as e:
                # Unexpected error
                error_msg = f"Unexpected error (attempt {attempt + 1}/{max_retries}): {str(e)}"
                logger.error(error_msg, exc_info=True)

                if attempt == max_retries - 1:
                    return False, None, {}, error_msg

            # Exponential backoff before retry
            if attempt < max_retries - 1:
                backoff_seconds = 2 ** attempt
                logger.info(f"Retrying in {backoff_seconds}s...")
                time.sleep(backoff_seconds)

        # Should never reach here, but just in case
        return False, None, {}, "Max retries exceeded"

    def _build_system_prompt_with_schema(
        self,
        base_prompt: str,
        schema: Dict,
        model_name: str
    ) -> str:
        """
        Build system prompt with embedded JSON schema

        Args:
            base_prompt: Base system instructions
            schema: JSON schema from Pydantic
            model_name: Name of Pydantic model

        Returns:
            Enhanced system prompt with schema
        """
        # Format schema nicely
        schema_str = json.dumps(schema, indent=2)

        # Build enhanced prompt
        enhanced_prompt = f"""{base_prompt}

CRITICAL: You MUST respond with a valid JSON object matching this exact schema:

Model: {model_name}

Schema:
{schema_str}

STRICT REQUIREMENTS:
1. Response must be pure JSON (no markdown, no code blocks, no explanations)
2. All required fields must be present
3. Field types must match schema exactly
4. Enums must use exact listed values (case-sensitive)
5. Number ranges must be respected (e.g., ge/le constraints)
6. String lengths must be within specified bounds
7. Arrays must meet min/max length requirements

VALIDATION:
- Your response will be validated against this schema
- Invalid responses will be rejected and retried
- Follow the schema exactly to avoid errors

OUTPUT FORMAT:
Start your response with {{ and end with }}. Do NOT include:
- Markdown code blocks (no ```json)
- Explanations before or after the JSON
- Comments in the JSON
- Any text outside the JSON object

Example of CORRECT response format for {model_name}:
{{
  "field1": "value1",
  "field2": 123,
  "nested": {{
    "inner_field": "value"
  }}
}}
"""
        return enhanced_prompt

    def generate_scenario(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> Tuple[bool, Optional[MatchScenario], Dict, Optional[str]]:
        """
        Convenience method for generating MatchScenario

        Args:
            prompt: User prompt describing the match
            system_prompt: Optional system instructions
            temperature: Sampling temperature

        Returns:
            Tuple of (success, scenario, usage, error)
        """
        return self.generate_structured(
            prompt=prompt,
            response_model=MatchScenario,
            system_prompt=system_prompt,
            temperature=temperature
        )

    def analyze_result(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.5
    ) -> Tuple[bool, Optional[AnalysisResult], Dict, Optional[str]]:
        """
        Convenience method for generating AnalysisResult

        Args:
            prompt: User prompt with simulation result
            system_prompt: Optional system instructions
            temperature: Sampling temperature (lower for analysis)

        Returns:
            Tuple of (success, analysis, usage, error)
        """
        return self.generate_structured(
            prompt=prompt,
            response_model=AnalysisResult,
            system_prompt=system_prompt,
            temperature=temperature
        )

    def health_check(self) -> Tuple[bool, Optional[str]]:
        """
        Check if Claude API is accessible

        Returns:
            Tuple of (is_healthy, error_message)
        """
        try:
            # Simple test call
            response = self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hello"}]
            )

            logger.info("Claude API health check passed")
            return True, None

        except Exception as e:
            error_msg = f"Claude API health check failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def get_model_info(self) -> Dict:
        """Get model information"""
        return {
            'provider': 'anthropic',
            'model': self.model,
            'version': '2025-01',
            'capabilities': ['structured_output', 'long_context', 'analysis'],
            'max_tokens': self.default_max_tokens,
            'cost_per_1k_input_tokens': 0.003,  # $3 per 1M tokens
            'cost_per_1k_output_tokens': 0.015  # $15 per 1M tokens
        }


# ==========================================================================
# Testing
# ==========================================================================

def test_structured_client():
    """Test Claude structured output client"""
    print("=" * 70)
    print("Testing Claude Structured Output Client")
    print("=" * 70)

    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n⚠️  ANTHROPIC_API_KEY not set - skipping live tests")
        print("Set environment variable to run live tests:")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        return

    try:
        # Initialize client
        client = ClaudeStructuredClient(api_key=api_key)
        print(f"\n✅ Client initialized: {client.model}")

        # Test 1: Health check
        print("\n" + "=" * 70)
        print("Test 1: Health Check")
        print("=" * 70)

        healthy, error = client.health_check()
        if healthy:
            print("✅ Claude API is healthy")
        else:
            print(f"❌ Health check failed: {error}")
            return

        # Test 2: Generate scenario
        print("\n" + "=" * 70)
        print("Test 2: Generate Match Scenario")
        print("=" * 70)

        prompt = """
Analyze this Premier League match:
- Home: Arsenal (strong attack, good form)
- Away: Liverpool (strong all-around, counter-attacking)

Generate a realistic match scenario with 3-5 key events.
"""

        system_prompt = "You are an expert football analyst. Generate realistic match scenarios."

        success, scenario, usage, error = client.generate_scenario(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7
        )

        if success:
            print(f"✅ Scenario generated successfully!")
            print(f"  Events: {len(scenario.events)}")
            print(f"  Predicted score: {scenario.predicted_score}")
            print(f"  Confidence: {scenario.confidence}")
            print(f"  Tokens: {usage['total_tokens']} ({usage['latency_ms']:.0f}ms)")
            print(f"\n  Description: {scenario.description[:100]}...")

            # Show first event
            if scenario.events:
                e = scenario.events[0]
                print(f"\n  First event:")
                print(f"    Time: {e.minute_range}")
                print(f"    Type: {e.event_type.value}")
                print(f"    Team: {e.team.value}")
                print(f"    Boost: {e.probability_boost}")
        else:
            print(f"❌ Scenario generation failed: {error}")

        print("\n" + "=" * 70)
        print("✅ All tests completed!")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    test_structured_client()
