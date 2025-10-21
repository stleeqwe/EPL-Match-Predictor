"""
Position Value Object
Represents player position with general and detailed categorization
"""
from enum import Enum
from dataclasses import dataclass
from typing import List


class GeneralPosition(Enum):
    """General position categories"""
    GK = "GK"
    DF = "DF"
    MF = "MF"
    FW = "FW"


class DetailedPosition(Enum):
    """Detailed position categories"""
    GK = "GK"
    CB = "CB"  # Center Back
    FB = "FB"  # Full Back
    DM = "DM"  # Defensive Midfielder
    CM = "CM"  # Central Midfielder
    CAM = "CAM"  # Central Attacking Midfielder
    WG = "WG"  # Winger
    ST = "ST"  # Striker


@dataclass(frozen=True)
class Position:
    """
    Position value object (immutable)

    Represents a player's position with both general and detailed classification.
    Validates consistency between general and detailed positions.
    """
    general: GeneralPosition
    detailed: DetailedPosition

    # Position mapping: general -> allowed detailed positions
    _POSITION_MAPPING = {
        GeneralPosition.GK: [DetailedPosition.GK],
        GeneralPosition.DF: [DetailedPosition.CB, DetailedPosition.FB],
        GeneralPosition.MF: [DetailedPosition.DM, DetailedPosition.CM, DetailedPosition.CAM],
        GeneralPosition.FW: [DetailedPosition.WG, DetailedPosition.ST]
    }

    def __post_init__(self):
        """Validate position consistency"""
        allowed_detailed = self._POSITION_MAPPING.get(self.general, [])

        if self.detailed not in allowed_detailed:
            raise ValueError(
                f"Inconsistent position: {self.general.value} cannot be {self.detailed.value}. "
                f"Allowed detailed positions for {self.general.value}: "
                f"{[p.value for p in allowed_detailed]}"
            )

    def is_defensive(self) -> bool:
        """Check if position is defensive (GK or DF)"""
        return self.general in [GeneralPosition.GK, GeneralPosition.DF]

    def is_offensive(self) -> bool:
        """Check if position is offensive (FW)"""
        return self.general == GeneralPosition.FW

    def is_midfield(self) -> bool:
        """Check if position is midfield"""
        return self.general == GeneralPosition.MF

    def is_goalkeeper(self) -> bool:
        """Check if position is goalkeeper"""
        return self.general == GeneralPosition.GK

    @classmethod
    def from_string(cls, general: str, detailed: str = None) -> 'Position':
        """
        Create Position from string values

        Args:
            general: General position string (e.g., "GK", "DF")
            detailed: Detailed position string (e.g., "CB", "ST")
                     If None, uses default for general position

        Returns:
            Position instance

        Raises:
            ValueError: If position strings are invalid
        """
        try:
            general_pos = GeneralPosition(general.upper())
        except ValueError:
            raise ValueError(
                f"Invalid general position: {general}. "
                f"Must be one of {[p.value for p in GeneralPosition]}"
            )

        # Use default detailed position if not provided
        if detailed is None:
            default_mapping = {
                GeneralPosition.GK: DetailedPosition.GK,
                GeneralPosition.DF: DetailedPosition.CB,
                GeneralPosition.MF: DetailedPosition.CM,
                GeneralPosition.FW: DetailedPosition.ST
            }
            detailed_pos = default_mapping[general_pos]
        else:
            try:
                detailed_pos = DetailedPosition(detailed.upper())
            except ValueError:
                raise ValueError(
                    f"Invalid detailed position: {detailed}. "
                    f"Must be one of {[p.value for p in DetailedPosition]}"
                )

        return cls(general=general_pos, detailed=detailed_pos)

    @classmethod
    def get_allowed_detailed_positions(cls, general: GeneralPosition) -> List[DetailedPosition]:
        """Get list of allowed detailed positions for a general position"""
        return cls._POSITION_MAPPING.get(general, [])

    def __str__(self) -> str:
        return f"{self.general.value}/{self.detailed.value}"

    def __repr__(self) -> str:
        return f"Position(general={self.general.value}, detailed={self.detailed.value})"
