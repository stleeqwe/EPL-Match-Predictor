# -*- coding: utf-8 -*-
"""
Action Definitions for Agent Behavior System

All possible actions a player can take during a match.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Tuple
import numpy as np


class ActionType(Enum):
    """
    Core action types that agents can perform

    Categorized by situation:
    - Ball possession actions (SHOOT, PASS, DRIBBLE, CROSS, CLEAR)
    - Movement actions (MOVE_TO_POSITION, CHASE_BALL, MAKE_RUN)
    - Defensive actions (MARK_OPPONENT, TACKLE, INTERCEPT)
    - Goalkeeper actions (SAVE_SHOT, CATCH_BALL, DISTRIBUTE)
    - Special actions (IDLE, CELEBRATE)
    """

    # === Attacking Actions (with ball) ===
    SHOOT = "shoot"
    PASS = "pass"
    DRIBBLE = "dribble"
    CROSS = "cross"

    # === Ball Control ===
    CONTROL_BALL = "control_ball"
    SHIELD_BALL = "shield_ball"

    # === Defensive Actions ===
    TACKLE = "tackle"
    INTERCEPT = "intercept"
    MARK_OPPONENT = "mark_opponent"
    CLEAR_BALL = "clear_ball"
    BLOCK_SHOT = "block_shot"

    # === Movement Actions ===
    CHASE_BALL = "chase_ball"
    MOVE_TO_POSITION = "move_to_position"
    MAKE_RUN = "make_run"
    TRACK_BACK = "track_back"
    PRESS_OPPONENT = "press_opponent"

    # === Goalkeeper Actions ===
    SAVE_SHOT = "save_shot"
    CATCH_BALL = "catch_ball"
    PUNCH_BALL = "punch_ball"
    DISTRIBUTE = "distribute"
    STAY_ON_LINE = "stay_on_line"

    # === Idle/Special ===
    IDLE = "idle"
    CELEBRATE = "celebrate"


@dataclass
class Action:
    """
    Complete action with parameters

    Attributes:
        action_type: Type of action to perform
        target_position: Target position for movement (x, y)
        target_velocity: Desired velocity vector (vx, vy)
        target_player_id: ID of teammate/opponent (for pass/mark)
        power: Action power (0-100) for shots/passes
        direction: Direction vector (normalized)
        metadata: Additional action-specific data
    """
    action_type: ActionType
    target_position: Optional[np.ndarray] = None
    target_velocity: Optional[np.ndarray] = None
    target_player_id: Optional[str] = None
    power: float = 50.0
    direction: Optional[np.ndarray] = None
    metadata: dict = None

    def __post_init__(self):
        """Ensure numpy arrays and defaults"""
        if self.target_position is not None and not isinstance(self.target_position, np.ndarray):
            self.target_position = np.array(self.target_position, dtype=float)

        if self.target_velocity is not None and not isinstance(self.target_velocity, np.ndarray):
            self.target_velocity = np.array(self.target_velocity, dtype=float)

        if self.direction is not None and not isinstance(self.direction, np.ndarray):
            self.direction = np.array(self.direction, dtype=float)

        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        result = {
            'action_type': self.action_type.value,
            'power': float(self.power),
            'metadata': self.metadata
        }

        if self.target_position is not None:
            result['target_position'] = {
                'x': float(self.target_position[0]),
                'y': float(self.target_position[1])
            }

        if self.target_velocity is not None:
            result['target_velocity'] = {
                'vx': float(self.target_velocity[0]),
                'vy': float(self.target_velocity[1])
            }

        if self.direction is not None:
            result['direction'] = {
                'x': float(self.direction[0]),
                'y': float(self.direction[1])
            }

        if self.target_player_id is not None:
            result['target_player_id'] = self.target_player_id

        return result

    @classmethod
    def create_shoot(cls, target_position: np.ndarray, power: float = 80.0) -> 'Action':
        """Create a SHOOT action"""
        return cls(
            action_type=ActionType.SHOOT,
            target_position=target_position,
            power=power,
            metadata={'action': 'shoot'}
        )

    @classmethod
    def create_pass(cls, target_player_id: str, target_position: np.ndarray,
                   power: float = 50.0) -> 'Action':
        """Create a PASS action"""
        return cls(
            action_type=ActionType.PASS,
            target_player_id=target_player_id,
            target_position=target_position,
            power=power,
            metadata={'action': 'pass'}
        )

    @classmethod
    def create_dribble(cls, direction: np.ndarray, power: float = 60.0) -> 'Action':
        """Create a DRIBBLE action"""
        # Normalize direction
        norm = np.linalg.norm(direction)
        if norm > 0:
            direction = direction / norm

        return cls(
            action_type=ActionType.DRIBBLE,
            direction=direction,
            power=power,
            metadata={'action': 'dribble'}
        )

    @classmethod
    def create_move_to_position(cls, target_position: np.ndarray,
                               speed: float = 70.0) -> 'Action':
        """Create a MOVE_TO_POSITION action"""
        return cls(
            action_type=ActionType.MOVE_TO_POSITION,
            target_position=target_position,
            power=speed,
            metadata={'action': 'move'}
        )

    @classmethod
    def create_chase_ball(cls, ball_position: np.ndarray, speed: float = 90.0) -> 'Action':
        """Create a CHASE_BALL action"""
        return cls(
            action_type=ActionType.CHASE_BALL,
            target_position=ball_position,
            power=speed,
            metadata={'action': 'chase'}
        )

    @classmethod
    def create_mark_opponent(cls, opponent_id: str, opponent_position: np.ndarray) -> 'Action':
        """Create a MARK_OPPONENT action"""
        return cls(
            action_type=ActionType.MARK_OPPONENT,
            target_player_id=opponent_id,
            target_position=opponent_position,
            power=70.0,
            metadata={'action': 'mark'}
        )

    @classmethod
    def create_tackle(cls, opponent_position: np.ndarray, power: float = 80.0) -> 'Action':
        """Create a TACKLE action"""
        return cls(
            action_type=ActionType.TACKLE,
            target_position=opponent_position,
            power=power,
            metadata={'action': 'tackle'}
        )

    @classmethod
    def create_clear_ball(cls, direction: np.ndarray, power: float = 90.0) -> 'Action':
        """Create a CLEAR_BALL action (kick it away)"""
        # Normalize direction
        norm = np.linalg.norm(direction)
        if norm > 0:
            direction = direction / norm

        return cls(
            action_type=ActionType.CLEAR_BALL,
            direction=direction,
            power=power,
            metadata={'action': 'clear'}
        )

    @classmethod
    def create_save_shot(cls, ball_position: np.ndarray) -> 'Action':
        """Create a SAVE_SHOT action (goalkeeper)"""
        return cls(
            action_type=ActionType.SAVE_SHOT,
            target_position=ball_position,
            power=100.0,
            metadata={'action': 'save'}
        )

    @classmethod
    def create_idle(cls) -> 'Action':
        """Create an IDLE action"""
        return cls(
            action_type=ActionType.IDLE,
            power=0.0,
            metadata={'action': 'idle'}
        )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def calculate_shot_direction(
    player_position: np.ndarray,
    goal_position: np.ndarray,
    accuracy: float = 0.9
) -> np.ndarray:
    """
    Calculate shot direction with some inaccuracy

    Args:
        player_position: Player's current position [x, y]
        goal_position: Target goal position [x, y]
        accuracy: Shooting accuracy (0-1), where 1 = perfect

    Returns:
        Direction vector (normalized)
    """
    # Base direction to goal
    direction = goal_position - player_position

    # Add random error based on accuracy
    if accuracy < 1.0:
        error_angle = (1.0 - accuracy) * 0.2  # Max ±0.2 radians (±11 degrees)
        angle_offset = np.random.uniform(-error_angle, error_angle)

        # Rotate direction by error angle
        cos_theta = np.cos(angle_offset)
        sin_theta = np.sin(angle_offset)

        rotation_matrix = np.array([
            [cos_theta, -sin_theta],
            [sin_theta, cos_theta]
        ])

        direction = rotation_matrix @ direction

    # Normalize
    norm = np.linalg.norm(direction)
    if norm > 0:
        direction = direction / norm

    return direction


def calculate_pass_power(distance: float, pass_type: str = 'medium') -> float:
    """
    Calculate appropriate pass power based on distance

    Args:
        distance: Distance to target (meters)
        pass_type: 'short', 'medium', 'long'

    Returns:
        Pass power (0-100)
    """
    if pass_type == 'short':
        # Short pass: 5-15m, power 20-40
        return min(40.0, 20.0 + distance * 1.5)
    elif pass_type == 'long':
        # Long pass: 30-50m, power 70-100
        return min(100.0, 50.0 + distance * 1.0)
    else:  # medium
        # Medium pass: 15-30m, power 40-70
        return min(70.0, 30.0 + distance * 1.5)


def is_in_shooting_range(
    player_position: np.ndarray,
    goal_position: np.ndarray,
    max_range: float = 30.0,
    optimal_range: float = 15.0
) -> Tuple[bool, float]:
    """
    Check if player is in shooting range

    Args:
        player_position: Player's position [x, y]
        goal_position: Goal position [x, y]
        max_range: Maximum shooting distance (meters)
        optimal_range: Optimal shooting distance (meters)

    Returns:
        (is_in_range, quality) where quality is 0-1
    """
    distance = np.linalg.norm(goal_position - player_position)

    if distance > max_range:
        return False, 0.0

    # Quality decreases with distance
    if distance <= optimal_range:
        quality = 1.0 - (distance / optimal_range) * 0.3  # 70-100% quality
    else:
        quality = 0.7 * (1.0 - (distance - optimal_range) / (max_range - optimal_range))

    return True, max(0.0, min(1.0, quality))


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    'ActionType',
    'Action',
    'calculate_shot_direction',
    'calculate_pass_power',
    'is_in_shooting_range'
]
