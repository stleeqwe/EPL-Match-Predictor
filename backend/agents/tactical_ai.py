# -*- coding: utf-8 -*-
"""
Tactical AI - Haiku LLM Integration
Handles complex tactical decisions (20% of cases)

Cost-optimized for Claude Haiku with upgrade path to Sonnet/Opus.

Design:
- Only called for complex decisions (3+ passing options, tactical adjustments)
- Short prompts (~30 tokens) to minimize cost
- Limited responses (max_tokens=50-200)
- Integrates with existing claude_config system
"""

import os
import time
import json
import hashlib
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np

from .actions import Action, ActionType
from .simple_agent import PlayerGameState, GameContext

# Import Anthropic client if available
try:
    from anthropic import Anthropic, AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


@dataclass
class TacticalDecision:
    """
    Result of tactical AI decision

    Attributes:
        action: Recommended action
        confidence: Confidence score (0-1)
        reasoning: Brief reasoning (for debugging)
        tokens_used: Total tokens used
        cost_usd: Estimated cost in USD
    """
    action: Action
    confidence: float
    reasoning: str
    tokens_used: int
    cost_usd: float


class TacticalDecisionMaker:
    """
    Uses Claude Haiku for complex tactical decisions

    Only called when:
    - Multiple good options available (3+ passing targets)
    - Opponent pattern unclear
    - Strategic planning needed (formation change, etc.)

    Cost per call: ~$0.004 (Haiku)
    Calls per match: ~25 (after caching)
    Total cost: ~$0.10 per match
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = 'claude-haiku-3-5-20250219',
        tier: str = 'BASIC'
    ):
        """
        Initialize tactical AI

        Args:
            api_key: Anthropic API key (or from env)
            model: Claude model name (default: Haiku)
            tier: Subscription tier ('BASIC' or 'PRO')
        """
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY', '')
        self.tier = tier

        # Model configuration
        self.model_configs = {
            'BASIC': {
                'model': 'claude-haiku-3-5-20250219',  # Haiku for cost
                'max_tokens': 200,
                'temperature': 0.7
            },
            'PRO': {
                'model': 'claude-sonnet-4-5-20250514',  # Sonnet for quality
                'max_tokens': 500,
                'temperature': 0.7
            }
        }

        # Use tier-specific config
        config = self.model_configs.get(tier, self.model_configs['BASIC'])
        self.model = config['model']
        self.max_tokens = config['max_tokens']
        self.temperature = config['temperature']

        # Initialize client
        if ANTHROPIC_AVAILABLE and self.api_key:
            self.client = Anthropic(api_key=self.api_key)
            self.async_client = AsyncAnthropic(api_key=self.api_key)
            self.enabled = True
        else:
            self.client = None
            self.async_client = None
            self.enabled = False

        # Cost tracking (per 1M tokens)
        self.cost_per_1m_tokens = {
            'claude-haiku-3-5-20250219': {
                'input': 0.25,
                'output': 1.25
            },
            'claude-sonnet-4-5-20250514': {
                'input': 3.00,
                'output': 15.00
            }
        }

        # Statistics
        self.total_calls = 0
        self.total_tokens = 0
        self.total_cost = 0.0

    def should_use_llm(self, situation: Dict) -> bool:
        """
        Determine if LLM should be used for this situation

        Only use LLM if:
        - Complex decision (3+ options)
        - High stakes (near goal, important moment)
        - Unclear best choice

        Args:
            situation: Dictionary describing current situation

        Returns:
            True if LLM should be used
        """
        # Don't use if disabled
        if not self.enabled:
            return False

        # Complex passing decision
        if situation.get('decision_type') == 'pass':
            num_options = len(situation.get('passing_options', []))
            if num_options >= 3:
                return True

        # Tactical adjustment needed
        if situation.get('decision_type') == 'tactical_adjustment':
            return True

        # Near goal, unclear shot/pass choice
        if situation.get('decision_type') == 'shoot_or_pass':
            if situation.get('shot_quality', 0) > 0.4 and len(situation.get('passing_options', [])) > 0:
                return True

        # Opponent pattern analysis
        if situation.get('decision_type') == 'counter_strategy':
            return True

        return False

    def decide_complex_pass(
        self,
        player_state: PlayerGameState,
        passing_options: List[PlayerGameState],
        game_context: GameContext
    ) -> TacticalDecision:
        """
        Decide best pass when multiple good options exist

        Args:
            player_state: Current player state
            passing_options: List of 3+ open teammates
            game_context: Current game context

        Returns:
            TacticalDecision with recommended pass
        """
        if not self.enabled or len(passing_options) < 3:
            # Fall back to simple heuristic
            return self._fallback_pass_decision(player_state, passing_options, game_context)

        # Build concise prompt
        prompt = self._build_pass_prompt(player_state, passing_options, game_context)

        # Call LLM
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Parse response
            decision = self._parse_pass_response(
                response, player_state, passing_options, game_context
            )

            # Track usage
            self._track_usage(response.usage)

            return decision

        except Exception as e:
            print(f"Tactical AI error: {e}")
            # Fall back to rule-based
            return self._fallback_pass_decision(player_state, passing_options, game_context)

    def suggest_tactical_adjustment(
        self,
        team_state: Dict,
        opponent_state: Dict,
        match_situation: Dict
    ) -> Dict:
        """
        Suggest tactical changes based on match situation

        Args:
            team_state: Current team tactical setup
            opponent_state: Opponent tactical setup
            match_situation: Score, time, momentum

        Returns:
            Suggested tactical adjustments
        """
        if not self.enabled:
            return {'adjustment': 'none', 'reasoning': 'AI disabled'}

        prompt = self._build_tactical_prompt(team_state, opponent_state, match_situation)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            adjustment = self._parse_tactical_response(response)
            self._track_usage(response.usage)

            return adjustment

        except Exception as e:
            print(f"Tactical AI error: {e}")
            return {'adjustment': 'none', 'reasoning': f'Error: {e}'}

    # =========================================================================
    # PROMPT BUILDERS (Keep SHORT for cost optimization)
    # =========================================================================

    def _build_pass_prompt(
        self,
        player_state: PlayerGameState,
        passing_options: List[PlayerGameState],
        game_context: GameContext
    ) -> str:
        """
        Build concise pass decision prompt

        Target: ~30-50 tokens
        """
        px, py = player_state.position
        goal_x = -52.5 if game_context.is_attacking_left else 52.5

        # Format passing options (name, position, distance to goal)
        options_str = ""
        for i, option in enumerate(passing_options[:5], 1):  # Max 5 options
            ox, oy = option.position
            dist_to_goal = abs(ox - goal_x)
            options_str += f"{i}. {option.role} at ({ox:.0f},{oy:.0f}), {dist_to_goal:.0f}m from goal\n"

        prompt = f"""Player at ({px:.0f},{py:.0f}). Goal at x={goal_x}.
{len(passing_options)} passing options:
{options_str}
Best pass? Reply with number only."""

        return prompt

    def _build_tactical_prompt(
        self,
        team_state: Dict,
        opponent_state: Dict,
        match_situation: Dict
    ) -> str:
        """
        Build concise tactical adjustment prompt

        Target: ~50-80 tokens
        """
        score = match_situation.get('score', {'home': 0, 'away': 0})
        time_left = match_situation.get('time_remaining', 90)
        formation = team_state.get('formation', '4-3-3')

        prompt = f"""Formation: {formation}
