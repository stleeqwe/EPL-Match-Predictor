"""
Player ORM Model
SQLAlchemy model for players with position-specific attributes for physics simulation
"""

from sqlalchemy import Column, Integer, String, DECIMAL, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from typing import Dict, List, Optional

from backend.database.connection import Base


class Player(Base):
    """
    Player model with position-specific attributes

    Positions:
    - GK: Goalkeeper
    - CB: Center Back
    - FB: Full Back (LB/RB)
    - DM: Defensive Midfielder
    - CM: Central Midfielder
    - CAM: Attacking Midfielder
    - WG: Winger (LW/RW)
    - ST: Striker

    Physical attributes (0-100 scale):
    - pace: Sprint speed (70 = 7.0 m/s max speed)
    - acceleration: Acceleration rate (70 = 7.0 m/s² max)
    - stamina: Endurance (affects stamina drain rate)
    - strength: Physical power (affects duels)
    - agility: Change of direction speed
    """

    __tablename__ = 'players'

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key
    team_id = Column(UUID(as_uuid=True), ForeignKey('teams.id', ondelete='CASCADE'))

    # Basic info
    name = Column(String(100), nullable=False)
    position = Column(String(10), nullable=False)
    squad_number = Column(Integer)

    # Physical attributes (0-100 scale)
    pace = Column(DECIMAL(5, 2))  # Sprint speed
    acceleration = Column(DECIMAL(5, 2))  # Acceleration rate
    stamina = Column(DECIMAL(5, 2))  # Endurance
    strength = Column(DECIMAL(5, 2))  # Physical power
    agility = Column(DECIMAL(5, 2))  # Change of direction

    # Technical attributes (position-specific, stored as JSONB)
    technical_attributes = Column(JSONB, nullable=False, default={})

    # Mental attributes (JSONB)
    mental_attributes = Column(JSONB, default={})

    # Overall rating (calculated)
    overall_rating = Column(DECIMAL(5, 2))

    # External IDs
    fpl_player_id = Column(Integer, unique=True)
    external_ids = Column(JSONB, default={})

    # Status
    is_active = Column(Boolean, default=True)
    injury_status = Column(String(20))
    injury_return_date = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    team = relationship("Team", back_populates="players")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            position.in_(['GK', 'CB', 'FB', 'DM', 'CM', 'CAM', 'WG', 'ST']),
            name='valid_position'
        ),
    )

    # =========================================================================
    # POSITION-SPECIFIC ATTRIBUTE DEFINITIONS
    # =========================================================================

    @classmethod
    def get_position_attributes(cls, position: str) -> List[str]:
        """
        Get required technical attributes for a position

        Returns list of attribute names that should be in technical_attributes JSONB
        """
        attributes_map = {
            'GK': [
                'reflexes',  # Shot stopping ability
                'positioning',  # Goalkeeper positioning
                'handling',  # Catching/holding ball
                'diving',  # Diving save ability
                'kicking',  # Distribution quality
                'command_area',  # Commanding penalty area
                'one_on_one',  # 1v1 situations
                'aerial_reach'  # High ball collection
            ],
            'CB': [
                'tackling',  # Tackling accuracy
                'marking',  # Man marking
                'heading',  # Aerial duels
                'positioning',  # Defensive positioning
                'passing',  # Passing accuracy
                'composure',  # Calmness under pressure
                'interceptions',  # Reading the game
                'aerial_ability'  # Heading strength
            ],
            'FB': [
                'tackling',  # 1v1 defending
                'marking',  # Defensive awareness
                'crossing',  # Cross quality
                'stamina',  # Endurance for overlaps
                'positioning',  # Defensive position
                'pace',  # Recovery speed
                'dribbling',  # Carrying ball forward
                'passing'  # Distribution
            ],
            'DM': [
                'tackling',  # Ball winning
                'interceptions',  # Reading play
                'passing',  # Distribution
                'vision',  # Passing range
                'positioning',  # Defensive shape
                'stamina',  # Box-to-box ability
                'composure',  # Calmness
                'long_shots'  # Shooting from distance
            ],
            'CM': [
                'passing',  # Passing accuracy
                'vision',  # Creative passing
                'dribbling',  # Ball control
                'stamina',  # Box-to-box
                'tackling',  # Defensive contribution
                'long_shots',  # Shooting
                'positioning',  # Spatial awareness
                'work_rate'  # Defensive work rate
            ],
            'CAM': [
                'passing',  # Through balls
                'vision',  # Creative vision
                'dribbling',  # Close control
                'shooting',  # Finishing
                'creativity',  # Unpredictability
                'weak_foot',  # Weak foot ability
                'long_shots',  # Distance shooting
                'free_kicks'  # Set piece delivery
            ],
            'WG': [
                'pace',  # Sprint speed
                'dribbling',  # 1v1 ability
                'crossing',  # Cross delivery
                'shooting',  # Finishing
                'stamina',  # Tracking back
                'weak_foot',  # Both feet
                'agility',  # Change of direction
                'creativity'  # Unpredictability
            ],
            'ST': [
                'shooting',  # Shot power
                'finishing',  # Clinical finishing
                'positioning',  # Movement in box
                'heading',  # Aerial ability
                'dribbling',  # Hold-up play
                'pace',  # Sprint speed
                'composure',  # 1v1 finishing
                'weak_foot'  # Both feet
            ]
        }

        return attributes_map.get(position, [])

    # =========================================================================
    # METHODS
    # =========================================================================

    def to_dict(self, include_team: bool = False) -> Dict:
        """Convert player to dictionary"""
        data = {
            'id': str(self.id),
            'team_id': str(self.team_id) if self.team_id else None,
            'name': self.name,
            'position': self.position,
            'squad_number': self.squad_number,

            # Physical attributes
            'pace': float(self.pace) if self.pace else None,
            'acceleration': float(self.acceleration) if self.acceleration else None,
            'stamina': float(self.stamina) if self.stamina else None,
            'strength': float(self.strength) if self.strength else None,
            'agility': float(self.agility) if self.agility else None,

            # Technical/Mental
            'technical_attributes': self.technical_attributes or {},
            'mental_attributes': self.mental_attributes or {},

            # Overall
            'overall_rating': float(self.overall_rating) if self.overall_rating else None,

            # Status
            'is_active': self.is_active,
            'injury_status': self.injury_status,

            # External
            'fpl_player_id': self.fpl_player_id,
            'external_ids': self.external_ids or {}
        }

        if include_team and self.team:
            data['team'] = {
                'id': str(self.team.id),
                'name': self.team.name,
                'short_name': self.team.short_name
            }

        return data

    def to_physics_params(self) -> Dict:
        """
        Convert player attributes to physics simulation parameters

        Returns dict with physics-ready values:
        - max_speed: m/s
        - max_acceleration: m/s²
        - stamina_pool: 0-100
        - etc.
        """
        return {
            'player_id': str(self.id),
            'name': self.name,
            'position': self.position,

            # Physics parameters
            'max_speed': float(self.pace or 70) / 10.0,  # 70 pace = 7.0 m/s
            'max_acceleration': float(self.acceleration or 70) / 10.0,  # 70 accel = 7.0 m/s²
            'stamina_pool': float(self.stamina or 70),
            'strength_factor': float(self.strength or 70) / 100.0,
            'agility_factor': float(self.agility or 70) / 100.0,

            # Technical (normalized 0-1)
            'technical_skills': {
                k: v / 100.0 for k, v in (self.technical_attributes or {}).items()
            },

            # Mental (normalized 0-1)
            'mental_skills': {
                k: v / 100.0 for k, v in (self.mental_attributes or {}).items()
            }
        }

    def calculate_overall_rating(self) -> float:
        """
        Calculate overall rating from attributes

        Weighted average based on position
        """
        if not self.pace or not self.acceleration:
            return 0.0

        # Physical base (40% weight)
        physical_avg = (
            float(self.pace or 0) +
            float(self.acceleration or 0) +
            float(self.stamina or 0) +
            float(self.strength or 0) +
            float(self.agility or 0)
        ) / 5.0

        # Technical attributes (40% weight)
        technical_attrs = self.technical_attributes or {}
        if technical_attrs:
            technical_avg = sum(technical_attrs.values()) / len(technical_attrs)
        else:
            technical_avg = 70.0  # Default

        # Mental attributes (20% weight)
        mental_attrs = self.mental_attributes or {}
        if mental_attrs:
            mental_avg = sum(mental_attrs.values()) / len(mental_attrs)
        else:
            mental_avg = 70.0  # Default

        # Weighted average
        overall = (physical_avg * 0.4) + (technical_avg * 0.4) + (mental_avg * 0.2)

        return round(overall, 2)

    def __repr__(self):
        return f"<Player(id={self.id}, name='{self.name}', position='{self.position}', rating={self.overall_rating})>"
