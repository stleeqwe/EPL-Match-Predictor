# -*- coding: utf-8 -*-
"""
BallContestResolver - Resolve Loose Ball Contests

Part of Phase 2.0 Architecture Redesign
Resolves loose ball situations with multiple contestants

Key Innovation:
- Models spatial influence for each player near ball
- Considers distance, speed, positioning, reactions
- Realistic outcomes: Clear winner, continued contest, or rolling free
- Creates natural possession changes

This addresses the user's feedback:
> "When ball is loose, who gets it should depend on spatial influence:
   distance, speed towards ball, reactions, teammates nearby"
"""

import numpy as np
from enum import Enum
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass


class ContestOutcomeType(Enum):
    """Possible contest outcomes"""
    CONTROLLED = "controlled"  # Player won ball clearly
    CONTESTED = "contested"  # Still being fought over
    ROLLING_FREE = "rolling_free"  # No one won, ball escaped


@dataclass
class ContestOutcome:
    """
    Result of a ball contest

    Contains:
    - Outcome type
    - Winner (if controlled)
    - Ball position
    - Ball velocity
    - Player influences (for analysis)
    """
    outcome_type: ContestOutcomeType
    winner: Optional[any] = None
    ball_position: np.ndarray = None
    ball_velocity: np.ndarray = None
    player_influences: Dict[str, float] = None  # player_id -> influence


