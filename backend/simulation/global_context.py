# -*- coding: utf-8 -*-
"""
Global Context
Tracks global match state for team-level intelligence

Phase 1 Component for 95% balance target
"""

import numpy as np
from typing import Optional, Dict


class GlobalContext:
    """
    Track global match state across entire simulation

    Provides team-level awareness:
    - Who has possessed ball for how long
    - Overall possession balance
    - Ball location zone
    - Match phase

    This enables dynamic adjustments to prevent runaway possession.
    """

    def __init__(self):
        """Initialize global context"""
        # Possession tracking
        self.possession_timer = {'home': 0.0, 'away': 0.0}
        self.current_possessor = None  # 'home', 'away', or None
        self.last_possessor = None

        # Possession balance (-1.0 to +1.0)
        # -1.0 = away completely dominates
        #  0.0 = perfectly balanced
        # +1.0 = home completely dominates
        self.possession_balance = 0.0

        # Ball zone tracking
        self.ball_zone = 'middle'  # 'attacking_home', 'middle', 'attacking_away'

        # Match phase
        self.match_phase = 'early'  # 'early', 'mid', 'late'
        self.elapsed_time = 0.0

        # Statistics
        self.possession_changes = 0
        self.time_in_balance = 0.0  # Time spent in balanced state (<30% diff)

        # PHASE 1.5: Emergency tracking for extreme imbalances
        self.time_in_extreme_imbalance = 0.0  # Time spent in >80% imbalance
        self.last_imbalance_state = False  # Track if was in extreme imbalance last tick

    def update(
        self,
        dt: float,
        ball_position: np.ndarray,
        current_possessor: Optional[str],
        elapsed_time: float
    ):
        """
        Update global context

        Args:
            dt: Time step (seconds)
            ball_position: Current ball position [x, y, z]
            current_possessor: 'home', 'away', or None
            elapsed_time: Total elapsed match time
        """
        # Update elapsed time
        self.elapsed_time = elapsed_time

        # Update match phase
        if elapsed_time < 90:
            self.match_phase = 'early'
        elif elapsed_time < 210:
            self.match_phase = 'mid'
        else:
            self.match_phase = 'late'

        # Track possession changes
        if current_possessor != self.current_possessor:
            if current_possessor is not None and self.current_possessor is not None:
                self.possession_changes += 1
            self.last_possessor = self.current_possessor
            self.current_possessor = current_possessor

        # Update possession timer
        if current_possessor is not None:
            self.possession_timer[current_possessor] += dt

        # Calculate possession balance
        total_possession = self.possession_timer['home'] + self.possession_timer['away']
        if total_possession > 0:
            # Balance ranges from -1.0 (away dominant) to +1.0 (home dominant)
            self.possession_balance = (
                (self.possession_timer['home'] - self.possession_timer['away']) /
                total_possession
            )
        else:
            self.possession_balance = 0.0

        # Track time in balance
        if abs(self.possession_balance) < 0.3:  # Within 30% = balanced
            self.time_in_balance += dt

        # PHASE 1.5: Track time in extreme imbalance (>70%)
        is_extreme_imbalance = abs(self.possession_balance) > 0.7
        if is_extreme_imbalance:
            if self.last_imbalance_state:
                # Continuous extreme imbalance - accumulate time
                self.time_in_extreme_imbalance += dt
            else:
                # Just entered extreme imbalance - reset timer
                self.time_in_extreme_imbalance = dt
        else:
            # Not in extreme imbalance - reset
            self.time_in_extreme_imbalance = 0.0

        self.last_imbalance_state = is_extreme_imbalance

        # Update ball zone
        self._update_ball_zone(ball_position)

    def _update_ball_zone(self, ball_position: np.ndarray):
        """
        Update which zone ball is in

        Zones:
        - attacking_home: x > 35 (home attacking third)
        - attacking_away: x < -35 (away attacking third)
        - middle: -35 <= x <= 35
        """
        x = ball_position[0]

        if x > 35:
            self.ball_zone = 'attacking_home'
        elif x < -35:
            self.ball_zone = 'attacking_away'
        else:
            self.ball_zone = 'middle'

    def get_possession_percentages(self) -> Dict[str, float]:
        """
        Get current possession percentages

        Returns:
            {'home': float, 'away': float} - percentages (0-100)
        """
        total = self.possession_timer['home'] + self.possession_timer['away']
        if total == 0:
            return {'home': 50.0, 'away': 50.0}

        return {
            'home': (self.possession_timer['home'] / total) * 100.0,
            'away': (self.possession_timer['away'] / total) * 100.0
        }

    def is_imbalanced(self, threshold: float = 0.3) -> bool:
        """
        Check if possession is significantly imbalanced

        Args:
            threshold: Imbalance threshold (0.3 = 30% difference)

        Returns:
            True if imbalanced beyond threshold
        """
        return abs(self.possession_balance) > threshold

    def get_dominant_team(self) -> Optional[str]:
        """
        Get which team is dominating possession (if any)

        Returns:
            'home', 'away', or None if balanced
        """
        if abs(self.possession_balance) < 0.15:  # Within 15% = balanced
            return None

        return 'home' if self.possession_balance > 0 else 'away'

    def get_losing_team(self) -> Optional[str]:
        """
        Get which team is losing possession battle (if any)

        Returns:
            'home', 'away', or None if balanced
        """
        dominant = self.get_dominant_team()
        if dominant is None:
            return None

        return 'away' if dominant == 'home' else 'home'

    def get_summary(self) -> Dict:
        """
        Get summary statistics

        Returns:
            Dictionary with context statistics
        """
        percentages = self.get_possession_percentages()

        return {
            'possession_home': percentages['home'],
            'possession_away': percentages['away'],
            'possession_balance': self.possession_balance,
            'ball_zone': self.ball_zone,
            'match_phase': self.match_phase,
            'possession_changes': self.possession_changes,
            'time_in_balance': self.time_in_balance,
            'elapsed_time': self.elapsed_time,
            'is_imbalanced': self.is_imbalanced(),
            'dominant_team': self.get_dominant_team(),
            'losing_team': self.get_losing_team()
        }


# =============================================================================
# EXPORT
# =============================================================================

__all__ = ['GlobalContext']
