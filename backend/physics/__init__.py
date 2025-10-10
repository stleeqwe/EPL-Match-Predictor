"""
Physics Engine Module
2D Football Simulation with Newton's Laws

Modules:
- constants: Physical constants and field dimensions
- player_physics: 2D player movement engine
- ball_physics: 2D ball trajectory with Magnus effect
- field: Field boundaries and zones
"""

from .constants import (
    # Time
    DT, TICKS_PER_SECOND, MATCH_DURATION_SECONDS, TOTAL_TICKS,

    # Field dimensions
    FIELD_LENGTH, FIELD_WIDTH,
    FIELD_X_MIN, FIELD_X_MAX, FIELD_Y_MIN, FIELD_Y_MAX,
    GOAL_WIDTH, GOAL_HEIGHT,

    # Player physics
    PLAYER_BASE_MAX_SPEED, PLAYER_BASE_MAX_ACCEL,
    PLAYER_CONTROL_RADIUS, SHOT_POWER_BASE,

    # Ball physics
    BALL_MASS, BALL_RADIUS, GRAVITY,

    # Helper functions
    rating_to_speed, rating_to_accel, stamina_factor,
    is_in_field, is_in_goal, distance_2d
)

from .player_physics import (
    PlayerState,
    PlayerPhysicsEngine,
    create_initial_state,
    calculate_target_velocity
)

from .ball_physics import (
    BallState,
    BallPhysicsEngine,
    create_ball_at_position,
    create_pass,
    create_shot
)

__all__ = [
    # Constants
    'DT', 'TICKS_PER_SECOND', 'TOTAL_TICKS',
    'FIELD_LENGTH', 'FIELD_WIDTH',
    'GOAL_WIDTH', 'GOAL_HEIGHT',

    # Player physics
    'PlayerState',
    'PlayerPhysicsEngine',
    'create_initial_state',
    'calculate_target_velocity',

    # Ball physics
    'BallState',
    'BallPhysicsEngine',
    'create_ball_at_position',
    'create_pass',
    'create_shot',

    # Helper functions
    'rating_to_speed',
    'rating_to_accel',
    'stamina_factor',
    'is_in_field',
    'is_in_goal',
    'distance_2d'
]

__version__ = '1.0.0-mvp'
