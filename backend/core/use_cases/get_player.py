"""
Get Player Use Case
"""
from dataclasses import dataclass

from core.ports.repositories.player_repository import PlayerRepository
from core.domain.entities.player import Player
from core.domain.value_objects.player_id import PlayerId


@dataclass
class GetPlayerRequest:
    """Request to get player"""
    player_id: int


@dataclass
class GetPlayerResponse:
    """Response with player data"""
    player: Player


class GetPlayerUseCase:
    """
    Get Player Use Case

    Retrieves a player by ID.
    """

    def __init__(self, player_repository: PlayerRepository):
        self._player_repository = player_repository

    def execute(self, request: GetPlayerRequest) -> GetPlayerResponse:
        """
        Execute use case

        Args:
            request: Request with player ID

        Returns:
            Response with player

        Raises:
            ValueError: If player not found
        """
        player_id = PlayerId(request.player_id)
        player = self._player_repository.find_by_id(player_id)

        if not player:
            raise ValueError(f"Player not found: {request.player_id}")

        return GetPlayerResponse(player=player)
