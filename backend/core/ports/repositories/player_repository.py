"""
Player Repository Interface (Port)
"""
from abc import ABC, abstractmethod
from typing import Optional, List

from backend.core.domain.entities.player import Player
from backend.core.domain.value_objects.player_id import PlayerId, TeamId


class PlayerRepository(ABC):
    """
    Player Repository Interface

    Defines contract for player data access.
    Concrete implementations in infrastructure layer.
    """

    @abstractmethod
    def find_by_id(self, player_id: PlayerId) -> Optional[Player]:
        """Find player by ID"""
        pass

    @abstractmethod
    def find_by_external_id(self, external_id: int) -> Optional[Player]:
        """Find player by external ID (FPL API ID)"""
        pass

    @abstractmethod
    def find_by_team(self, team_id: TeamId) -> List[Player]:
        """Find all players in a team"""
        pass

    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Player]:
        """Find player by name (partial match)"""
        pass

    @abstractmethod
    def find_all(self) -> List[Player]:
        """Find all players"""
        pass

    @abstractmethod
    def save(self, player: Player) -> Player:
        """Save or update player"""
        pass

    @abstractmethod
    def delete(self, player_id: PlayerId) -> bool:
        """Delete player"""
        pass

    @abstractmethod
    def exists(self, player_id: PlayerId) -> bool:
        """Check if player exists"""
        pass