class BallContestResolver:
    """
    Resolves loose ball contests (multiple players)

    Used when:
    - Pass failed and ball is loose
    - Dribble failed and ball is loose
    - Tackle/clearance resulted in loose ball
    - Aerial duel knockdown
    - Deflection or rebound

    Process:
    1. Find all players within contest range
    2. Calculate each player's influence (distance, speed, reactions)
    3. Determine winner based on influence ratio
    4. Return outcome with ball state
    """

    def __init__(self):
        """Initialize ball contest resolver"""
        # Tuning parameters
        self.contest_range = 5.0  # Players within 5m can contest
        self.clear_winner_threshold = 0.6  # 60%+ influence = clear winner
        self.min_influence_to_win = 0.2  # Must have 20%+ to win

    def resolve(self, ball_position: np.ndarray, ball_velocity: np.ndarray,
                all_players: List[any], field_state: any = None,
                dt: float = 0.1) -> ContestOutcome:
        """
        Resolve a loose ball contest

        Args:
            ball_position: Current ball position [x, y, z]
            ball_velocity: Current ball velocity [vx, vy, vz]
            all_players: List of all player states (home + away)
            field_state: FieldState object (optional)
            dt: Time step (for predicting ball position)

        Returns:
            ContestOutcome with result
        """
        # 1. Predict where ball will be in next dt
        # (players react to where ball is going, not where it is)
        predicted_ball_pos = ball_position + ball_velocity * dt

        # 2. Find players in contest range
        contestants = self._find_contestants(predicted_ball_pos, all_players)

        # No contestants - ball rolling free
        if len(contestants) == 0:
            return ContestOutcome(
                outcome_type=ContestOutcomeType.ROLLING_FREE,
                winner=None,
                ball_position=ball_position.copy(),
                ball_velocity=ball_velocity.copy(),
                player_influences={}
            )

        # Single contestant - automatic winner
        if len(contestants) == 1:
            return ContestOutcome(
                outcome_type=ContestOutcomeType.CONTROLLED,
                winner=contestants[0],
                ball_position=ball_position.copy(),
                ball_velocity=ball_velocity.copy(),
                player_influences={contestants[0].id if hasattr(contestants[0], 'id') else 0: 1.0}
            )

        # 3. Multiple contestants - calculate influences
        influences = {}
        total_influence = 0.0

        for player in contestants:
            influence = self._calculate_player_influence(
                player, predicted_ball_pos, ball_velocity
            )
            influences[player] = influence
            total_influence += influence

        # 4. Determine outcome
        if total_influence < 0.001:
            # Edge case - no one has influence (shouldn't happen)
            return ContestOutcome(
                outcome_type=ContestOutcomeType.ROLLING_FREE,
                winner=None,
                ball_position=ball_position.copy(),
                ball_velocity=ball_velocity.copy(),
                player_influences={}
            )

        # Normalize influences to percentages
        influence_percentages = {
            player: (influence / total_influence)
            for player, influence in influences.items()
        }

        # Find player with highest influence
        winner = max(influence_percentages.items(), key=lambda x: x[1])
        winner_player = winner[0]
        winner_influence = winner[1]

        # Decide outcome based on winner's influence percentage
        if winner_influence >= self.clear_winner_threshold:
            # Clear winner - controls ball
            outcome_type = ContestOutcomeType.CONTROLLED
            # Ball goes to winner
            new_ball_pos = np.array(winner_player.position).copy()
            new_ball_vel = np.zeros(3)  # Controlled, stopped
        elif winner_influence >= self.min_influence_to_win:
            # Close contest - winner gets it but ball stays live
            outcome_type = ContestOutcomeType.CONTROLLED
            # Ball near winner but not fully controlled
            new_ball_pos = ball_position.copy()
            new_ball_vel = ball_velocity * 0.3  # Slowed down
        else:
            # No clear winner - contest continues or ball escapes
            # Roll to see if contest continues or ball escapes
            if np.random.random() < 0.6:
                outcome_type = ContestOutcomeType.CONTESTED
                new_ball_pos = ball_position.copy()
                # Ball gets kicked around in contest
                random_dir = np.random.randn(3)
                random_dir[2] = abs(random_dir[2]) * 0.3  # Small upward component
                random_dir = random_dir / (np.linalg.norm(random_dir) + 0.001)
                new_ball_vel = random_dir * 3.0  # Slow chaotic movement
            else:
                outcome_type = ContestOutcomeType.ROLLING_FREE
                new_ball_pos = ball_position.copy()
                new_ball_vel = ball_velocity * 0.7  # Ball escapes, slowed

            winner_player = None  # No winner yet

        # Build influence summary for analysis
        influence_summary = {
            (player.id if hasattr(player, 'id') else str(i)): pct
            for i, (player, pct) in enumerate(influence_percentages.items())
        }

        return ContestOutcome(
            outcome_type=outcome_type,
            winner=winner_player,
            ball_position=new_ball_pos,
            ball_velocity=new_ball_vel,
            player_influences=influence_summary
        )

    def _find_contestants(self, ball_position: np.ndarray,
                         players: List[any]) -> List[any]:
        """
        Find all players within contest range of ball

        Args:
            ball_position: Ball position [x, y, z]
            players: All players

        Returns:
            List of players within contest range
        """
        contestants = []

        for player in players:
            dist = self._distance_3d(
                np.array(player.position),
                ball_position
            )
            if dist < self.contest_range:
                contestants.append(player)

        return contestants

    def _calculate_player_influence(self, player: any,
                                   ball_position: np.ndarray,
                                   ball_velocity: np.ndarray) -> float:
        """
        Calculate player's influence in the contest

        Factors:
        - Distance to ball (40% weight) - closer is much better
        - Speed towards ball (30% weight) - moving towards helps
        - Reactions attribute (20% weight) - quick reactions help
        - Positioning attribute (10% weight) - good positioning helps

        Returns:
            Influence value (higher = more likely to win)
        """
        player_pos = np.array(player.position)

        # 1. Distance factor (40% weight)
        # Inverse square law - being close is VERY important
        distance = self._distance_3d(player_pos, ball_position)

        if distance < 0.1:
            distance_factor = 1.0
        else:
            # At 0m: 1.0, at 5m: 0.0
            distance_factor = (1.0 - distance / self.contest_range) ** 2
            distance_factor = max(0.0, distance_factor)

        # 2. Speed towards ball (30% weight)
        # Calculate player velocity towards ball
        if hasattr(player, 'velocity'):
            player_vel = np.array(player.velocity)
            to_ball = ball_position - player_pos
            to_ball_norm = np.linalg.norm(to_ball)

            if to_ball_norm > 0.001:
                to_ball_dir = to_ball / to_ball_norm
                # Dot product of player velocity with direction to ball
                speed_towards = np.dot(player_vel[:2], to_ball_dir[:2])
                # Normalize (typical sprint speed = 8 m/s)
                speed_factor = np.clip(speed_towards / 8.0, 0.0, 1.0)
            else:
                speed_factor = 0.5  # Already at ball
        else:
            # No velocity info - use speed attribute if available
            if hasattr(player, 'attributes') and hasattr(player.attributes, 'speed'):
                speed_attr = player.attributes.speed / 100.0
                speed_factor = speed_attr * 0.7  # Assume moving towards ball
            else:
                speed_factor = 0.5  # Default

        # 3. Reactions (20% weight)
        reactions = 70.0  # Default
        if hasattr(player, 'attributes') and hasattr(player.attributes, 'reactions'):
            reactions = player.attributes.reactions
        reactions_factor = reactions / 100.0

        # 4. Positioning (10% weight)
        positioning = 70.0  # Default
        if hasattr(player, 'attributes') and hasattr(player.attributes, 'positioning'):
            positioning = player.attributes.positioning
        positioning_factor = positioning / 100.0

        # Combine factors
        influence = (
            distance_factor * 0.40 +
            speed_factor * 0.30 +
            reactions_factor * 0.20 +
            positioning_factor * 0.10
        )

        return influence

    def resolve_simple(self, ball_position: np.ndarray,
                      players: List[any]) -> Optional[any]:
        """
        Simple resolution - just return closest player

        Used when full influence calculation not needed

        Args:
            ball_position: Ball position [x, y, z]
            players: List of players

        Returns:
            Closest player or None
        """
        if len(players) == 0:
            return None

        closest_player = None
        min_distance = self.contest_range

        for player in players:
            dist = self._distance_3d(
                np.array(player.position),
                ball_position
            )
            if dist < min_distance:
                min_distance = dist
                closest_player = player

        return closest_player

    def get_ball_possessor(self, ball_position: np.ndarray,
                          all_players: List[any],
                          control_radius: float = 2.0) -> Optional[any]:
        """
        Determine who (if anyone) currently possesses the ball

        This is a simpler check than resolve() - just checks if anyone
        is close enough to be considered "in control"

        Args:
            ball_position: Ball position [x, y, z]
            all_players: All players
            control_radius: Radius for possession (default 2m)

        Returns:
            Player in control, or None if loose
        """
        # If ball is in air, no one has possession
        if ball_position[2] > 1.0:
            return None

        # Find closest player
        closest_player = None
        min_distance = control_radius

        for player in all_players:
            dist = self._distance_3d(
                np.array(player.position),
                ball_position
            )
            if dist < min_distance:
                min_distance = dist
                closest_player = player

        return closest_player

    def _distance_3d(self, pos1: np.ndarray, pos2: np.ndarray) -> float:
        """Calculate 3D Euclidean distance"""
        return np.linalg.norm(pos2 - pos1)


# =============================================================================
# EXPORT
# =============================================================================

__all__ = ['BallContestResolver', 'ContestOutcome', 'ContestOutcomeType']
