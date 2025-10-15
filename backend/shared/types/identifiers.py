"""
Identifiers - Shared Type Aliases

타입 안전성을 위한 ID 타입 정의
"""

from typing import NewType

# 엔티티 ID 타입들
PlayerId = NewType('PlayerId', str)
TeamId = NewType('TeamId', str)
FormationId = NewType('FormationId', str)
MatchId = NewType('MatchId', str)
PositionId = NewType('PositionId', str)
EventId = NewType('EventId', str)

__all__ = [
    'PlayerId',
    'TeamId',
    'FormationId',
    'MatchId',
    'PositionId',
    'EventId',
]
