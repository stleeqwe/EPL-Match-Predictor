"""
Team Side - Shared Enum

모든 세그먼트에서 사용하는 팀 구분 표준
"""

from enum import Enum


class TeamSide(str, Enum):
    """
    팀 사이드 구분

    경기에서 홈/원정 구분
    """
    HOME = "home"
    AWAY = "away"

    @property
    def opponent(self) -> 'TeamSide':
        """상대 팀"""
        return TeamSide.AWAY if self == TeamSide.HOME else TeamSide.HOME

    @property
    def display_name(self) -> str:
        """표시용 이름"""
        return "홈" if self == TeamSide.HOME else "원정"
