"""
EPL Match Predictor - Application Constants
Immutable constants used throughout the application
"""

# Application Metadata
APP_NAME = "EPL Match Predictor"
APP_VERSION = "2.0.0"
APP_DESCRIPTION = "AI-powered Premier League match prediction platform"

# API Version
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# Player Positions
GENERAL_POSITIONS = ['GK', 'DF', 'MF', 'FW']
DETAILED_POSITIONS = {
    'GK': ['GK'],
    'DF': ['CB', 'FB'],
    'MF': ['DM', 'CM', 'CAM'],
    'FW': ['WG', 'ST']
}

# Rating System
RATING_MIN = 0.0
RATING_MAX = 5.0
RATING_STEP = 0.25

# Position Attributes
POSITION_ATTRIBUTES = {
    'GK': [
        'reflexes', 'positioning', 'handling', 'one_on_one',
        'aerial_control', 'buildup', 'leadership_communication', 'long_kick'
    ],
    'CB': [
        'positioning_reading', 'composure_judgement', 'interception',
        'aerial_duel', 'tackle_marking', 'speed', 'passing',
        'physical_jumping', 'buildup_contribution', 'leadership'
    ],
    'FB': [
        'stamina', 'speed', 'defensive_positioning', 'one_on_one_tackle',
        'overlapping', 'crossing_accuracy', 'covering', 'agility',
        'press_resistance', 'long_shot'
    ],
    'DM': [
        'positioning', 'ball_winning', 'pass_accuracy',
        'composure_press_resistance', 'backline_protection',
        'pressing_transition_blocking', 'progressive_play',
        'tempo_control', 'stamina', 'physicality_mobility', 'leadership'
    ],
    'CM': [
        'stamina', 'ball_possession_circulation', 'pass_accuracy_vision',
        'transition', 'dribbling_press_resistance', 'space_creation',
        'defensive_contribution', 'ball_retention', 'long_shot',
        'agility_acceleration', 'physicality'
    ],
    'CAM': [
        'creativity', 'vision_killpass', 'dribbling', 'decision_making',
        'penetration', 'shooting_finishing', 'one_touch_pass',
        'pass_and_move', 'acceleration', 'agility', 'set_piece'
    ],
    'WG': [
        'speed_dribbling', 'one_on_one_beating', 'speed', 'acceleration',
        'crossing_accuracy', 'shooting_accuracy', 'agility_direction_change',
        'cutting_in', 'creativity', 'defensive_contribution',
        'cutback_pass', 'link_up_play'
    ],
    'ST': [
        'finishing', 'shot_power', 'composure', 'off_ball_movement',
        'hold_up_play', 'heading', 'acceleration', 'physicality_balance',
        'jumping'
    ]
}

# Formations
SUPPORTED_FORMATIONS = [
    '4-3-3', '4-4-2', '4-2-3-1', '3-5-2', '3-4-3', '5-3-2', '4-5-1'
]

# EPL Teams (2024-25 Season)
EPL_TEAMS = [
    'Arsenal', 'Aston Villa', 'Bournemouth', 'Brentford', 'Brighton',
    'Chelsea', 'Crystal Palace', 'Everton', 'Fulham', 'Ipswich Town',
    'Leicester', 'Liverpool', 'Man City', 'Man Utd', 'Newcastle',
    'Nott\'m Forest', 'Southampton', 'Spurs', 'West Ham', 'Wolves'
]

# Simulation Settings
SIMULATION_DEFAULT_ITERATIONS = 1000
SIMULATION_MAX_ITERATIONS = 10000
SIMULATION_TIMEOUT_SECONDS = 120

# Cache Keys Prefixes
CACHE_KEY_PLAYER = "player"
CACHE_KEY_TEAM = "team"
CACHE_KEY_RATING = "rating"
CACHE_KEY_LINEUP = "lineup"
CACHE_KEY_FORMATION = "formation"
CACHE_KEY_TACTICS = "tactics"
CACHE_KEY_PREDICTION = "prediction"
CACHE_KEY_FPL = "fpl"
CACHE_KEY_ODDS = "odds"

# HTTP Status Codes
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204
HTTP_400_BAD_REQUEST = 400
HTTP_401_UNAUTHORIZED = 401
HTTP_403_FORBIDDEN = 403
HTTP_404_NOT_FOUND = 404
HTTP_422_UNPROCESSABLE_ENTITY = 422
HTTP_500_INTERNAL_SERVER_ERROR = 500

# Error Messages
ERROR_PLAYER_NOT_FOUND = "Player not found"
ERROR_TEAM_NOT_FOUND = "Team not found"
ERROR_INVALID_RATING = "Invalid rating value"
ERROR_INVALID_FORMATION = "Invalid formation"
ERROR_DATABASE_ERROR = "Database error occurred"
ERROR_EXTERNAL_API_ERROR = "External API error"
ERROR_AI_SERVICE_ERROR = "AI service error"

# File Paths (relative to backend/)
DATA_DIR = "data"
LINEUPS_DIR = f"{DATA_DIR}/lineups"
FORMATIONS_DIR = f"{DATA_DIR}/formations"
TACTICS_DIR = f"{DATA_DIR}/tactics"
TEAM_STRENGTH_DIR = f"{DATA_DIR}/team_strength"
OVERALL_SCORES_DIR = f"{DATA_DIR}/overall_scores"
INJURIES_DIR = f"{DATA_DIR}/injuries"

# AI Model Settings
AI_TEMPERATURE = 0.7
AI_MAX_TOKENS = 4096
AI_TOP_P = 0.9

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
