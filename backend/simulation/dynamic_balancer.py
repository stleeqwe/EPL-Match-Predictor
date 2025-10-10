# -*- coding: utf-8 -*-
"""
Dynamic Balancer
Self-balancing mechanism to prevent runaway possession

Phase 1 Component for 95% balance target

Philosophy:
- Simulates realistic fatigue/pressure effects
- Losing team gets "desperation" boost (increased pressing)
- Winning team gets "complacency" penalty (tired, sloppy passes)
- Only activates when imbalance exceeds 30% (subtle, not obvious)
"""

import numpy as np
from typing import Dict


class DynamicBalancer:
    """
    Calculates dynamic adjustments to game mechanics based on possession balance

    This is the CRITICAL component for achieving 95% balance.
    It acts as a safety net that prevents extreme possession dominance.

    Adjustments are modeled as realistic phenomena:
    - Fatigue: Dominant team's passes become less accurate
    - Desperation: Losing team presses harder, tackles more aggressively
    - Psychological pressure: Affects both teams' performance

    The adjustments are gradual and scale with imbalance magnitude.
    """

    def __init__(self):
        """Initialize dynamic balancer"""
        # Tuning parameters
        # PHASE 1 FINAL: Aggressive parameters (70% balanced - best achievable)
        self.activation_threshold = 0.2  # Activate when imbalance > 20%
        self.max_adjustment_strength = 1.0  # Maximum adjustment at 70% imbalance

        # Adjustment ranges - Optimized for 70% balanced matches
        self.losing_tackle_range_max_boost = 1.0  # Up to +100%
        self.losing_interception_max_boost = 1.2  # Up to +120%
        self.losing_speed_max_boost = 0.3  # Up to +30%

        self.dominant_pass_accuracy_max_penalty = 0.4  # Up to -40%
        self.dominant_tackle_range_max_penalty = 0.3  # Up to -30%
        self.dominant_stamina_drain = 1.3  # Simulated fatigue multiplier

    def calculate_adjustments(
        self,
        possession_balance: float,
        match_phase: str = 'mid'
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate dynamic adjustments based on possession balance

        Args:
            possession_balance: -1.0 to +1.0
                -1.0 = away completely dominates
                 0.0 = perfectly balanced
                +1.0 = home completely dominates
            match_phase: 'early', 'mid', 'late' (affects adjustment strength)

        Returns:
            {
                'home': {
                    'tackle_range_multiplier': float,
                    'pass_accuracy_multiplier': float,
                    'interception_multiplier': float,
                    'speed_multiplier': float
                },
                'away': { ... }
            }
        """
        # Extract imbalance magnitude (absolute value)
        imbalance = abs(possession_balance)

        # Determine which team is dominant/losing
        if possession_balance > 0:
            dominant_team = 'home'
            losing_team = 'away'
        else:
            dominant_team = 'away'
            losing_team = 'home'

        # No adjustment if balance is acceptable
        if imbalance < self.activation_threshold:
            return self._neutral_adjustments()

        # Calculate adjustment strength (0.0 to 1.0)
        # Maps imbalance from [activation_threshold, 0.7] to [0.0, 1.0]
        adjustment_strength = min(
            1.0,
            (imbalance - self.activation_threshold) / (0.7 - self.activation_threshold)
        )

        # Phase modifier (late game = stronger adjustments to prevent blowouts)
        phase_multiplier = {
            'early': 0.8,  # Gentler in early game
            'mid': 1.0,    # Normal in mid game
            'late': 1.2    # Stronger in late game
        }.get(match_phase, 1.0)

        adjustment_strength *= phase_multiplier

        # Calculate losing team advantages (desperation boost)
        losing_tackle_boost = 1.0 + (
            self.losing_tackle_range_max_boost * adjustment_strength
        )
        losing_interception_boost = 1.0 + (
            self.losing_interception_max_boost * adjustment_strength
        )
        losing_speed_boost = 1.0 + (
            self.losing_speed_max_boost * adjustment_strength
        )

        # Calculate dominant team penalties (fatigue/complacency)
        dominant_pass_penalty = 1.0 - (
            self.dominant_pass_accuracy_max_penalty * adjustment_strength
        )
        dominant_tackle_penalty = 1.0 - (
            self.dominant_tackle_range_max_penalty * adjustment_strength
        )

        # Build adjustments dictionary
        adjustments = {
            'home': {
                'tackle_range_multiplier': 1.0,
                'pass_accuracy_multiplier': 1.0,
                'interception_multiplier': 1.0,
                'speed_multiplier': 1.0
            },
            'away': {
                'tackle_range_multiplier': 1.0,
                'pass_accuracy_multiplier': 1.0,
                'interception_multiplier': 1.0,
                'speed_multiplier': 1.0
            }
        }

        # Apply to appropriate teams
        adjustments[losing_team]['tackle_range_multiplier'] = losing_tackle_boost
        adjustments[losing_team]['interception_multiplier'] = losing_interception_boost
        adjustments[losing_team]['speed_multiplier'] = losing_speed_boost

        adjustments[dominant_team]['pass_accuracy_multiplier'] = dominant_pass_penalty
        adjustments[dominant_team]['tackle_range_multiplier'] = dominant_tackle_penalty

        return adjustments

    def _neutral_adjustments(self) -> Dict[str, Dict[str, float]]:
        """
        Return neutral adjustments (no changes)

        Returns:
            Adjustments with all multipliers at 1.0
        """
        return {
            'home': {
                'tackle_range_multiplier': 1.0,
                'pass_accuracy_multiplier': 1.0,
                'interception_multiplier': 1.0,
                'speed_multiplier': 1.0
            },
            'away': {
                'tackle_range_multiplier': 1.0,
                'pass_accuracy_multiplier': 1.0,
                'interception_multiplier': 1.0,
                'speed_multiplier': 1.0
            }
        }

    def get_adjustment_summary(
        self,
        possession_balance: float,
        match_phase: str = 'mid'
    ) -> str:
        """
        Get human-readable summary of current adjustments

        Args:
            possession_balance: -1.0 to +1.0
            match_phase: 'early', 'mid', 'late'

        Returns:
            String description of adjustments
        """
        adjustments = self.calculate_adjustments(possession_balance, match_phase)

        imbalance = abs(possession_balance)
        if imbalance < self.activation_threshold:
            return "No adjustments - possession balanced"

        dominant_team = 'home' if possession_balance > 0 else 'away'
        losing_team = 'away' if dominant_team == 'home' else 'home'

        summary = []
        summary.append(f"Imbalance: {imbalance*100:.1f}%")
        summary.append(f"Dominant team: {dominant_team.upper()}")

        # Losing team boosts
        losing_adj = adjustments[losing_team]
        summary.append(f"\n{losing_team.upper()} (losing) boosts:")
        summary.append(f"  Tackle range: +{(losing_adj['tackle_range_multiplier']-1)*100:.1f}%")
        summary.append(f"  Interception: +{(losing_adj['interception_multiplier']-1)*100:.1f}%")
        summary.append(f"  Speed: +{(losing_adj['speed_multiplier']-1)*100:.1f}%")

        # Dominant team penalties
        dom_adj = adjustments[dominant_team]
        summary.append(f"\n{dominant_team.upper()} (dominant) penalties:")
        summary.append(f"  Pass accuracy: {(dom_adj['pass_accuracy_multiplier']-1)*100:.1f}%")
        summary.append(f"  Tackle range: {(dom_adj['tackle_range_multiplier']-1)*100:.1f}%")

        return "\n".join(summary)


# =============================================================================
# EXPORT
# =============================================================================

__all__ = ['DynamicBalancer']
