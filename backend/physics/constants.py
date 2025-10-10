# -*- coding: utf-8 -*-
"""
Physics Constants
All physical constants for 2D football simulation
"""

import numpy as np

# =============================================================================
# TIME & SIMULATION
# =============================================================================
DT = 0.1  # Time step in seconds (10 updates per second)
TICKS_PER_SECOND = int(1.0 / DT)  # 10 ticks/second
MATCH_DURATION_SECONDS = 90 * 60  # 5400 seconds (90 minutes)
TOTAL_TICKS = MATCH_DURATION_SECONDS * TICKS_PER_SECOND  # 54000 ticks

# =============================================================================
# FIELD DIMENSIONS (FIFA Standard)
# =============================================================================
FIELD_LENGTH = 105.0  # meters (x-axis)
FIELD_WIDTH = 68.0  # meters (y-axis)

# Field boundaries (origin at center)
FIELD_X_MIN = -FIELD_LENGTH / 2  # -52.5m
FIELD_X_MAX = FIELD_LENGTH / 2  # 52.5m
FIELD_Y_MIN = -FIELD_WIDTH / 2  # -34m
FIELD_Y_MAX = FIELD_WIDTH / 2  # 34m

# Goal dimensions
GOAL_WIDTH = 7.32  # meters (FIFA standard)
GOAL_HEIGHT = 2.44  # meters
GOAL_Y_MIN = -GOAL_WIDTH / 2  # -3.66m
GOAL_Y_MAX = GOAL_WIDTH / 2  # 3.66m

# Penalty area
PENALTY_AREA_LENGTH = 16.5  # meters from goal line
PENALTY_AREA_WIDTH = 40.3  # meters

# Goal areas
GOAL_AREA_LENGTH = 5.5  # meters from goal line
GOAL_AREA_WIDTH = 18.3  # meters

# Center circle
CENTER_CIRCLE_RADIUS = 9.15  # meters

# =============================================================================
# PLAYER PHYSICS
# =============================================================================

# Speed and acceleration (base values for rating=70)
PLAYER_BASE_MAX_SPEED = 7.0  # m/s (70 pace = 7.0 m/s = 25.2 km/h)
PLAYER_BASE_MAX_ACCEL = 7.0  # m/s� (70 acceleration = 7.0 m/s�)

# Conversion factors (rating to physics)
PACE_TO_SPEED_FACTOR = 0.1  # pace 70 � 7.0 m/s
ACCEL_TO_ACCEL_FACTOR = 0.1  # acceleration 70 � 7.0 m/s�

# Drag (air resistance and friction)
PLAYER_DRAG_COEFFICIENT = 0.3  # Dimensionless

# Stamina
STAMINA_DRAIN_RATE = 0.01  # Stamina lost per meter per second
STAMINA_RECOVERY_RATE = 0.05  # Stamina recovered per second when idle
MIN_STAMINA = 0.0
MAX_STAMINA = 100.0

# Fatigue effects
FATIGUE_SPEED_PENALTY = 0.5  # At 0 stamina, max speed = 50% of normal
FATIGUE_ACCEL_PENALTY = 0.5  # At 0 stamina, max accel = 50% of normal

# =============================================================================
# BALL PHYSICS
# =============================================================================

# Ball properties (FIFA standard)
BALL_MASS = 0.43  # kg
BALL_RADIUS = 0.11  # meters (11 cm)
BALL_CIRCUMFERENCE = 2 * np.pi * BALL_RADIUS  # ~0.69 m

# Air properties (sea level, 20�C)
AIR_DENSITY = 1.225  # kg/m�
AIR_VISCOSITY = 1.81e-5  # Pa�s

# Drag force: F_d = 0.5 * � * Cd * A * v�
BALL_DRAG_COEFFICIENT = 0.25  # Dimensionless (typical for football)
BALL_CROSS_SECTIONAL_AREA = np.pi * BALL_RADIUS**2  # m�

# Magnus effect (spin)
BALL_MAGNUS_COEFFICIENT = 0.25  # Lift coefficient for spinning ball
BALL_SPIN_DECAY = 0.99  # Spin decay per time step (in air)
BALL_SPIN_DECAY_GROUND = 0.7  # Spin decay on bounce

# Gravity
GRAVITY = 9.81  # m/s� (downward)

# Bounce (coefficient of restitution) - IMPROVED: Less bouncy for better control
BALL_BOUNCE_COEF = 0.4  # Energy retained after bounce (40%) - Was 0.6
BALL_FRICTION_COEF = 0.6  # Horizontal velocity retained after bounce (60%) - Was 0.8

# Ground detection
GROUND_LEVEL = 0.0  # z = 0 is ground level
BALL_GROUND_THRESHOLD = 0.01  # Ball considered on ground if h < 1cm

