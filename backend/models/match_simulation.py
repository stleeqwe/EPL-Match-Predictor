"""
Match Simulation ORM Models
SQLAlchemy models for match simulation results and physics states
"""

from sqlalchemy import Column, Integer, String, DECIMAL, Boolean, DateTime, ForeignKey, BigInteger, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import uuid
import hashlib
import json
from typing import Dict, List, Optional

from backend.database.connection import Base


class MatchSimulation(Base):
    """
    Match simulation result with full event tracking

    Stores complete physics simulation results including:
    - Final score and probabilities
    - Expected goals (xG)
    - Match events (goals, shots, passes, tackles)
    - Statistics (possession, shots, etc.)
    - Performance metrics (simulation time, physics ticks)
    - AI costs (tokens, USD)
    """

    __tablename__ = 'match_simulations'

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    match_id = Column(String(100), ForeignKey('matches.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))

    # Simulation metadata
    simulation_type = Column(String(20))  # 'basic', 'physics', 'full'
    tier = Column(String(20), nullable=False)  # 'BASIC', 'PRO'

    # Input data hash (for caching)
    input_hash = Column(String(64), nullable=False)

    # Simulation parameters
    parameters = Column(JSONB, nullable=False)  # weights, tactics, formations

    # Results
    final_score = Column(JSONB, nullable=False)  # {"home": 2, "away": 1}
    probabilities = Column(JSONB, nullable=False)  # {"home_win": 0.45, "draw": 0.30, "away_win": 0.25}
    expected_goals = Column(JSONB)  # {"home": 1.8, "away": 1.2}

    # Analysis
    analysis = Column(JSONB)  # key_factors, tactical_insight, etc.

    # Events (goals, shots, passes, tackles)
    match_events = Column(JSONB)  # Array of event objects

    # Statistics
    statistics = Column(JSONB)  # possession, shots, passes, etc.

    # Performance metrics
    simulation_duration_ms = Column(Integer)  # How long simulation took
    physics_ticks = Column(Integer)  # Number of physics update cycles (5400 for 90 min)

    # AI metrics
    tokens_used = Column(Integer)
    cost_usd = Column(DECIMAL(10, 6))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(hours=1))

    # Constraints
    __table_args__ = (
        CheckConstraint(
            simulation_type.in_(['basic', 'physics', 'full']),
            name='valid_simulation_type'
        ),
        CheckConstraint(
            tier.in_(['BASIC', 'PRO']),
            name='valid_tier'
        ),
    )

    # =========================================================================
    # CLASS METHODS
    # =========================================================================

    @classmethod
    def generate_input_hash(cls, match_id: str, parameters: Dict) -> str:
        """
        Generate hash of input parameters for caching

        Args:
            match_id: Match identifier
            parameters: Simulation parameters dict

        Returns:
            SHA256 hash string
        """
        input_str = f"{match_id}:{json.dumps(parameters, sort_keys=True)}"
        return hashlib.sha256(input_str.encode()).hexdigest()

    # =========================================================================
    # INSTANCE METHODS
    # =========================================================================

    def to_dict(self, include_events: bool = False, include_stats: bool = True) -> Dict:
        """Convert simulation to dictionary"""
        data = {
            'id': str(self.id),
            'match_id': self.match_id,
            'user_id': str(self.user_id) if self.user_id else None,

            # Metadata
            'simulation_type': self.simulation_type,
            'tier': self.tier,

            # Results
            'final_score': self.final_score,
            'probabilities': self.probabilities,
            'expected_goals': self.expected_goals,

            # Analysis
            'analysis': self.analysis or {},

            # Performance
            'simulation_duration_ms': self.simulation_duration_ms,
            'physics_ticks': self.physics_ticks,

            # AI metrics
            'tokens_used': self.tokens_used,
            'cost_usd': float(self.cost_usd) if self.cost_usd else None,

            # Timestamps
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

        if include_events:
            data['events'] = self.match_events or []

        if include_stats:
            data['statistics'] = self.statistics or {}

        return data

    def is_expired(self) -> bool:
        """Check if simulation cache has expired"""
        if not self.expires_at:
            return True
        return datetime.utcnow() > self.expires_at

    def get_summary(self) -> Dict:
        """Get concise summary of simulation"""
        return {
            'id': str(self.id),
            'final_score': self.final_score,
            'probabilities': self.probabilities,
            'expected_goals': self.expected_goals,
            'simulation_type': self.simulation_type,
            'duration_ms': self.simulation_duration_ms
        }

    def __repr__(self):
        score = self.final_score or {}
        return f"<MatchSimulation(id={self.id}, score={score.get('home')}-{score.get('away')})>"


class MatchPhysicsState(Base):
    """
    Frame-by-frame physics states for match playback

    WARNING: This table will be VERY large (5,400 rows per 90-minute match)
    Only use if you need frame-by-frame playback
    Consider using keyframe compression (only store significant states)
    """

    __tablename__ = 'match_physics_states'

    # Primary key
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # Foreign key
    simulation_id = Column(UUID(as_uuid=True), ForeignKey('match_simulations.id', ondelete='CASCADE'), nullable=False)

    # Time
    tick = Column(Integer, nullable=False)  # 0 to 5400 (0.1s intervals for 90 minutes)
    game_time = Column(DECIMAL(6, 2))  # Seconds (0.0 to 5400.0)

    # Ball state (2D + height)
    ball_position = Column(JSONB, nullable=False)  # {"x": 0.0, "y": 0.0, "h": 0.5}
    ball_velocity = Column(JSONB, nullable=False)  # {"vx": 5.0, "vy": 0.0, "vh": 0.0}
    ball_spin = Column(JSONB)  # {"spin": 50} (simplified 2D spin)

    # Player states (array of 22 players)
    home_players = Column(JSONB, nullable=False)  # Array of player state objects
    away_players = Column(JSONB, nullable=False)  # Array of player state objects

    # Game state
    score = Column(JSONB, nullable=False)  # {"home": 0, "away": 0}
    possession = Column(String(10))  # 'home' or 'away'

    # Event flag (if something important happened at this tick)
    event_type = Column(String(20))  # 'goal', 'shot', 'pass', 'tackle', null
    event_data = Column(JSONB)

    # Compression: Only store keyframes
    is_keyframe = Column(Boolean, default=False)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict:
        """Convert physics state to dictionary"""
        return {
            'tick': self.tick,
            'game_time': float(self.game_time) if self.game_time else None,
            'ball': {
                'position': self.ball_position,
                'velocity': self.ball_velocity,
                'spin': self.ball_spin
            },
            'players': {
                'home': self.home_players,
                'away': self.away_players
            },
            'score': self.score,
            'possession': self.possession,
            'event': {
                'type': self.event_type,
                'data': self.event_data
            } if self.event_type else None,
            'is_keyframe': self.is_keyframe
        }

    def __repr__(self):
        return f"<MatchPhysicsState(tick={self.tick}, time={self.game_time}s)>"


class PlayerMatchStats(Base):
    """
    Individual player statistics from physics simulation

    Tracks detailed player performance metrics:
    - Basic: goals, assists, shots
    - Passing: passes, accuracy, key passes
    - Defensive: tackles, interceptions, clearances
    - Physical: distance covered, sprints, speeds
    - Advanced: xG, xA, match rating
    """

    __tablename__ = 'player_match_stats'

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    simulation_id = Column(UUID(as_uuid=True), ForeignKey('match_simulations.id', ondelete='CASCADE'), nullable=False)
    player_id = Column(UUID(as_uuid=True), ForeignKey('players.id'), nullable=False)
    team_id = Column(UUID(as_uuid=True), ForeignKey('teams.id'), nullable=False)

    # Basic stats
    minutes_played = Column(Integer)
    goals = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    shots = Column(Integer, default=0)
    shots_on_target = Column(Integer, default=0)

    # Passing
    passes = Column(Integer, default=0)
    passes_completed = Column(Integer, default=0)
    pass_accuracy = Column(DECIMAL(5, 2))
    key_passes = Column(Integer, default=0)

    # Defensive
    tackles = Column(Integer, default=0)
    tackles_won = Column(Integer, default=0)
    interceptions = Column(Integer, default=0)
    clearances = Column(Integer, default=0)

    # Physical (from physics simulation)
    distance_covered_km = Column(DECIMAL(5, 2))  # Total distance in km
    sprints = Column(Integer, default=0)
    avg_speed_kmh = Column(DECIMAL(5, 2))
    max_speed_kmh = Column(DECIMAL(5, 2))

    # Advanced metrics
    expected_goals = Column(DECIMAL(5, 2))  # xG
    expected_assists = Column(DECIMAL(5, 2))  # xA

    # Rating (0-10 scale)
    match_rating = Column(DECIMAL(4, 2))

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict:
        """Convert player stats to dictionary"""
        return {
            'id': str(self.id),
            'simulation_id': str(self.simulation_id),
            'player_id': str(self.player_id),
            'team_id': str(self.team_id),

            # Basic
            'minutes_played': self.minutes_played,
            'goals': self.goals,
            'assists': self.assists,
            'shots': self.shots,
            'shots_on_target': self.shots_on_target,

            # Passing
            'passes': self.passes,
            'passes_completed': self.passes_completed,
            'pass_accuracy': float(self.pass_accuracy) if self.pass_accuracy else None,
            'key_passes': self.key_passes,

            # Defensive
            'tackles': self.tackles,
            'tackles_won': self.tackles_won,
            'interceptions': self.interceptions,
            'clearances': self.clearances,

            # Physical
            'distance_covered_km': float(self.distance_covered_km) if self.distance_covered_km else None,
            'sprints': self.sprints,
            'avg_speed_kmh': float(self.avg_speed_kmh) if self.avg_speed_kmh else None,
            'max_speed_kmh': float(self.max_speed_kmh) if self.max_speed_kmh else None,

            # Advanced
            'expected_goals': float(self.expected_goals) if self.expected_goals else None,
            'expected_assists': float(self.expected_assists) if self.expected_assists else None,

            # Rating
            'match_rating': float(self.match_rating) if self.match_rating else None
        }

    def calculate_rating(self) -> float:
        """
        Calculate match rating (0-10 scale) based on performance

        Simple algorithm for MVP, can be enhanced later
        """
        rating = 6.0  # Base rating

        # Goals (very important)
        rating += self.goals * 1.0

        # Assists
        rating += self.assists * 0.7

        # Shots on target
        rating += (self.shots_on_target * 0.1)

        # Pass accuracy bonus
        if self.pass_accuracy and self.pass_accuracy > 80:
            rating += 0.5

        # Distance covered (stamina contribution)
        if self.distance_covered_km and self.distance_covered_km > 10:
            rating += 0.3

        # Tackles won
        if self.tackles_won:
            rating += self.tackles_won * 0.2

        # Interceptions
        rating += (self.interceptions or 0) * 0.15

        # Cap at 10.0
        return min(10.0, round(rating, 2))

    def __repr__(self):
        return f"<PlayerMatchStats(player_id={self.player_id}, rating={self.match_rating})>"