Score: {score['home']}-{score['away']}
Time left: {time_left:.0f} min

Suggest tactical change (attack/defend/press/counter)?"""

        return prompt

    # =========================================================================
    # RESPONSE PARSERS
    # =========================================================================

    def _parse_pass_response(
        self,
        response,
        player_state: PlayerGameState,
        passing_options: List[PlayerGameState],
        game_context: GameContext
    ) -> TacticalDecision:
        """Parse LLM response for pass decision"""
        text = response.content[0].text.strip()

        # Extract number (1-5)
        try:
            choice_num = int(text.split()[0])  # First number in response
            if 1 <= choice_num <= len(passing_options):
                target = passing_options[choice_num - 1]

                # Create pass action
                from .actions import calculate_pass_power
                from backend.physics.constants import distance_2d

                distance = distance_2d(
                    player_state.position[0], player_state.position[1],
                    target.position[0], target.position[1]
                )

                pass_type = 'short' if distance < 15 else 'medium' if distance < 30 else 'long'
                power = calculate_pass_power(distance, pass_type)

                action = Action.create_pass(
                    target_player_id=target.player_id,
                    target_position=target.position,
                    power=power
                )

                # Calculate cost
                tokens_used = response.usage.input_tokens + response.usage.output_tokens
                cost = self._calculate_cost(response.usage.input_tokens, response.usage.output_tokens)

                return TacticalDecision(
                    action=action,
                    confidence=0.8,
                    reasoning=f"LLM chose option {choice_num}: {target.role}",
                    tokens_used=tokens_used,
                    cost_usd=cost
                )

        except (ValueError, IndexError):
            pass

        # Fall back if parsing failed
        return self._fallback_pass_decision(player_state, passing_options, game_context)

    def _parse_tactical_response(self, response) -> Dict:
        """Parse LLM response for tactical adjustment"""
        text = response.content[0].text.strip().lower()

        adjustment = 'none'
        if 'attack' in text:
            adjustment = 'more_attacking'
        elif 'defend' in text:
            adjustment = 'more_defensive'
        elif 'press' in text:
            adjustment = 'high_press'
        elif 'counter' in text:
            adjustment = 'counter_attack'

        tokens_used = response.usage.input_tokens + response.usage.output_tokens
        cost = self._calculate_cost(response.usage.input_tokens, response.usage.output_tokens)

        return {
            'adjustment': adjustment,
            'reasoning': text,
            'tokens_used': tokens_used,
            'cost_usd': cost
        }

    # =========================================================================
    # FALLBACK DECISIONS (Rule-based)
    # =========================================================================

    def _fallback_pass_decision(
        self,
        player_state: PlayerGameState,
        passing_options: List[PlayerGameState],
        game_context: GameContext
    ) -> TacticalDecision:
        """Fallback to rule-based pass decision"""
        if len(passing_options) == 0:
            # No options, just dribble
            action = Action.create_dribble(np.array([1.0, 0.0]), power=50.0)
            return TacticalDecision(
                action=action,
                confidence=0.5,
                reasoning="No pass options, dribbling",
                tokens_used=0,
                cost_usd=0.0
            )

        # Pick teammate closest to goal
        goal_x = -52.5 if game_context.is_attacking_left else 52.5
        best_option = min(passing_options, key=lambda p: abs(p.position[0] - goal_x))

        from .actions import calculate_pass_power
        from backend.physics.constants import distance_2d

        distance = distance_2d(
            player_state.position[0], player_state.position[1],
            best_option.position[0], best_option.position[1]
        )

        pass_type = 'short' if distance < 15 else 'medium' if distance < 30 else 'long'
        power = calculate_pass_power(distance, pass_type)

        action = Action.create_pass(
            target_player_id=best_option.player_id,
            target_position=best_option.position,
            power=power
        )

        return TacticalDecision(
            action=action,
            confidence=0.6,
            reasoning="Rule-based: closest to goal",
            tokens_used=0,
            cost_usd=0.0
        )

    # =========================================================================
    # COST TRACKING
    # =========================================================================

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate API call cost in USD"""
        if self.model not in self.cost_per_1m_tokens:
            return 0.0

        costs = self.cost_per_1m_tokens[self.model]
        input_cost = (input_tokens / 1_000_000) * costs['input']
        output_cost = (output_tokens / 1_000_000) * costs['output']

        return input_cost + output_cost

    def _track_usage(self, usage):
        """Track API usage statistics"""
        self.total_calls += 1
        tokens = usage.input_tokens + usage.output_tokens
        self.total_tokens += tokens

        cost = self._calculate_cost(usage.input_tokens, usage.output_tokens)
        self.total_cost += cost

    def get_statistics(self) -> Dict:
        """Get usage statistics"""
        return {
            'total_calls': self.total_calls,
            'total_tokens': self.total_tokens,
            'total_cost_usd': round(self.total_cost, 4),
            'avg_tokens_per_call': self.total_tokens / max(1, self.total_calls),
            'avg_cost_per_call': self.total_cost / max(1, self.total_calls),
            'model': self.model,
            'tier': self.tier,
            'enabled': self.enabled
        }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_tactical_ai(tier: str = 'BASIC') -> TacticalDecisionMaker:
    """
    Create tactical AI instance for given tier

    Args:
        tier: 'BASIC' (Haiku) or 'PRO' (Sonnet)

    Returns:
        TacticalDecisionMaker instance
    """
    return TacticalDecisionMaker(tier=tier)


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    'TacticalDecision',
    'TacticalDecisionMaker',
    'create_tactical_ai'
]
