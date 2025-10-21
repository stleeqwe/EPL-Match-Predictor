"""
Rating Entity
Represents player ratings and evaluations
"""
from dataclasses import dataclass, field
from typing import Dict, Optional, List
from datetime import datetime

from core.domain.value_objects.player_id import PlayerId
from core.domain.value_objects.position import Position
from core.domain.value_objects.rating_value import RatingValue


@dataclass
class AttributeRating:
    """
    Single attribute rating

    Represents a rating for one specific attribute (e.g., "pace", "finishing")
    """
    attribute_name: str
    value: RatingValue
    comment: str = ""

    def __post_init__(self):
        """Validate attribute rating"""
        if not self.attribute_name or len(self.attribute_name.strip()) == 0:
            raise ValueError("Attribute name cannot be empty")

    def __str__(self) -> str:
        return f"{self.attribute_name}: {self.value}"


@dataclass
class PlayerRatings:
    """
    Player Ratings Entity

    Aggregate of all attribute ratings for a player.
    Ratings are position-specific (e.g., GK has different attributes than ST).
    """
    # Identity
    player_id: PlayerId
    user_id: str = "default"  # User who created ratings

    # Ratings
    ratings: List[AttributeRating] = field(default_factory=list)

    # Optional comment
    comment: str = ""

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate ratings"""
        if not self.player_id:
            raise ValueError("Player ID is required")

    # ========== Commands ==========

    def add_rating(self, attribute: str, value: RatingValue, comment: str = "") -> None:
        """
        Add or update attribute rating

        Args:
            attribute: Attribute name
            value: Rating value
            comment: Optional comment
        """
        # Check if attribute already exists
        existing = self.get_rating(attribute)
        if existing:
            # Update existing
            existing.value = value
            existing.comment = comment
        else:
            # Add new
            rating = AttributeRating(
                attribute_name=attribute,
                value=value,
                comment=comment
            )
            self.ratings.append(rating)

        self.updated_at = datetime.utcnow()

    def remove_rating(self, attribute: str) -> None:
        """
        Remove attribute rating

        Args:
            attribute: Attribute name to remove
        """
        self.ratings = [r for r in self.ratings if r.attribute_name != attribute]
        self.updated_at = datetime.utcnow()

    def clear_all_ratings(self) -> None:
        """Clear all ratings"""
        self.ratings = []
        self.updated_at = datetime.utcnow()

    # ========== Queries ==========

    def get_rating(self, attribute: str) -> Optional[AttributeRating]:
        """
        Get rating for specific attribute

        Args:
            attribute: Attribute name

        Returns:
            AttributeRating if exists, None otherwise
        """
        for rating in self.ratings:
            if rating.attribute_name == attribute:
                return rating
        return None

    def get_rating_value(self, attribute: str) -> Optional[RatingValue]:
        """
        Get rating value for specific attribute

        Args:
            attribute: Attribute name

        Returns:
            RatingValue if exists, None otherwise
        """
        rating = self.get_rating(attribute)
        return rating.value if rating else None

    def has_rating(self, attribute: str) -> bool:
        """Check if rating exists for attribute"""
        return self.get_rating(attribute) is not None

    def get_all_ratings_dict(self) -> Dict[str, RatingValue]:
        """
        Get all ratings as dictionary

        Returns:
            Dictionary of attribute_name -> RatingValue
        """
        return {r.attribute_name: r.value for r in self.ratings}

    def get_rating_count(self) -> int:
        """Get total number of ratings"""
        return len(self.ratings)

    def is_complete_for_position(self, position: Position, required_attributes: List[str]) -> bool:
        """
        Check if all required attributes for position are rated

        Args:
            position: Player position
            required_attributes: List of required attribute names for position

        Returns:
            True if all required attributes have ratings
        """
        rated_attributes = {r.attribute_name for r in self.ratings}
        required_set = set(required_attributes)
        return required_set.issubset(rated_attributes)

    def calculate_weighted_average(self, weights: Dict[str, float]) -> Optional[RatingValue]:
        """
        Calculate weighted average rating

        Args:
            weights: Dictionary of attribute_name -> weight (must sum to 1.0)

        Returns:
            Weighted average RatingValue, or None if no ratings
        """
        if not self.ratings:
            return None

        total_weight = 0.0
        weighted_sum = 0.0

        for rating in self.ratings:
            weight = weights.get(rating.attribute_name, 0.0)
            weighted_sum += float(rating.value) * weight
            total_weight += weight

        if total_weight == 0:
            return None

        avg = weighted_sum / total_weight
        # Round to 0.25 step
        rounded = round(avg / 0.25) * 0.25
        return RatingValue(rounded)

    def get_top_attributes(self, n: int = 5) -> List[AttributeRating]:
        """
        Get top N highest-rated attributes

        Args:
            n: Number of top attributes to return

        Returns:
            List of top AttributeRating objects
        """
        sorted_ratings = sorted(self.ratings, key=lambda r: r.value.value, reverse=True)
        return sorted_ratings[:n]

    def get_weak_attributes(self, threshold: RatingValue = RatingValue(2.0)) -> List[AttributeRating]:
        """
        Get attributes below threshold

        Args:
            threshold: Minimum rating value

        Returns:
            List of AttributeRating objects below threshold
        """
        return [r for r in self.ratings if r.value < threshold]

    # ========== Validation ==========

    def validate(self, position: Position, required_attributes: List[str]) -> tuple[bool, List[str]]:
        """
        Validate ratings for position

        Args:
            position: Player position
            required_attributes: Required attributes for position

        Returns:
            Tuple of (is_valid, missing_attributes)
        """
        rated_attributes = {r.attribute_name for r in self.ratings}
        required_set = set(required_attributes)

        missing = required_set - rated_attributes

        return len(missing) == 0, list(missing)

    def __str__(self) -> str:
        return f"PlayerRatings(player={self.player_id}, ratings={len(self.ratings)})"

    def __repr__(self) -> str:
        return f"PlayerRatings(player_id={self.player_id}, user_id='{self.user_id}', ratings={len(self.ratings)})"
