# -*- coding: utf-8 -*-
"""
2D Ball Physics Engine
Ball trajectory with gravity, drag, and simplified Magnus effect

MVP Version: 2D horizontal (x, y) + height (h)
- Ball position: [x, y, h] where h = height off ground
- Ball velocity: [vx, vy, vh] where vh = vertical velocity
- Spin: single value (clockwise/counter-clockwise) instead of 3D vector
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple, List, Optional

from .constants import (
    DT, BALL_MASS, BALL_RADIUS, AIR_DENSITY,
    BALL_DRAG_COEFFICIENT, BALL_CROSS_SECTIONAL_AREA,
    BALL_MAGNUS_COEFFICIENT, BALL_SPIN_DECAY, BALL_SPIN_DECAY_GROUND,
    GRAVITY, BALL_BOUNCE_COEF, BALL_FRICTION_COEF,
    GROUND_LEVEL, BALL_GROUND_THRESHOLD, ROLLING_RESISTANCE,
    FIELD_X_MIN, FIELD_X_MAX, FIELD_Y_MIN, FIELD_Y_MAX,
    GOAL_WIDTH, GOAL_HEIGHT, is_in_goal
)


@dataclass
class BallState:
    """
    Ball physics state (2D + height)

    Attributes:
        position: [x, y, h] in meters (h = height off ground)
        velocity: [vx, vy, vh] in m/s (vh = vertical velocity)
        spin: Spin rate in rad/s (positive = clockwise, negative = counter-clockwise)
              Simplified from 3D spin vector for MVP
    """
    position: np.ndarray  # Shape: (3,) for [x, y, h]
    velocity: np.ndarray  # Shape: (3,) for [vx, vy, vh]
    spin: float  # rad/s (simplified 2D spin)

    def __post_init__(self):
        """Ensure numpy arrays"""
        if not isinstance(self.position, np.ndarray):
            self.position = np.array(self.position, dtype=float)
        if not isinstance(self.velocity, np.ndarray):
            self.velocity = np.array(self.velocity, dtype=float)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'position': {
                'x': float(self.position[0]),
                'y': float(self.position[1]),
                'h': float(self.position[2])
            },
            'velocity': {
                'vx': float(self.velocity[0]),
                'vy': float(self.velocity[1]),
                'vh': float(self.velocity[2])
            },
            'spin': float(self.spin),
            'speed': float(np.linalg.norm(self.velocity[:2])),  # Horizontal speed only
            'is_on_ground': self.position[2] < BALL_GROUND_THRESHOLD
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'BallState':
        """Create from dictionary"""
        if 'position' in data and isinstance(data['position'], dict):
            position = np.array([data['position']['x'], data['position']['y'], data['position']['h']])
            velocity = np.array([data['velocity']['vx'], data['velocity']['vy'], data['velocity']['vh']])
        else:
            position = np.array(data['position'])
            velocity = np.array(data['velocity'])

        return cls(
            position=position,
            velocity=velocity,
            spin=data.get('spin', 0.0)
        )


class BallPhysicsEngine:
    """
    2D ball physics with gravity, drag, and Magnus effect

    Forces:
    1. Gravity: F_g = -mg (vertical only)
    2. Drag: F_d = -0.5 � � � Cd � A � |v| � v
    3. Magnus (spin): Simplified 2D version for MVP

    Integration: Velocity Verlet
    """

    def __init__(self, dt: float = DT):
        """
        Initialize ball physics engine

        Args:
            dt: Time step in seconds (default 0.1s)
        """
        self.dt = dt
        self.mass = BALL_MASS
        self.radius = BALL_RADIUS
        self.area = BALL_CROSS_SECTIONAL_AREA
        self.rho = AIR_DENSITY
        self.Cd = BALL_DRAG_COEFFICIENT
        self.Cl = BALL_MAGNUS_COEFFICIENT
        self.g = GRAVITY

    def update_ball_state(
        self,
        ball_state: BallState,
        dt: Optional[float] = None
    ) -> BallState:
        """
        Update ball state for one time step

        Args:
            ball_state: Current ball state
            dt: Time step (default: self.dt)

        Returns:
            Updated BallState
        """
        if dt is None:
            dt = self.dt

        pos = ball_state.position.copy()
        vel = ball_state.velocity.copy()
        spin = ball_state.spin

        # Calculate forces
        # 1. Gravity (vertical only)
        F_gravity = np.array([0.0, 0.0, -self.mass * self.g])

        # 2. Drag force: F_d = -0.5 � � � Cd � A � |v| � v
        speed = np.linalg.norm(vel)
        if speed > 0.01:
            F_drag = -0.5 * self.rho * self.Cd * self.area * speed * vel
        else:
            F_drag = np.zeros(3)

        # 3. Magnus force (simplified 2D)
        # In 2D, spin causes force perpendicular to velocity in x-y plane
        if speed > 0.01 and abs(spin) > 0.1:
            # Get horizontal velocity direction
            vel_horiz = vel[:2]
            speed_horiz = np.linalg.norm(vel_horiz)

            if speed_horiz > 0.01:
                # Perpendicular direction in x-y plane (rotated 90�)
                perp_dir = np.array([-vel_horiz[1], vel_horiz[0]]) / speed_horiz

                # Magnus force magnitude (simplified)
                magnus_magnitude = 0.5 * self.rho * self.Cl * self.area * abs(spin) * speed_horiz

                # Direction depends on spin sign
                magnus_dir = perp_dir * np.sign(spin)

                # Full 3D Magnus force (horizontal only for simplicity)
                F_magnus = np.array([magnus_dir[0], magnus_dir[1], 0.0]) * magnus_magnitude
            else:
                F_magnus = np.zeros(3)
        else:
            F_magnus = np.zeros(3)

        # Total force
        F_total = F_gravity + F_drag + F_magnus

        # Acceleration: a = F/m
        accel = F_total / self.mass

        # Velocity Verlet integration
        new_position = pos + vel * dt + 0.5 * accel * dt**2
        new_velocity = vel + accel * dt

        # Ground collision detection
        if new_position[2] <= GROUND_LEVEL and new_velocity[2] < 0:
            # Ball hit ground - bounce
            new_position[2] = GROUND_LEVEL

            # Vertical velocity reverses with energy loss
            new_velocity[2] = -new_velocity[2] * BALL_BOUNCE_COEF

            # Horizontal velocity reduced by friction
            new_velocity[0] *= BALL_FRICTION_COEF
            new_velocity[1] *= BALL_FRICTION_COEF

            # Spin decay on bounce
            new_spin = spin * BALL_SPIN_DECAY_GROUND

        else:
            # In air - spin decay slowly
            new_spin = spin * BALL_SPIN_DECAY

        # Rolling resistance (if ball is on ground and moving slowly)
        if new_position[2] < BALL_GROUND_THRESHOLD:
            horiz_speed = np.linalg.norm(new_velocity[:2])
            if horiz_speed > 0.01:
                # Apply rolling resistance
                resistance = ROLLING_RESISTANCE * dt
                new_velocity[:2] *= max(0, 1 - resistance)
            else:
                # Ball stopped
                new_velocity[:2] = 0

        # Field boundary checks (ball goes out of play)
        # Note: We don't bounce off boundaries - ball just goes out
        # This will be handled by match logic (throw-ins, corners, etc.)

        return BallState(
            position=new_position,
            velocity=new_velocity,
            spin=new_spin
        )

    def simulate_trajectory(
        self,
        initial_state: BallState,
        max_time: float = 5.0,
        dt: Optional[float] = None
    ) -> Tuple[BallState, List[Dict]]:
        """
        Simulate complete ball trajectory

        Args:
            initial_state: Starting ball state
            max_time: Maximum time to simulate (seconds)
            dt: Time step (default: self.dt)

        Returns:
            (final_state, trajectory_list)
        """
        if dt is None:
            dt = self.dt

        ball_state = initial_state
        trajectory = [ball_state.to_dict()]

        t = 0
        while t < max_time:
            ball_state = self.update_ball_state(ball_state, dt)
            trajectory.append(ball_state.to_dict())

            # Stop if ball has stopped moving
            if (np.linalg.norm(ball_state.velocity) < 0.1 and
                ball_state.position[2] <= BALL_GROUND_THRESHOLD):
                break

            t += dt

        return ball_state, trajectory

    def will_score(
        self,
        initial_state: BallState,
        attacking_left: bool = True,
        max_time: float = 5.0
    ) -> Tuple[bool, float, Optional[np.ndarray]]:
        """
        Determine if shot will score

        Args:
            initial_state: Ball state (typically after shot)
            attacking_left: True if attacking left goal (x=-52.5), False if right (x=+52.5)
            max_time: Maximum time to simulate (seconds)

        Returns:
            (is_goal, time_to_goal, goal_position)
        """
        ball_state = initial_state
        dt = 0.01  # Fine time step for accuracy
        t = 0

        while t < max_time:
            ball_state = self.update_ball_state(ball_state, dt)

            # Check if ball is in goal
            x, y, h = ball_state.position

            if is_in_goal(x, y, h, attacking_left):
                return True, t, ball_state.position.copy()

            # Stop if ball stopped moving or went out of bounds
            if np.linalg.norm(ball_state.velocity) < 0.1:
                break

            if h < 0:  # Ball went through ground (shouldn't happen but safety check)
                break

            t += dt

        return False, 0.0, None

    def calculate_shot_parameters(
        self,
        start_position: np.ndarray,
        target_position: np.ndarray,
        shot_power: float,
        elevation_angle: float = 0.0,
        spin: float = 0.0
    ) -> BallState:
        """
        Calculate initial ball state for a shot

        Args:
            start_position: Starting position [x, y, h]
            target_position: Target position [x, y, h]
            shot_power: Shot power (m/s) - initial speed
            elevation_angle: Vertical angle (radians) - 0 = horizontal, �/4 = 45� up
            spin: Spin rate (rad/s) - positive = clockwise

        Returns:
            Initial BallState for shot
        """
        # Calculate direction to target (horizontal)
        direction_horiz = target_position[:2] - start_position[:2]
        distance_horiz = np.linalg.norm(direction_horiz)

        if distance_horiz > 0:
            direction_norm = direction_horiz / distance_horiz
        else:
            direction_norm = np.array([1.0, 0.0])  # Default forward

        # Calculate initial velocity
        vx = direction_norm[0] * shot_power * np.cos(elevation_angle)
        vy = direction_norm[1] * shot_power * np.cos(elevation_angle)
        vh = shot_power * np.sin(elevation_angle)

        return BallState(
            position=start_position.copy(),
            velocity=np.array([vx, vy, vh]),
            spin=spin
        )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_ball_at_position(x: float, y: float, h: float = BALL_RADIUS) -> BallState:
    """
    Create ball at rest at given position

    Args:
        x, y: Horizontal position (meters)
        h: Height (default: ball radius, i.e., resting on ground)

    Returns:
        BallState at rest
    """
    return BallState(
        position=np.array([x, y, h]),
        velocity=np.zeros(3),
        spin=0.0
    )


def create_pass(
    start_position: np.ndarray,
    target_position: np.ndarray,
    pass_power: float
) -> BallState:
    """
    Create ball state for a pass

    Args:
        start_position: Starting position [x, y, h]
        target_position: Target position [x, y, h]
        pass_power: Pass power (m/s)

    Returns:
        Initial BallState for pass
    """
    engine = BallPhysicsEngine()
    return engine.calculate_shot_parameters(
        start_position,
        target_position,
        pass_power,
        elevation_angle=0.0,  # Ground pass
        spin=0.0
    )


def create_shot(
    start_position: np.ndarray,
    target_position: np.ndarray,
    shot_power: float,
    elevation: float = 0.1,  # Slight upward angle
    spin: float = 0.0
) -> BallState:
    """
    Create ball state for a shot

    Args:
        start_position: Starting position [x, y, h]
        target_position: Target position [x, y, h]
        shot_power: Shot power (m/s)
        elevation: Vertical angle (radians)
        spin: Spin rate (rad/s)

    Returns:
        Initial BallState for shot
    """
    engine = BallPhysicsEngine()
    return engine.calculate_shot_parameters(
        start_position,
        target_position,
        shot_power,
        elevation_angle=elevation,
        spin=spin
    )


# =============================================================================
# TESTING & VALIDATION
# =============================================================================

def validate_ball_physics():
    """
    Run basic ball physics validation tests

    Checks:
    - Ball falls under gravity
    - Ball bounces correctly
    - Ball curves with spin (Magnus effect)
    - Goal detection works
    """
    print("=" * 60)
    print("Ball Physics Validation")
    print("=" * 60)

    engine = BallPhysicsEngine()

    # Test 1: Gravity (ball falls)
    print("\n[Test 1] Ball falls under gravity")
    ball_state = BallState(
        position=np.array([0.0, 0.0, 10.0]),  # 10m high
        velocity=np.zeros(3),
        spin=0.0
    )

    for i in range(15):  # 1.5 seconds
        ball_state = engine.update_ball_state(ball_state)

    print(f"  After 1.5s: height = {ball_state.position[2]:.2f}m")
    print(f"  Ball hit ground: {ball_state.position[2] <= 0.1}")

    # Test 2: Bounce
    print("\n[Test 2] Ball bounces")
    ball_state = BallState(
        position=np.array([0.0, 0.0, 2.0]),
        velocity=np.array([0.0, 0.0, -5.0]),  # Falling at 5 m/s
        spin=0.0
    )

    positions = []
    for i in range(30):  # 3 seconds
        ball_state = engine.update_ball_state(ball_state)
        positions.append(ball_state.position[2])

    bounces = sum(1 for i in range(1, len(positions)) if positions[i] > positions[i-1] and positions[i-1] < 0.2)
    print(f"  Number of bounces: {bounces}")
    print(f"  Ball bounced: {bounces > 0}")

    # Test 3: Magnus effect (curve)
    print("\n[Test 3] Ball curves with spin")
    ball_state = BallState(
        position=np.array([0.0, 0.0, 1.0]),
        velocity=np.array([20.0, 0.0, 0.0]),  # 20 m/s forward
        spin=100.0  # 100 rad/s clockwise
    )

    initial_y = ball_state.position[1]

    for i in range(10):  # 1 second
        ball_state = engine.update_ball_state(ball_state)

    y_deviation = abs(ball_state.position[1] - initial_y)
    print(f"  Y deviation after 1s: {y_deviation:.2f}m")
    print(f"  Ball curved: {y_deviation > 0.5}")

    # Test 4: Goal detection
    print("\n[Test 4] Goal detection")
    # Shot toward right goal
    ball_state = BallState(
        position=np.array([50.0, 0.0, 1.0]),
        velocity=np.array([10.0, 0.0, 0.0]),  # Toward goal
        spin=0.0
    )

    is_goal, time_to_goal, goal_pos = engine.will_score(ball_state, attacking_left=False)
    print(f"  Shot is goal: {is_goal}")
    if is_goal:
        print(f"  Time to goal: {time_to_goal:.2f}s")
        print(f"  Goal position: {goal_pos}")

    print("\n" + "=" * 60)
    print("Validation Complete ")
    print("=" * 60)


if __name__ == "__main__":
    validate_ball_physics()
