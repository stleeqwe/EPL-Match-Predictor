# -*- coding: utf-8 -*-
"""
Action Executor
Converts agent actions into physics engine parameters

Responsibilities:
- Action → Target velocity conversion
- Ball interaction (kicks, passes, shots)
- Player-ball collision detection
- Action validation
"""

import numpy as np
from typing import Dict, Tuple, Optional
from dataclasses import dataclass

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.actions import Action, ActionType
from agents.simple_agent import PlayerGameState
from physics.player_physics import PlayerState, PlayerPhysicsEngine
from physics.ball_physics import BallState, BallPhysicsEngine
from physics.constants import (
    PLAYER_CONTROL_RADIUS,
    SHOT_POWER_BASE, SHOT_POWER_FACTOR,
    PASS_POWER_SHORT, PASS_POWER_MEDIUM, PASS_POWER_LONG,
    distance_2d, rating_to_speed
)


@dataclass
class BallInteraction:
    """Result of player-ball interaction"""
    ball_kicked: bool
    new_ball_velocity: Optional[np.ndarray] = None
    new_ball_spin: float = 0.0
    interaction_type: str = 'none'  # 'shot', 'pass', 'dribble', 'tackle'


class ActionExecutor:
    """
    Executes agent actions in physics engine

    Converts high-level actions (SHOOT, PASS, DRIBBLE) into
    low-level physics parameters (velocity vectors, forces)
    """

    def __init__(self):
        """Initialize action executor"""
        self.player_engine = PlayerPhysicsEngine()
        self.ball_engine = BallPhysicsEngine()

    def execute_action(
        self,
        action: Action,
        player_state: PlayerState,
        player_attributes: Dict,
        ball_state: BallState,
        dt: float = 0.1,
        team_adjustments: Optional[Dict[str, float]] = None
    ) -> Tuple[np.ndarray, Optional[BallInteraction]]:
        """
        Execute agent action

        Args:
            action: Action to execute
            player_state: Current player physics state
            player_attributes: Player attributes (pace, shooting, etc.)
            ball_state: Current ball state
            dt: Time step
            team_adjustments: PHASE 1 - Dynamic balance adjustments for this team
                             {'pass_accuracy_multiplier': float, 'speed_multiplier': float, ...}

        Returns:
            (target_velocity, ball_interaction)
            - target_velocity: Desired velocity for physics engine
            - ball_interaction: Ball interaction if any
        """
        # PHASE 1: Store adjustments for use in action handlers
        if team_adjustments is None:
            team_adjustments = {
                'pass_accuracy_multiplier': 1.0,
                'speed_multiplier': 1.0,
                'tackle_range_multiplier': 1.0,
                'interception_multiplier': 1.0
            }
        self._current_adjustments = team_adjustments

        action_type = action.action_type

        # Route to appropriate handler
        if action_type == ActionType.SHOOT:
            return self._execute_shoot(action, player_state, player_attributes, ball_state)

        elif action_type == ActionType.PASS:
            return self._execute_pass(action, player_state, player_attributes, ball_state)

        elif action_type == ActionType.DRIBBLE:
            return self._execute_dribble(action, player_state, player_attributes, ball_state)

        elif action_type == ActionType.CHASE_BALL:
            return self._execute_chase_ball(action, player_state, player_attributes, ball_state)

        elif action_type == ActionType.MOVE_TO_POSITION:
            return self._execute_move_to_position(action, player_state, player_attributes)

        elif action_type == ActionType.MARK_OPPONENT:
            return self._execute_mark_opponent(action, player_state, player_attributes)

        elif action_type == ActionType.TACKLE:
            return self._execute_tackle(action, player_state, player_attributes, ball_state)

        elif action_type == ActionType.CLEAR_BALL:
            return self._execute_clear_ball(action, player_state, player_attributes, ball_state)

        elif action_type == ActionType.SAVE_SHOT:
            return self._execute_save_shot(action, player_state, player_attributes, ball_state)

        elif action_type == ActionType.IDLE:
            return self._execute_idle(player_state)

        else:
            # Unknown action - idle
            return np.zeros(2), None

    # =========================================================================
    # ACTION HANDLERS
    # =========================================================================

    def _execute_shoot(
        self,
        action: Action,
        player_state: PlayerState,
        player_attributes: Dict,
        ball_state: BallState
    ) -> Tuple[np.ndarray, Optional[BallInteraction]]:
        """Execute SHOOT action"""
        # Check if player can shoot (has ball)
        if not self._player_has_ball(player_state, ball_state):
            # Move toward ball first
            return self._move_toward_ball(player_state, ball_state, player_attributes)

        # Calculate shot parameters
        shooting = player_attributes.get('shooting', 70) / 100.0
        power = action.power or 80.0

        # Shot speed based on shooting attribute
        shot_speed = SHOT_POWER_BASE + shooting * SHOT_POWER_FACTOR * (power / 100.0)

        # Direction to target
        target_pos = action.target_position
        if target_pos is None:
            # Default: straight forward
            direction = np.array([1.0, 0.0])
        else:
            direction = target_pos - player_state.position
            norm = np.linalg.norm(direction)
            if norm > 0:
                direction = direction / norm

        # Shot velocity (slightly upward for air shot)
        ball_velocity = np.array([
            direction[0] * shot_speed,
            direction[1] * shot_speed,
            shot_speed * 0.15  # Slight upward angle
        ])

        # Add spin for curve (advanced players)
        spin = np.random.uniform(-20, 20) * shooting

        # Player velocity: slight movement toward shot
        target_velocity = direction * rating_to_speed(player_attributes.get('pace', 70)) * 0.3

        interaction = BallInteraction(
            ball_kicked=True,
            new_ball_velocity=ball_velocity,
            new_ball_spin=spin,
            interaction_type='shot'
        )

        return target_velocity, interaction

    def _execute_pass(
        self,
        action: Action,
        player_state: PlayerState,
        player_attributes: Dict,
        ball_state: BallState
    ) -> Tuple[np.ndarray, Optional[BallInteraction]]:
        """Execute PASS action"""
        # Check if player has ball
        if not self._player_has_ball(player_state, ball_state):
            return self._move_toward_ball(player_state, ball_state, player_attributes)

        # Calculate pass parameters
        passing = player_attributes.get('passing', 70) / 100.0
        power = action.power or 60.0

        # Pass speed based on power
        if power < 40:
            pass_speed = PASS_POWER_SHORT
        elif power < 70:
            pass_speed = PASS_POWER_MEDIUM
        else:
            pass_speed = PASS_POWER_LONG

        # Adjust for passing skill
        pass_speed *= (0.8 + passing * 0.4)

        # Direction to target
        target_pos = action.target_position
        if target_pos is None:
            direction = np.array([1.0, 0.0])
        else:
            direction = target_pos - player_state.position
            norm = np.linalg.norm(direction)
            if norm > 0:
                direction = direction / norm

        # V10 FIX: Add pass inaccuracy to reduce 100% completion rate
        # Pass accuracy degrades based on:
        # 1. Passing skill (65-100% accuracy for skill 50-90)
        # 2. Pass distance (longer = less accurate)
        # 3. Pass power (harder passes = less accurate)

        distance_to_target = np.linalg.norm(target_pos - player_state.position) if target_pos is not None else 10.0

        # V11 TUNING: More aggressive pass failure to break feedback loop
        # Base accuracy from passing skill (50-85% for skill 50-90)
        base_accuracy = 0.35 + passing * 0.5

        # Distance penalty (up to 30% loss for 30m+ passes)
        distance_penalty = min(0.3, distance_to_target / 100.0)

        # Power penalty (harder passes are less accurate)
        power_penalty = (power / 100.0) * 0.15

        # PHASE 1: Apply dynamic balance adjustment to pass accuracy
        # Dominant teams get penalized (multiplier < 1.0)
        pass_accuracy_multiplier = self._current_adjustments.get('pass_accuracy_multiplier', 1.0)

        # Final accuracy (with dynamic adjustment)
        pass_accuracy = (base_accuracy - distance_penalty - power_penalty) * pass_accuracy_multiplier

        # Random check: does pass fail?
        if np.random.random() > pass_accuracy:
            # PHASE 1.7: ATTACK FAILURE - Pass fails creating turnover opportunity
            # User insight: Attacking team losing ball through mistakes is more natural

            # Moderate error angle - pass goes wrong direction but not absurdly
            error_angle = np.random.uniform(-1.0, 1.0)  # Up to 57 degrees error (balanced)
            cos_error = np.cos(error_angle)
            sin_error = np.sin(error_angle)

            # Rotate direction
            direction = np.array([
                direction[0] * cos_error - direction[1] * sin_error,
                direction[0] * sin_error + direction[1] * cos_error
            ])

            # Reduce power moderately - creates turnover opportunity
            pass_speed *= 0.5  # Slower for easier interception

        # Pass velocity (ground pass mostly)
        ball_velocity = np.array([
            direction[0] * pass_speed,
            direction[1] * pass_speed,
            pass_speed * 0.05  # Very slight elevation
        ])

        # Player velocity: follow through
        target_velocity = direction * rating_to_speed(player_attributes.get('pace', 70)) * 0.2

        interaction = BallInteraction(
            ball_kicked=True,
            new_ball_velocity=ball_velocity,
            new_ball_spin=0.0,
            interaction_type='pass'
        )

        return target_velocity, interaction

    def _execute_dribble(
        self,
        action: Action,
        player_state: PlayerState,
        player_attributes: Dict,
        ball_state: BallState
    ) -> Tuple[np.ndarray, Optional[BallInteraction]]:
        """Execute DRIBBLE action"""
        # Dribbling: move with ball
        direction = action.direction
        if direction is None:
            direction = np.array([1.0, 0.0])

        # Normalize direction
        norm = np.linalg.norm(direction)
        if norm > 0:
            direction = direction / norm

        # Dribble speed
        dribbling = player_attributes.get('dribbling', 70) / 100.0
        pace = player_attributes.get('pace', 70)
        dribble_speed = rating_to_speed(pace) * (0.6 + dribbling * 0.3)

        # PHASE 1: Apply dynamic speed multiplier (losing teams get boost)
        speed_multiplier = self._current_adjustments.get('speed_multiplier', 1.0)
        target_velocity = direction * dribble_speed * speed_multiplier

        # PHASE 1.7: ATTACK FAILURE - Add dribble failure mechanism
        # User insight: Dominant teams should lose ball through mistakes

        interaction = None
        if self._player_has_ball(player_state, ball_state):
            # Calculate dribble success rate based on dribbling skill
            dribble_success_rate = 0.92 + dribbling * 0.08  # 92-100% base rate (higher than pass)

            # PHASE 1: Apply dynamic penalty to dominant teams
            pass_accuracy_multiplier = self._current_adjustments.get('pass_accuracy_multiplier', 1.0)
            # Reuse pass accuracy multiplier as "attack failure" multiplier
            dribble_success_rate *= pass_accuracy_multiplier

            # Check if dribble fails
            if np.random.random() > dribble_success_rate:
                # DRIBBLE FAILED - Ball gets away from player (loose touch)
                # Ball goes forward with slight deviation
                error_direction = direction.copy()
                # Add random perpendicular component
                perpendicular = np.array([-direction[1], direction[0]])
                error_direction = error_direction + perpendicular * np.random.uniform(-0.3, 0.3)

                # Normalize safely (avoid division by zero)
                norm = np.linalg.norm(error_direction)
                if norm > 0.001:
                    error_direction = error_direction / norm
                else:
                    error_direction = direction  # Fallback to original direction

                # Ball shoots ahead slightly faster (loose touch)
                kick_velocity = np.array([
                    error_direction[0] * dribble_speed * 1.3,  # Slightly faster
                    error_direction[1] * dribble_speed * 1.3,
                    0.0
                ])
            else:
                # Normal dribble - ball stays with player
                kick_velocity = np.array([
                    direction[0] * dribble_speed * 1.0,
                    direction[1] * dribble_speed * 1.0,
                    0.0
                ])

            interaction = BallInteraction(
                ball_kicked=True,
                new_ball_velocity=kick_velocity,
                new_ball_spin=0.0,
                interaction_type='dribble'
            )

        return target_velocity, interaction

    def _execute_chase_ball(
        self,
        action: Action,
        player_state: PlayerState,
        player_attributes: Dict,
        ball_state: BallState
    ) -> Tuple[np.ndarray, Optional[BallInteraction]]:
        """Execute CHASE_BALL action"""
        return self._move_toward_ball(player_state, ball_state, player_attributes, speed_mult=0.9)

    def _execute_move_to_position(
        self,
        action: Action,
        player_state: PlayerState,
        player_attributes: Dict
    ) -> Tuple[np.ndarray, Optional[BallInteraction]]:
        """Execute MOVE_TO_POSITION action"""
        target_pos = action.target_position
        if target_pos is None:
            return np.zeros(2), None

        # Direction to target
        direction = target_pos - player_state.position
        distance = np.linalg.norm(direction)

        if distance < 1.0:
            # Close enough, slow down
            return np.zeros(2), None

        direction = direction / distance

        # Speed based on action power
        pace = player_attributes.get('pace', 70)
        speed_factor = (action.power or 60.0) / 100.0
        target_speed = rating_to_speed(pace) * speed_factor

        target_velocity = direction * target_speed

        return target_velocity, None

    def _execute_mark_opponent(
        self,
        action: Action,
        player_state: PlayerState,
        player_attributes: Dict
    ) -> Tuple[np.ndarray, Optional[BallInteraction]]:
        """Execute MARK_OPPONENT action"""
        # Move toward opponent position
        target_pos = action.target_position
        if target_pos is None:
            return np.zeros(2), None

        direction = target_pos - player_state.position
        distance = np.linalg.norm(direction)

        if distance < 2.0:
            # Close enough, match movement
            return np.zeros(2), None

        direction = direction / distance

        # Marking speed
        pace = player_attributes.get('pace', 70)
        target_velocity = direction * rating_to_speed(pace) * 0.7

        return target_velocity, None

    def _execute_tackle(
        self,
        action: Action,
        player_state: PlayerState,
        player_attributes: Dict,
        ball_state: BallState
    ) -> Tuple[np.ndarray, Optional[BallInteraction]]:
        """Execute TACKLE action"""
        # Move toward ball aggressively
        target_velocity = self._move_toward_ball(
            player_state, ball_state, player_attributes, speed_mult=1.0
        )[0]

        # If close enough, kick ball away
        interaction = None
        distance = distance_2d(
            player_state.position[0], player_state.position[1],
            ball_state.position[0], ball_state.position[1]
        )

        # V7 TUNING: Tighter tackle range (1.2x instead of 1.5x) + success probability
        # This prevents tackles from being too easy/frequent
        if distance < PLAYER_CONTROL_RADIUS * 1.2:
            # Tackle success based on defending attribute (50-90% success)
            defending = player_attributes.get('defending', 60) / 100.0
            tackle_success_chance = 0.5 + defending * 0.4  # 50-90% range

            if np.random.random() < tackle_success_chance:
                # Successful tackle - kick ball away (clearance)
                tackle_direction = np.random.uniform(-1, 1, 2)
                tackle_direction = tackle_direction / np.linalg.norm(tackle_direction)

                kick_velocity = np.array([
                    tackle_direction[0] * 15.0,
                    tackle_direction[1] * 15.0,
                    5.0  # High clearance
                ])

                interaction = BallInteraction(
                    ball_kicked=True,
                    new_ball_velocity=kick_velocity,
                    new_ball_spin=0.0,
                    interaction_type='tackle'
                )

        return target_velocity, interaction

    def _execute_clear_ball(
        self,
        action: Action,
        player_state: PlayerState,
        player_attributes: Dict,
        ball_state: BallState
    ) -> Tuple[np.ndarray, Optional[BallInteraction]]:
        """Execute CLEAR_BALL action"""
        # Similar to tackle but in specified direction
        if not self._player_has_ball(player_state, ball_state):
            return self._move_toward_ball(player_state, ball_state, player_attributes)

        # Clear in specified direction
        direction = action.direction
        if direction is None:
            direction = np.array([1.0, 0.0])

        direction = direction / np.linalg.norm(direction)

        # Powerful clearance
        clear_velocity = np.array([
            direction[0] * 25.0,
            direction[1] * 25.0,
            12.0  # High and far
        ])

        interaction = BallInteraction(
            ball_kicked=True,
            new_ball_velocity=clear_velocity,
            new_ball_spin=0.0,
            interaction_type='clearance'
        )

        target_velocity = direction * rating_to_speed(player_attributes.get('pace', 70)) * 0.3

        return target_velocity, interaction

    def _execute_save_shot(
        self,
        action: Action,
        player_state: PlayerState,
        player_attributes: Dict,
        ball_state: BallState
    ) -> Tuple[np.ndarray, Optional[BallInteraction]]:
        """Execute SAVE_SHOT action (goalkeeper)"""
        # Dive toward ball
        direction = ball_state.position[:2] - player_state.position
        distance = np.linalg.norm(direction)

        if distance > 0:
            direction = direction / distance

        # Diving speed (reflexes)
        reflexes = player_attributes.get('reflexes', 70) / 100.0
        dive_speed = rating_to_speed(70) * (1.0 + reflexes * 0.5)

        target_velocity = direction * dive_speed

        # If close enough, deflect ball
        interaction = None
        if distance < PLAYER_CONTROL_RADIUS * 2.0:
            # Deflect ball (random direction)
            deflect_dir = np.random.uniform(-1, 1, 2)
            deflect_dir = deflect_dir / np.linalg.norm(deflect_dir)

            deflect_velocity = np.array([
                deflect_dir[0] * 10.0,
                deflect_dir[1] * 10.0,
                5.0
            ])

            interaction = BallInteraction(
                ball_kicked=True,
                new_ball_velocity=deflect_velocity,
                new_ball_spin=0.0,
                interaction_type='save'
            )

        return target_velocity, interaction

    def _execute_idle(
        self,
        player_state: PlayerState
    ) -> Tuple[np.ndarray, Optional[BallInteraction]]:
        """Execute IDLE action"""
        return np.zeros(2), None

    # =========================================================================
    # HELPER FUNCTIONS
    # =========================================================================

    def _player_has_ball(
        self,
        player_state: PlayerState,
        ball_state: BallState
    ) -> bool:
        """Check if player has ball control"""
        # Ball must be on ground and within control radius
        if ball_state.position[2] > 0.5:  # Ball in air
            return False

        distance = distance_2d(
            player_state.position[0], player_state.position[1],
            ball_state.position[0], ball_state.position[1]
        )

        return distance < PLAYER_CONTROL_RADIUS

    def _move_toward_ball(
        self,
        player_state: PlayerState,
        ball_state: BallState,
        player_attributes: Dict,
        speed_mult: float = 0.9
    ) -> Tuple[np.ndarray, Optional[BallInteraction]]:
        """Move player toward ball"""
        direction = ball_state.position[:2] - player_state.position
        distance = np.linalg.norm(direction)

        if distance > 0:
            direction = direction / distance

        pace = player_attributes.get('pace', 70)
        base_speed = rating_to_speed(pace) * speed_mult

        # PHASE 1: Apply dynamic speed multiplier (losing teams get boost)
        speed_multiplier = self._current_adjustments.get('speed_multiplier', 1.0)
        target_velocity = direction * base_speed * speed_multiplier

        return target_velocity, None


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    'BallInteraction',
    'ActionExecutor'
]