# Rolling resistance (when ball is on ground) - IMPROVED: More friction for control
ROLLING_RESISTANCE = 0.15  # Deceleration due to grass friction - Was 0.05

# =============================================================================
# PLAYER-BALL INTERACTION
# =============================================================================

# Ball control (TUNING: Adjusted for balanced possession)
PLAYER_CONTROL_RADIUS = 1.5  # meters (can control ball within 1.5m) - Was 2.0, originally 1.0
PLAYER_TACKLE_RADIUS = 3.0  # meters (can tackle within 3.0m) - Was 2.5, enables opponent pressing
PLAYER_PASS_RADIUS = 1.0  # meters (must be closer to pass accurately) - Was 0.5

# Shot power (based on shooting attribute)
SHOT_POWER_BASE = 20.0  # m/s (base shot speed)
SHOT_POWER_FACTOR = 0.3  # Additional speed per shooting point
# shooting=80 � 20 + 80*0.3 = 44 m/s = 158 km/h

# Pass power
PASS_POWER_SHORT = 8.0  # m/s (short pass)
PASS_POWER_MEDIUM = 15.0  # m/s (medium pass)
PASS_POWER_LONG = 25.0  # m/s (long pass)

# Accuracy (angular deviation in radians)
PASS_ACCURACY_ERROR = 0.1  # �5.7 degrees for perfect passer (90 rating)
SHOT_ACCURACY_ERROR = 0.15  # �8.6 degrees for perfect shooter (90 rating)

# =============================================================================
# AGENT DECISION-MAKING
# =============================================================================

# Vision & awareness
PLAYER_VISION_RANGE = 30.0  # meters (can see players/ball within 30m)
PLAYER_VISION_ANGLE = np.pi / 2  # 90 degrees (can see in front)

# Decision-making
ACTION_DECISION_INTERVAL = 0.5  # seconds (make decision every 0.5s)
TICKS_PER_DECISION = int(ACTION_DECISION_INTERVAL / DT)  # 5 ticks

# Distance thresholds - IMPROVED: Extended shooting range
SHOOTING_RANGE_MAX = 40.0  # meters (won't shoot from > 40m) - Was 30.0
SHOOTING_RANGE_OPTIMAL = 20.0  # meters (prefers to shoot from < 20m) - Was 15.0
PASSING_RANGE_SHORT = 15.0  # meters
PASSING_RANGE_MEDIUM = 30.0  # meters
PASSING_RANGE_LONG = 50.0  # meters

# =============================================================================
# POSITIONS & FORMATIONS
# =============================================================================

# Formation zones (x-coordinate ranges)
DEFENSIVE_THIRD_X_MIN = -FIELD_X_MAX  # -52.5m
DEFENSIVE_THIRD_X_MAX = -FIELD_X_MAX / 3  # -17.5m

MIDDLE_THIRD_X_MIN = -FIELD_X_MAX / 3  # -17.5m
MIDDLE_THIRD_X_MAX = FIELD_X_MAX / 3  # 17.5m

ATTACKING_THIRD_X_MIN = FIELD_X_MAX / 3  # 17.5m
ATTACKING_THIRD_X_MAX = FIELD_X_MAX  # 52.5m

# Position roles (for agent behavior)
POSITION_ROLES = {
    'GK': 'goalkeeper',
    'CB': 'defender',
    'FB': 'defender',
    'DM': 'midfielder',
    'CM': 'midfielder',
    'CAM': 'midfielder',
    'WG': 'forward',
    'ST': 'forward'
}

# =============================================================================
# MATCH EVENTS
# =============================================================================

# Event types
EVENT_KICK_OFF = 'kick_off'
EVENT_GOAL = 'goal'
EVENT_SHOT = 'shot'
EVENT_SHOT_ON_TARGET = 'shot_on_target'
EVENT_SHOT_OFF_TARGET = 'shot_off_target'
EVENT_SAVE = 'save'
EVENT_PASS = 'pass'
EVENT_PASS_COMPLETED = 'pass_completed'
EVENT_PASS_FAILED = 'pass_failed'
EVENT_TACKLE = 'tackle'
EVENT_TACKLE_WON = 'tackle_won'
EVENT_TACKLE_LOST = 'tackle_lost'
EVENT_INTERCEPTION = 'interception'
EVENT_CLEARANCE = 'clearance'
EVENT_CORNER = 'corner'
EVENT_THROW_IN = 'throw_in'
EVENT_GOAL_KICK = 'goal_kick'
EVENT_FOUL = 'foul'
EVENT_OFFSIDE = 'offside'

# =============================================================================
# PHYSICS VALIDATION THRESHOLDS
# =============================================================================

# Realistic ranges for EPL (for testing)
REALISTIC_GOALS_PER_MATCH_MIN = 0
REALISTIC_GOALS_PER_MATCH_MAX = 8
REALISTIC_GOALS_PER_TEAM_AVG = 1.4  # EPL average ~2.8 total

