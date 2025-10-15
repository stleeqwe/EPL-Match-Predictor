"""
Shared Kernel

모든 세그먼트가 공유하는 핵심 개념과 타입
"""

from .domain.field_coordinates import FieldCoordinates
from .domain.position_type import PositionType
from .domain.team_side import TeamSide
from .types.identifiers import PlayerId, TeamId, FormationId, MatchId

__all__ = [
    'FieldCoordinates',
    'PositionType',
    'TeamSide',
    'PlayerId',
    'TeamId',
    'FormationId',
    'MatchId',
]
