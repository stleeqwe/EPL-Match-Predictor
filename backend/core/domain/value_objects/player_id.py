"""
Player ID Value Object
Immutable identifier for Player entity
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class PlayerId:
    """
    Player ID value object (immutable)

    Represents a unique identifier for a player.
    Frozen dataclass ensures immutability.
    """
    value: int

    def __post_init__(self):
        """Validate player ID"""
        if not isinstance(self.value, int):
            raise TypeError(f"Player ID must be an integer, got {type(self.value)}")

        if self.value <= 0:
            raise ValueError(f"Player ID must be positive, got {self.value}")

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"PlayerId({self.value})"

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True)
class TeamId:
    """
    Team ID value object (immutable)

    Represents a unique identifier for a team.
    """
    value: int

    def __post_init__(self):
        """Validate team ID"""
        if not isinstance(self.value, int):
            raise TypeError(f"Team ID must be an integer, got {type(self.value)}")

        if self.value <= 0:
            raise ValueError(f"Team ID must be positive, got {self.value}")

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"TeamId({self.value})"

    def __int__(self) -> int:
        return self.value


@dataclass(frozen=True)
class MatchId:
    """
    Match ID value object (immutable)

    Represents a unique identifier for a match.
    """
    value: int

    def __post_init__(self):
        """Validate match ID"""
        if not isinstance(self.value, int):
            raise TypeError(f"Match ID must be an integer, got {type(self.value)}")

        if self.value <= 0:
            raise ValueError(f"Match ID must be positive, got {self.value}")

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"MatchId({self.value})"

    def __int__(self) -> int:
        return self.value