REALISTIC_SHOTS_PER_TEAM_MIN = 5
REALISTIC_SHOTS_PER_TEAM_MAX = 25
REALISTIC_SHOTS_PER_TEAM_AVG = 13

REALISTIC_POSSESSION_MIN = 0.30  # 30%
REALISTIC_POSSESSION_MAX = 0.70  # 70%

REALISTIC_PASS_ACCURACY_MIN = 0.65  # 65%
REALISTIC_PASS_ACCURACY_MAX = 0.92  # 92%

# Player speed limits (for validation)
REALISTIC_PLAYER_SPEED_MAX = 11.0  # m/s (39.6 km/h - Usain Bolt territory)
REALISTIC_PLAYER_SPEED_AVG = 4.0  # m/s (14.4 km/h - average during match)

# Ball speed limits
REALISTIC_BALL_SPEED_MAX = 60.0  # m/s (216 km/h - world record shot)
REALISTIC_BALL_SPEED_AVG_PASS = 12.0  # m/s (43.2 km/h - average pass)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def rating_to_speed(pace_rating: float) -> float:
    """Convert pace rating (0-100) to max speed (m/s)"""
    return pace_rating * PACE_TO_SPEED_FACTOR


def rating_to_accel(accel_rating: float) -> float:
    """Convert acceleration rating (0-100) to max acceleration (m/s�)"""
    return accel_rating * ACCEL_TO_ACCEL_FACTOR


def stamina_factor(stamina: float) -> float:
    """
    Calculate stamina factor (0-1) for speed/acceleration penalties

    Args:
        stamina: Current stamina (0-100)

    Returns:
        Factor between 0.5 and 1.0
        (0 stamina = 0.5, 100 stamina = 1.0)
    """
    normalized = max(0.0, min(100.0, stamina)) / 100.0
    return FATIGUE_SPEED_PENALTY + (1.0 - FATIGUE_SPEED_PENALTY) * normalized


def is_in_field(x: float, y: float) -> bool:
    """Check if position is within field boundaries"""
    return (FIELD_X_MIN <= x <= FIELD_X_MAX and
            FIELD_Y_MIN <= y <= FIELD_Y_MAX)


def is_in_goal(x: float, y: float, h: float, attacking_left: bool = True) -> bool:
    """
    Check if ball position is in goal

    Args:
        x, y, h: Ball position (meters)
        attacking_left: True if attacking left goal (x=-52.5), False if right (x=+52.5)

    Returns:
        True if ball is in goal
    """
    goal_x = FIELD_X_MIN if attacking_left else FIELD_X_MAX

    # Check if ball crossed goal line
    crossed_line = (x <= goal_x if attacking_left else x >= goal_x)

    # Check if within goal dimensions
    within_width = (GOAL_Y_MIN <= y <= GOAL_Y_MAX)
    within_height = (0 <= h <= GOAL_HEIGHT)

    return crossed_line and within_width and within_height


def distance_2d(x1: float, y1: float, x2: float, y2: float) -> float:
    """Calculate 2D Euclidean distance"""
    return np.sqrt((x2 - x1)**2 + (y2 - y1)**2)


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max"""
    return max(min_val, min(max_val, value))

# =============================================================================
# DEBUGGING & LOGGING
# =============================================================================

DEBUG_MODE = False  # Enable verbose physics logging
LOG_PHYSICS_EVERY_N_TICKS = 100  # Log every N ticks (for debugging)

# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    # Time
    'DT', 'TICKS_PER_SECOND', 'MATCH_DURATION_SECONDS', 'TOTAL_TICKS',

    # Field
    'FIELD_LENGTH', 'FIELD_WIDTH',
    'FIELD_X_MIN', 'FIELD_X_MAX', 'FIELD_Y_MIN', 'FIELD_Y_MAX',
    'GOAL_WIDTH', 'GOAL_HEIGHT',

    # Player
    'PLAYER_BASE_MAX_SPEED', 'PLAYER_BASE_MAX_ACCEL',
    'PLAYER_DRAG_COEFFICIENT',
    'STAMINA_DRAIN_RATE', 'STAMINA_RECOVERY_RATE',

    # Ball
    'BALL_MASS', 'BALL_RADIUS',
    'BALL_DRAG_COEFFICIENT', 'BALL_MAGNUS_COEFFICIENT',
    'GRAVITY', 'BALL_BOUNCE_COEF',

    # Interaction
    'PLAYER_CONTROL_RADIUS', 'SHOT_POWER_BASE',

    # Helper functions
    'rating_to_speed', 'rating_to_accel', 'stamina_factor',
    'is_in_field', 'is_in_goal', 'distance_2d', 'clamp'
]
