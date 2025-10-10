"""
Pytest Configuration and Shared Fixtures
Common test fixtures for physics engine testing
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from physics.player_physics import PlayerState, PlayerPhysicsEngine, create_initial_state
from physics.ball_physics import BallState, BallPhysicsEngine, create_ball_at_position
from physics.constants import FIELD_X_MIN, FIELD_X_MAX, FIELD_Y_MIN, FIELD_Y_MAX


# =============================================================================
# PLAYER FIXTURES
# =============================================================================

@pytest.fixture
def player_engine():
    """Standard player physics engine"""
    return PlayerPhysicsEngine()


@pytest.fixture
def player_at_rest():
    """Player at rest at field center"""
    return create_initial_state("test_player", position=(0, 0), stamina=100)


@pytest.fixture
def player_moving():
    """Player moving forward at 5 m/s"""
    player = create_initial_state("test_player", position=(0, 0), stamina=100)
    player.velocity = np.array([5.0, 0.0])
    return player


@pytest.fixture
def fast_player_attrs():
    """Fast player attributes (pace=90, accel=88)"""
    return {
        'pace': 90,
        'acceleration': 88,
        'stamina': 85,
        'strength': 80,
        'agility': 82
    }


@pytest.fixture
def slow_player_attrs():
    """Slow player attributes (pace=60, accel=60)"""
    return {
        'pace': 60,
        'acceleration': 60,
        'stamina': 70,
        'strength': 75,
        'agility': 65
    }


@pytest.fixture
def average_player_attrs():
    """Average player attributes (all 70)"""
    return {
        'pace': 70,
        'acceleration': 70,
        'stamina': 70,
        'strength': 70,
        'agility': 70
    }


@pytest.fixture
def tired_player():
    """Player with low stamina (20)"""
    player = create_initial_state("tired_player", position=(0, 0), stamina=20)
    return player


# =============================================================================
# BALL FIXTURES
# =============================================================================

@pytest.fixture
def ball_engine():
    """Standard ball physics engine"""
    return BallPhysicsEngine()


@pytest.fixture
def ball_at_center():
    """Ball at rest at field center"""
    return create_ball_at_position(0, 0, 0.11)  # Ball radius height


@pytest.fixture
def ball_in_air():
    """Ball in air at 10m height"""
    return BallState(
        position=np.array([0.0, 0.0, 10.0]),
        velocity=np.zeros(3),
        spin=0.0
    )


@pytest.fixture
def ball_moving_forward():
    """Ball moving forward at 10 m/s"""
    ball = create_ball_at_position(0, 0, 0.5)
    ball.velocity = np.array([10.0, 0.0, 0.0])
    return ball


@pytest.fixture
def ball_with_spin():
    """Ball with spin"""
    ball = create_ball_at_position(0, 0, 1.0)
    ball.velocity = np.array([20.0, 0.0, 0.0])
    ball.spin = 100.0
    return ball


# =============================================================================
# SCENARIO FIXTURES
# =============================================================================

@pytest.fixture
def striker_near_goal():
    """Striker positioned 15m from goal"""
    return create_initial_state("striker", position=(37.5, 0), stamina=100)


@pytest.fixture
def goalkeeper_at_goal():
    """Goalkeeper at goal line"""
    return create_initial_state("goalkeeper", position=(FIELD_X_MIN + 5, 0), stamina=100)


@pytest.fixture
def midfielder_at_center():
    """Midfielder at field center"""
    return create_initial_state("midfielder", position=(0, 0), stamina=100)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

@pytest.fixture
def assert_near():
    """Helper to assert values are nearly equal"""
    def _assert_near(actual, expected, tolerance=0.1):
        """
        Assert two values are within tolerance

        Args:
            actual: Actual value
            expected: Expected value
            tolerance: Absolute tolerance (default 0.1)
        """
        if isinstance(actual, np.ndarray):
            assert np.allclose(actual, expected, atol=tolerance), \
                f"Expected {expected}, got {actual}"
        else:
            assert abs(actual - expected) < tolerance, \
                f"Expected {expected}, got {actual} (diff: {abs(actual - expected)})"

    return _assert_near


@pytest.fixture
def assert_in_range():
    """Helper to assert value is in range"""
    def _assert_in_range(value, min_val, max_val):
        """Assert value is within range [min_val, max_val]"""
        assert min_val <= value <= max_val, \
            f"Value {value} not in range [{min_val}, {max_val}]"

    return _assert_in_range


@pytest.fixture
def run_simulation():
    """Helper to run physics simulation for N ticks"""
    def _run_simulation(engine, initial_state, attributes, target_velocity, ticks):
        """
        Run simulation for N ticks

        Args:
            engine: Physics engine
            initial_state: Initial state
            attributes: Player/ball attributes
            target_velocity: Target velocity
            ticks: Number of ticks to simulate

        Returns:
            Final state
        """
        state = initial_state
        for _ in range(ticks):
            if hasattr(engine, 'update_player_state'):
                state = engine.update_player_state(state, attributes, target_velocity)
            else:
                state = engine.update_ball_state(state)
        return state

    return _run_simulation


# =============================================================================
# PERFORMANCE FIXTURES
# =============================================================================

@pytest.fixture
def benchmark_player_update(player_engine, player_at_rest, average_player_attrs):
    """Benchmark fixture for player update performance"""
    def _benchmark():
        target_vel = np.array([7.0, 0.0])
        return player_engine.update_player_state(
            player_at_rest,
            average_player_attrs,
            target_vel
        )
    return _benchmark


@pytest.fixture
def benchmark_ball_update(ball_engine, ball_in_air):
    """Benchmark fixture for ball update performance"""
    def _benchmark():
        return ball_engine.update_ball_state(ball_in_air)
    return _benchmark


# =============================================================================
# VALIDATION FIXTURES
# =============================================================================

@pytest.fixture
def epl_validation_ranges():
    """EPL realistic validation ranges"""
    return {
        'player_speed_min': 0.0,
        'player_speed_max': 11.0,  # 39.6 km/h (Usain Bolt territory)
        'player_speed_avg': 4.0,  # 14.4 km/h average during match
        'player_speed_sprint': 8.0,  # 28.8 km/h sprint

        'ball_speed_pass_min': 5.0,
        'ball_speed_pass_max': 20.0,
        'ball_speed_shot_min': 15.0,
        'ball_speed_shot_max': 60.0,  # 216 km/h world record

        'stamina_drain_per_minute': 1.0,  # ~1% per minute at average speed
        'stamina_recovery_per_minute': 3.0,  # ~3% per minute when idle

        'shot_accuracy_10m': 0.90,  # 90% on target from 10m
        'shot_accuracy_20m': 0.50,  # 50% on target from 20m
        'shot_accuracy_30m': 0.20,  # 20% on target from 30m
    }


@pytest.fixture
def field_bounds():
    """Field boundary coordinates"""
    return {
        'x_min': FIELD_X_MIN,
        'x_max': FIELD_X_MAX,
        'y_min': FIELD_Y_MIN,
        'y_max': FIELD_Y_MAX
    }
