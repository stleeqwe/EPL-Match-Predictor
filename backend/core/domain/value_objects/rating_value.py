"""
Rating Value Object
Represents a player rating with strict validation (0.0-5.0, 0.25 step)
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class RatingValue:
    """
    Rating value object (immutable)

    Represents a player rating with the following constraints:
    - Range: 0.0 to 5.0
    - Step: 0.25 (only values like 0.0, 0.25, 0.5, ..., 4.75, 5.0)

    Immutable to ensure data integrity.
    """
    value: float

    # Class constants
    MIN_VALUE = 0.0
    MAX_VALUE = 5.0
    STEP = 0.25

    def __post_init__(self):
        """Validate rating value"""
        # Type check
        if not isinstance(self.value, (int, float)):
            raise TypeError(f"Rating must be a number, got {type(self.value)}")

        # Range check
        if self.value < self.MIN_VALUE or self.value > self.MAX_VALUE:
            raise ValueError(
                f"Rating must be between {self.MIN_VALUE} and {self.MAX_VALUE}, "
                f"got {self.value}"
            )

        # Step check (0.25 increments)
        # Calculate expected value by rounding to nearest 0.25
        rounded = round(self.value / self.STEP) * self.STEP

        # Allow small floating point tolerance
        if abs(self.value - rounded) > 1e-9:
            raise ValueError(
                f"Rating must be in {self.STEP} increments. "
                f"Got {self.value}, nearest valid value is {rounded}"
            )

    def to_percentage(self) -> float:
        """
        Convert rating to percentage (0-100)

        Returns:
            Percentage value (0.0 = 0%, 5.0 = 100%)
        """
        return (self.value / self.MAX_VALUE) * 100

    def get_grade(self) -> str:
        """
        Get qualitative grade for the rating

        Returns:
            Grade string (e.g., "World Class", "Elite", etc.)
        """
        if self.value >= 4.5:
            return "World Class"
        elif self.value >= 4.0:
            return "Elite"
        elif self.value >= 3.0:
            return "Good"
        elif self.value >= 2.0:
            return "Average"
        else:
            return "Below Average"

    def get_color_code(self) -> str:
        """
        Get color code for UI display

        Returns:
            Color name for the rating tier
        """
        if self.value >= 4.5:
            return "green"  # Bright green
        elif self.value >= 4.0:
            return "teal"  # Teal
        elif self.value >= 3.0:
            return "blue"  # Blue
        elif self.value >= 2.0:
            return "yellow"  # Yellow
        else:
            return "red"  # Red

    @classmethod
    def from_percentage(cls, percentage: float) -> 'RatingValue':
        """
        Create RatingValue from percentage (0-100)

        Args:
            percentage: Percentage value (0-100)

        Returns:
            RatingValue instance
        """
        value = (percentage / 100) * cls.MAX_VALUE
        # Round to nearest 0.25
        value = round(value / cls.STEP) * cls.STEP
        return cls(value=value)

    def __float__(self) -> float:
        return self.value

    def __str__(self) -> str:
        return f"{self.value:.2f}"

    def __repr__(self) -> str:
        return f"RatingValue({self.value})"

    # Comparison operators
    def __lt__(self, other) -> bool:
        if isinstance(other, RatingValue):
            return self.value < other.value
        return self.value < other

    def __le__(self, other) -> bool:
        if isinstance(other, RatingValue):
            return self.value <= other.value
        return self.value <= other

    def __gt__(self, other) -> bool:
        if isinstance(other, RatingValue):
            return self.value > other.value
        return self.value > other

    def __ge__(self, other) -> bool:
        if isinstance(other, RatingValue):
            return self.value >= other.value
        return self.value >= other

    def __eq__(self, other) -> bool:
        if isinstance(other, RatingValue):
            return abs(self.value - other.value) < 1e-9
        return abs(self.value - other) < 1e-9
