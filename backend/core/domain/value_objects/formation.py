"""
Formation Value Object
Represents team formation (e.g., 4-3-3, 4-4-2)
"""
from dataclasses import dataclass
from typing import List, Tuple
import re


@dataclass(frozen=True)
class Formation:
    """
    Formation value object (immutable)

    Represents a football formation with validation.
    Examples: 4-3-3, 4-4-2, 3-5-2, etc.
    """
    value: str

    # Supported formations
    SUPPORTED_FORMATIONS = [
        '4-3-3', '4-4-2', '4-2-3-1', '3-5-2',
        '3-4-3', '5-3-2', '4-5-1', '5-4-1'
    ]

    def __post_init__(self):
        """Validate formation"""
        if not isinstance(self.value, str):
            raise TypeError(f"Formation must be a string, got {type(self.value)}")

        # Check if formation is in supported list
        if self.value not in self.SUPPORTED_FORMATIONS:
            raise ValueError(
                f"Unsupported formation: {self.value}. "
                f"Supported formations: {', '.join(self.SUPPORTED_FORMATIONS)}"
            )

        # Additional validation: format check (X-X-X or X-X-X-X)
        if not re.match(r'^\d+-\d+(-\d+)?(-\d+)?$', self.value):
            raise ValueError(f"Invalid formation format: {self.value}")

        # Validate total players (must be 10 outfield players)
        parts = self.value.split('-')
        total = sum(int(p) for p in parts)
        if total != 10:
            raise ValueError(
                f"Formation must have exactly 10 outfield players, got {total}"
            )

    def get_structure(self) -> List[int]:
        """
        Get formation structure as list of integers

        Returns:
            List of player counts per line (e.g., [4, 3, 3] for 4-3-3)
        """
        return [int(p) for p in self.value.split('-')]

    def get_defender_count(self) -> int:
        """Get number of defenders"""
        return self.get_structure()[0]

    def get_midfielder_count(self) -> int:
        """Get number of midfielders (sum of all midfield lines)"""
        structure = self.get_structure()
        if len(structure) == 3:
            # Standard formation (e.g., 4-3-3)
            return structure[1]
        elif len(structure) == 4:
            # Complex formation (e.g., 4-2-3-1)
            return structure[1] + structure[2]
        return 0

    def get_forward_count(self) -> int:
        """Get number of forwards"""
        structure = self.get_structure()
        return structure[-1]

    def is_defensive(self) -> bool:
        """Check if formation is defensive (5+ defenders)"""
        return self.get_defender_count() >= 5

    def is_offensive(self) -> bool:
        """Check if formation is offensive (3 defenders)"""
        return self.get_defender_count() == 3

    def is_balanced(self) -> bool:
        """Check if formation is balanced (4 defenders)"""
        return self.get_defender_count() == 4

    @classmethod
    def create(cls, defenders: int, midfielders: int, forwards: int) -> 'Formation':
        """
        Create Formation from separate line counts

        Args:
            defenders: Number of defenders
            midfielders: Number of midfielders
            forwards: Number of forwards

        Returns:
            Formation instance
        """
        value = f"{defenders}-{midfielders}-{forwards}"
        return cls(value=value)

    @classmethod
    def get_all_supported(cls) -> List[str]:
        """Get list of all supported formations"""
        return cls.SUPPORTED_FORMATIONS.copy()

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"Formation('{self.value}')"
