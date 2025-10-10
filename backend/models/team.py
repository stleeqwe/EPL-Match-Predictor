"""
Team ORM Model
SQLAlchemy model for teams with tactical profiles
"""

from sqlalchemy import Column, Integer, String, DECIMAL, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from typing import Dict, List, Optional

from backend.database.connection import Base


class Team(Base):
    """
    Team model with tactical profiles

    Tactical Profile (from existing framework):
    - tactical_organization (38% weight)
    - attacking_efficiency (25% weight)
    - defensive_stability (22% weight)
    - physicality_stamina (8% weight)
    - psychological_factors (7% weight)

    Each category contains weighted sub-attributes (0-100 scale)
    """

    __tablename__ = 'teams'

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic info
    name = Column(String(100), unique=True, nullable=False)
    short_name = Column(String(20))
    code = Column(String(10))  # e.g., "LIV", "MCI"

    # League info
    league = Column(String(50), default='Premier League')
    season = Column(String(10))  # e.g., "2024-25"

    # Tactical Profile (5 categories from existing framework)
    tactical_organization = Column(JSONB, nullable=False, default={})
    attacking_efficiency = Column(JSONB, nullable=False, default={})
    defensive_stability = Column(JSONB, nullable=False, default={})
    physicality_stamina = Column(JSONB, nullable=False, default={})
    psychological_factors = Column(JSONB, nullable=False, default={})

    # Overall team rating (calculated from tactical profile)
    overall_rating = Column(DECIMAL(5, 2))

    # Formation & Style
    default_formation = Column(String(10))  # e.g., "4-3-3", "3-5-2"
    playing_style = Column(JSONB, default={})  # e.g., {"possession": 65, "pressing": 80}

    # External IDs
    fpl_team_id = Column(Integer, unique=True)
    external_ids = Column(JSONB, default={})

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    players = relationship("Player", back_populates="team", cascade="all, delete-orphan")

    # =========================================================================
    # TACTICAL PROFILE STRUCTURE
    # =========================================================================

    @classmethod
    def get_tactical_framework(cls) -> Dict:
        """
        Get the standard tactical framework structure

        Returns the 5 categories with their sub-attributes and weights
        """
        return {
            'tactical_organization': {
                'weight': 0.38,
                'attributes': {
                    'shape_discipline': {'weight': 0.25, 'default': 70},
                    'positional_awareness': {'weight': 0.20, 'default': 70},
                    'defensive_line': {'weight': 0.15, 'default': 70},
                    'compactness': {'weight': 0.15, 'default': 70},
                    'transition_speed': {'weight': 0.15, 'default': 70},
                    'set_piece_organization': {'weight': 0.10, 'default': 70}
                }
            },
            'attacking_efficiency': {
                'weight': 0.25,
                'attributes': {
                    'chance_creation': {'weight': 0.30, 'default': 70},
                    'finishing': {'weight': 0.25, 'default': 70},
                    'movement_off_ball': {'weight': 0.20, 'default': 70},
                    'buildup_quality': {'weight': 0.15, 'default': 70},
                    'crossing_delivery': {'weight': 0.10, 'default': 70}
                }
            },
            'defensive_stability': {
                'weight': 0.22,
                'attributes': {
                    'marking': {'weight': 0.25, 'default': 70},
                    'tackling': {'weight': 0.20, 'default': 70},
                    'aerial_dominance': {'weight': 0.20, 'default': 70},
                    'defensive_positioning': {'weight': 0.20, 'default': 70},
                    'pressing_intensity': {'weight': 0.15, 'default': 70}
                }
            },
            'physicality_stamina': {
                'weight': 0.08,
                'attributes': {
                    'physical_strength': {'weight': 0.35, 'default': 70},
                    'stamina_endurance': {'weight': 0.35, 'default': 70},
                    'pace_speed': {'weight': 0.30, 'default': 70}
                }
            },
            'psychological_factors': {
                'weight': 0.07,
                'attributes': {
                    'mentality': {'weight': 0.40, 'default': 70},
                    'composure': {'weight': 0.30, 'default': 70},
                    'team_cohesion': {'weight': 0.30, 'default': 70}
                }
            }
        }

    # =========================================================================
    # METHODS
    # =========================================================================

    def to_dict(self, include_players: bool = False) -> Dict:
        """Convert team to dictionary"""
        data = {
            'id': str(self.id),
            'name': self.name,
            'short_name': self.short_name,
            'code': self.code,
            'league': self.league,
            'season': self.season,

            # Tactical profile
            'tactical_organization': self.tactical_organization or {},
            'attacking_efficiency': self.attacking_efficiency or {},
            'defensive_stability': self.defensive_stability or {},
            'physicality_stamina': self.physicality_stamina or {},
            'psychological_factors': self.psychological_factors or {},

            # Overall
            'overall_rating': float(self.overall_rating) if self.overall_rating else None,

            # Formation
            'default_formation': self.default_formation,
            'playing_style': self.playing_style or {},

            # Status
            'is_active': self.is_active,

            # External
            'fpl_team_id': self.fpl_team_id,
            'external_ids': self.external_ids or {}
        }

        if include_players and self.players:
            data['players'] = [p.to_dict() for p in self.players]
            data['squad_size'] = len(self.players)

        return data

    def calculate_overall_rating(self) -> float:
        """
        Calculate overall team rating from tactical profile

        Uses weighted average of all categories and sub-attributes
        """
        framework = self.get_tactical_framework()
        total_score = 0.0

        for category_name, category_info in framework.items():
            category_data = getattr(self, category_name) or {}
            category_weight = category_info['weight']

            # Calculate category score
            category_score = 0.0
            for attr_name, attr_info in category_info['attributes'].items():
                attr_value = category_data.get(attr_name, attr_info['default'])
                attr_weight = attr_info['weight']
                category_score += attr_value * attr_weight

            # Add to total
            total_score += category_score * category_weight

        return round(total_score, 2)

    def to_simulation_params(self) -> Dict:
        """
        Convert team tactical profile to simulation parameters

        Returns dict with normalized values (0-1) for physics simulation
        """
        return {
            'team_id': str(self.id),
            'name': self.name,
            'formation': self.default_formation or '4-3-3',
            'overall_rating': float(self.overall_rating or 70),

            # Tactical parameters (normalized 0-1)
            'tactics': {
                'organization': {
                    k: v / 100.0 for k, v in (self.tactical_organization or {}).items()
                },
                'attacking': {
                    k: v / 100.0 for k, v in (self.attacking_efficiency or {}).items()
                },
                'defensive': {
                    k: v / 100.0 for k, v in (self.defensive_stability or {}).items()
                },
                'physical': {
                    k: v / 100.0 for k, v in (self.physicality_stamina or {}).items()
                },
                'mental': {
                    k: v / 100.0 for k, v in (self.psychological_factors or {}).items()
                }
            },

            # Playing style (affects agent behavior)
            'style': self.playing_style or {
                'possession': 50,
                'pressing': 50,
                'tempo': 50,
                'width': 50,
                'attacking_risk': 50
            }
        }

    def get_starting_positions(self, formation: str = None) -> Dict[str, List[tuple]]:
        """
        Get starting positions for players based on formation

        Returns dict mapping position to (x, y) coordinates
        Field: 105m × 68m, origin at center
        """
        formation = formation or self.default_formation or '4-3-3'

        # Formation templates (x, y coordinates in meters)
        formations = {
            '4-3-3': {
                'GK': [(0, 0)],
                'CB': [(-40, -8), (-40, 8)],
                'FB': [(-40, -20), (-40, 20)],
                'DM': [(-20, 0)],
                'CM': [(-10, -12), (-10, 12)],
                'WG': [(20, -25), (20, 25)],
                'ST': [(35, 0)]
            },
            '4-2-3-1': {
                'GK': [(0, 0)],
                'CB': [(-40, -8), (-40, 8)],
                'FB': [(-40, -20), (-40, 20)],
                'DM': [(-25, -8), (-25, 8)],
                'CM': [(-5, -12), (-5, 12)],
                'CAM': [(10, 0)],
                'WG': [(10, -25), (10, 25)],
                'ST': [(35, 0)]
            },
            '3-5-2': {
                'GK': [(0, 0)],
                'CB': [(-40, -12), (-40, 0), (-40, 12)],
                'FB': [(-20, -25), (-20, 25)],
                'CM': [(-10, -12), (-10, 0), (-10, 12)],
                'ST': [(30, -8), (30, 8)]
            }
        }

        return formations.get(formation, formations['4-3-3'])

    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}', rating={self.overall_rating})>"
