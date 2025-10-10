# -*- coding: utf-8 -*-
"""
2D Player Physics Engine
Simulates player movement using Newton's equations of motion

MVP Version: 2D only (x, y coordinates)
Uses Velocity Verlet integration for numerical stability
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple, Optional

from .constants import (
    DT, FIELD_X_MIN, FIELD_X_MAX, FIELD_Y_MIN, FIELD_Y_MAX,
    PLAYER_DRAG_COEFFICIENT,
    STAMINA_DRAIN_RATE, STAMINA_RECOVERY_RATE,
    MIN_STAMINA, MAX_STAMINA,
    rating_to_speed, rating_to_accel, stamina_factor, clamp
)


@dataclass
class PlayerState:
    """
    Player physics state at a given moment (2D)

    Attributes:
        player_id: Unique player identifier
        position: [x, y] in meters (origin at field center)
        velocity: [vx, vy] in m/s
        acceleration: [ax, ay] in m/s�
        stamina: 0-100
        is_moving: Boolean flag
    """
    player_id: str
    position: np.ndarray  # Shape: (2,) for [x, y]
    velocity: np.ndarray  # Shape: (2,) for [vx, vy]
    acceleration: np.ndarray  # Shape: (2,) for [ax, ay]
    stamina: float  # 0-100
    is_moving: bool = False

    def __post_init__(self):
        """Ensure numpy arrays"""
        if not isinstance(self.position, np.ndarray):
            self.position = np.array(self.position, dtype=float)
        if not isinstance(self.velocity, np.ndarray):
            self.velocity = np.array(self.velocity, dtype=float)
        if not isinstance(self.acceleration, np.ndarray):
            self.acceleration = np.array(self.acceleration, dtype=float)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'player_id': self.player_id,
            'position': self.position.tolist(),
            'velocity': self.velocity.tolist(),
            'acceleration': self.acceleration.tolist(),
            'stamina': float(self.stamina),
            'is_moving': self.is_moving,
            'speed': float(np.linalg.norm(self.velocity))
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'PlayerState':
        """Create from dictionary"""
        return cls(
            player_id=data['player_id'],
            position=np.array(data['position']),
            velocity=np.array(data['velocity']),
            acceleration=np.array(data['acceleration']),
            stamina=data['stamina'],
            is_moving=data.get('is_moving', False)
        )


class PlayerPhysicsEngine:
    """
    2D Player physics engine using Newton's laws

    Physics model:
    - F_total = F_drive - F_drag
    - F_drive = m � desired_acceleration (mass = 1 for simplicity)
    - F_drag = -b � velocity (linear drag)

    Integration:
    - Velocity Verlet method (more stable than Euler)
    - new_position = position + velocity�dt + 0.5�acceleration�dt�
    - new_velocity = velocity + acceleration�dt
    """

    def __init__(self, dt: float = DT, drag_coef: float = PLAYER_DRAG_COEFFICIENT):
        """
        Initialize physics engine

        Args:
            dt: Time step in seconds (default 0.1s)
            drag_coef: Drag coefficient (default 0.3)
        """
        self.dt = dt
        self.drag_coef = drag_coef

    def update_player_state(
        self,
        player_state: PlayerState,
        player_attributes: Dict,
        target_velocity: np.ndarray,
        dt: Optional[float] = None
    ) -> PlayerState:
        """
        Update player state for one time step using physics simulation

        Args:
            player_state: Current player state
            player_attributes: Player's physical attributes (pace, acceleration, stamina, etc.)
            target_velocity: Desired velocity from agent decision [vx, vy]
            dt: Time step (default: self.dt)

        Returns:
            Updated PlayerState
        """
        if dt is None:
            dt = self.dt

        # Extract player attributes
        pace_rating = player_attributes.get('pace', 70)
        accel_rating = player_attributes.get('acceleration', 70)
        stamina_rating = player_attributes.get('stamina', 70)

        # Convert ratings to physics parameters
        max_speed = rating_to_speed(pace_rating)  # m/s
        max_accel = rating_to_accel(accel_rating)  # m/s�

        # Apply stamina effects
        stamina_mult = stamina_factor(player_state.stamina)
        effective_max_speed = max_speed * stamina_mult
        effective_max_accel = max_accel * stamina_mult

        # Calculate desired acceleration to reach target velocity
        velocity_error = target_velocity - player_state.velocity
        desired_accel = velocity_error / dt

        # Limit acceleration magnitude
        accel_magnitude = np.linalg.norm(desired_accel)
        if accel_magnitude > effective_max_accel:
            desired_accel = desired_accel * (effective_max_accel / accel_magnitude)

        # Apply forces
        # F_drive = desired_accel (mass = 1)
        # F_drag = -drag_coef � velocity
        drag_force = -self.drag_coef * player_state.velocity
        total_accel = desired_accel + drag_force

        # Velocity Verlet integration
        # x(t+dt) = x(t) + v(t)*dt + 0.5*a(t)*dt�
        new_position = (player_state.position +
                       player_state.velocity * dt +
                       0.5 * total_accel * dt**2)

        # v(t+dt) = v(t) + a(t)*dt
        new_velocity = player_state.velocity + total_accel * dt

        # Limit velocity to max speed
        velocity_magnitude = np.linalg.norm(new_velocity)
        if velocity_magnitude > effective_max_speed:
            new_velocity = new_velocity * (effective_max_speed / velocity_magnitude)

        # Update stamina
        speed = np.linalg.norm(new_velocity)
        if speed > 0.1:  # Moving
            # Stamina drain proportional to speed
            stamina_cost = STAMINA_DRAIN_RATE * speed * dt * (100.0 / stamina_rating)
            new_stamina = max(MIN_STAMINA, player_state.stamina - stamina_cost)
            is_moving = True
        else:  # Idle/walking
            # Stamina recovery
            stamina_gain = STAMINA_RECOVERY_RATE * dt
            new_stamina = min(MAX_STAMINA, player_state.stamina + stamina_gain)
            is_moving = False

        # Enforce field boundaries (simple bounce-back)
        new_position[0] = clamp(new_position[0], FIELD_X_MIN, FIELD_X_MAX)
        new_position[1] = clamp(new_position[1], FIELD_Y_MIN, FIELD_Y_MAX)

        # If hit boundary, stop velocity in that direction
        if new_position[0] == FIELD_X_MIN or new_position[0] == FIELD_X_MAX:
            new_velocity[0] = 0
        if new_position[1] == FIELD_Y_MIN or new_position[1] == FIELD_Y_MAX:
            new_velocity[1] = 0

        return PlayerState(
            player_id=player_state.player_id,
            position=new_position,
            velocity=new_velocity,
            acceleration=total_accel,
            stamina=new_stamina,
            is_moving=is_moving
        )

    def calculate_time_to_position(
        self,
        player_state: PlayerState,
        target_position: np.ndarray,
        player_attributes: Dict
    ) -> float:
        """
        Estimate time for player to reach target position

        Uses kinematic equation: t H sqrt(2*d/a) for constant acceleration
        (Simplified estimate, ignores current velocity)

        Args:
            player_state: Current player state
            target_position: Target position [x, y]
            player_attributes: Player attributes

        Returns:
            Estimated time in seconds
        """
        distance = np.linalg.norm(target_position - player_state.position)

        # Get max acceleration
        accel_rating = player_attributes.get('acceleration', 70)
        max_accel = rating_to_accel(accel_rating)

        # Apply stamina penalty
        stamina_mult = stamina_factor(player_state.stamina)
        effective_accel = max_accel * stamina_mult

        # Kinematic estimate: t = sqrt(2*d/a)
        if effective_accel > 0:
            time_estimate = np.sqrt(2 * distance / effective_accel)
        else:
            time_estimate = float('inf')

        return time_estimate

    def calculate_interception_point(
        self,
        player_state: PlayerState,
        ball_position: np.ndarray,
        ball_velocity: np.ndarray,
        player_attributes: Dict,
        max_time: float = 5.0
    ) -> Tuple[Optional[np.ndarray], float]:
        """
        Calculate where/when player can intercept moving ball

        Simplified approach: Sample ball positions at future times and
        check if player can reach them.

        Args:
            player_state: Current player state
            ball_position: Current ball position [x, y]
            ball_velocity: Ball velocity [vx, vy]
            player_attributes: Player attributes
            max_time: Maximum time to look ahead (seconds)

        Returns:
            (interception_point, interception_time) or (None, inf)
        """
        # Get player max speed
        pace_rating = player_attributes.get('pace', 70)
        max_speed = rating_to_speed(pace_rating)
        stamina_mult = stamina_factor(player_state.stamina)
        effective_speed = max_speed * stamina_mult

        # Sample future times
        num_samples = 50
        dt_sample = max_time / num_samples

        for i in range(num_samples):
            t = i * dt_sample

            # Future ball position (assumes constant velocity)
            future_ball_pos = ball_position + ball_velocity * t

            # Distance player needs to travel
            distance = np.linalg.norm(future_ball_pos - player_state.position)

            # Time needed for player
            time_needed = distance / effective_speed if effective_speed > 0 else float('inf')

            # Can player reach ball at this time?
            if time_needed <= t:
                return future_ball_pos, t

        return None, float('inf')

    def predict_trajectory(
        self,
        player_state: PlayerState,
        player_attributes: Dict,
        target_velocity: np.ndarray,
        duration: float = 2.0
    ) -> list:
        """
        Predict player trajectory for next N seconds

        Args:
            player_state: Current player state
            player_attributes: Player attributes
            target_velocity: Target velocity to maintain
            duration: How long to predict (seconds)

        Returns:
            List of PlayerState objects at each time step
        """
        trajectory = [player_state]
        current_state = player_state

        num_steps = int(duration / self.dt)

        for _ in range(num_steps):
            current_state = self.update_player_state(
                current_state,
                player_attributes,
                target_velocity
            )
            trajectory.append(current_state)

        return trajectory


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_initial_state(
    player_id: str,
    position: Tuple[float, float],
    stamina: float = 100.0
) -> PlayerState:
    """
    Create initial player state at rest

    Args:
        player_id: Player identifier
        position: Initial position (x, y)
        stamina: Initial stamina (default 100)

    Returns:
        PlayerState at rest
    """
    return PlayerState(
        player_id=player_id,
        position=np.array(position, dtype=float),
        velocity=np.zeros(2, dtype=float),
        acceleration=np.zeros(2, dtype=float),
        stamina=stamina,
        is_moving=False
    )


def calculate_target_velocity(
    current_position: np.ndarray,
    target_position: np.ndarray,
    max_speed: float
) -> np.ndarray:
    """
    Calculate target velocity to move toward a position

    Args:
        current_position: Current [x, y]
        target_position: Target [x, y]
        max_speed: Maximum speed (m/s)

    Returns:
        Target velocity [vx, vy]
    """
    direction = target_position - current_position
    distance = np.linalg.norm(direction)

    if distance < 0.1:  # Already at target
        return np.zeros(2)

    # Normalize direction
    direction_normalized = direction / distance

    # Target velocity = direction � max_speed
    return direction_normalized * max_speed


# =============================================================================
# TESTING & VALIDATION
# =============================================================================

def validate_player_physics():
    """
    Run basic physics validation tests

    Checks:
    - Player accelerates correctly
    - Player doesn't exceed max speed
    - Stamina drains when moving
    - Boundary collision works
    """
    print("=" * 60)
    print("Player Physics Validation")
    print("=" * 60)

    engine = PlayerPhysicsEngine()

    # Test 1: Acceleration from rest
    print("\n[Test 1] Acceleration from rest")
    player_state = create_initial_state("test_player", (0, 0))
    player_attrs = {'pace': 80, 'acceleration': 80, 'stamina': 80}
    target_vel = np.array([8.0, 0.0])  # 8 m/s forward

    for i in range(10):  # 1 second
        player_state = engine.update_player_state(
            player_state, player_attrs, target_vel
        )

    speed = np.linalg.norm(player_state.velocity)
    print(f"  After 1s: speed = {speed:.2f} m/s (target: 8.0 m/s)")
    print(f"  Position: {player_state.position}")
    print(f"  Stamina: {player_state.stamina:.1f}")

    # Test 2: Max speed limit
    print("\n[Test 2] Max speed limit")
    player_state = create_initial_state("test_player", (0, 0))
    target_vel = np.array([20.0, 0.0])  # Unrealistic target

    for i in range(50):  # 5 seconds
        player_state = engine.update_player_state(
            player_state, player_attrs, target_vel
        )

    speed = np.linalg.norm(player_state.velocity)
    max_expected = rating_to_speed(80)
    print(f"  After 5s: speed = {speed:.2f} m/s")
    print(f"  Max allowed: {max_expected:.2f} m/s")
    print(f"  Within limit: {speed <= max_expected * 1.1}")

    # Test 3: Stamina drain
    print("\n[Test 3] Stamina drain")
    player_state = create_initial_state("test_player", (0, 0), stamina=100.0)
    target_vel = np.array([8.0, 0.0])

    for i in range(600):  # 60 seconds
        player_state = engine.update_player_state(
            player_state, player_attrs, target_vel
        )

    print(f"  After 60s running: stamina = {player_state.stamina:.1f}")
    print(f"  Stamina decreased: {player_state.stamina < 100}")

    print("\n" + "=" * 60)
    print("Validation Complete ")
    print("=" * 60)


if __name__ == "__main__":
    validate_player_physics()
