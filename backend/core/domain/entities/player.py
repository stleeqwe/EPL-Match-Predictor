"""
Player Entity
Core business entity representing a football player
"""
from dataclasses import dataclass, field
from typing import Optional, Dict
from datetime import datetime

from backend.core.domain.value_objects.player_id import PlayerId, TeamId
from backend.core.domain.value_objects.position import Position
from backend.core.domain.value_objects.rating_value import RatingValue


@dataclass
class PlayerStats:
    """
    Player statistics value object

    Contains match statistics for a player.
    Immutable once created.
    """
    appearances: int = 0
    starts: int = 0
    minutes: int = 0
    goals: int = 0
    assists: int = 0
    clean_sheets: int = 0
    yellow_cards: int = 0
    red_cards: int = 0

    def __post_init__(self):
        """Validate statistics"""
        if self.appearances < 0:
            raise ValueError("Appearances cannot be negative")
        if self.starts > self.appearances:
            raise ValueError("Starts cannot exceed appearances")
        if self.minutes < 0:
            raise ValueError("Minutes cannot be negative")
        if self.goals < 0:
            raise ValueError("Goals cannot be negative")
        if self.assists < 0:
            raise ValueError("Assists cannot be negative")

    @property
    def minutes_per_appearance(self) -> float:
        """Calculate average minutes per appearance"""
        if self.appearances == 0:
            return 0.0
        return self.minutes / self.appearances

    @property
    def goals_per_90(self) -> float:
        """Calculate goals per 90 minutes"""
        if self.minutes == 0:
            return 0.0
        return (self.goals / self.minutes) * 90

    @property
    def assists_per_90(self) -> float:
        """Calculate assists per 90 minutes"""
        if self.minutes == 0:
            return 0.0
        return (self.assists / self.minutes) * 90

    @property
    def goal_contributions_per_90(self) -> float:
        """Calculate goal contributions (goals + assists) per 90 minutes"""
        if self.minutes == 0:
            return 0.0
        return ((self.goals + self.assists) / self.minutes) * 90


@dataclass
class Player:
    """
    Player Entity - Aggregate Root

    Represents a football player with all associated data and behavior.
    Central entity in the player management domain.
    """
    # Identity
    id: PlayerId
    external_id: int  # FPL API ID

    # Basic Info
    name: str
    position: Position
    team_id: TeamId
    age: int

    # Optional Info
    photo_code: Optional[str] = None
    nationality: Optional[str] = None

    # Statistics
    stats: PlayerStats = field(default_factory=PlayerStats)

    # Ratings (stored separately, loaded on demand)
    _ratings: Optional[Dict[str, RatingValue]] = field(default=None, repr=False)

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate player entity invariants"""
        # Name validation
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Player name cannot be empty")

        # Age validation
        if self.age < 16 or self.age > 50:
            raise ValueError(f"Invalid age: {self.age}. Must be between 16 and 50")

        # External ID validation
        if self.external_id <= 0:
            raise ValueError(f"Invalid external_id: {self.external_id}. Must be positive")

    # ========== Commands (State Changes) ==========

    def update_stats(self, stats: PlayerStats) -> None:
        """
        Update player statistics

        Args:
            stats: New statistics
        """
        self.stats = stats
        self.updated_at = datetime.utcnow()

    def update_ratings(self, ratings: Dict[str, RatingValue]) -> None:
        """
        Update player ratings

        Args:
            ratings: Dictionary of attribute name -> rating value

        Raises:
            ValueError: If ratings are invalid for the player's position
        """
        # Validation would go here (check if attributes match position)
        self._ratings = ratings
        self.updated_at = datetime.utcnow()

    def update_team(self, team_id: TeamId) -> None:
        """
        Update player's team (transfer)

        Args:
            team_id: New team ID
        """
        self.team_id = team_id
        self.updated_at = datetime.utcnow()

    def increment_age(self) -> None:
        """Increment player age by one year"""
        self.age += 1
        self.updated_at = datetime.utcnow()

    # ========== Queries (Read-only) ==========

    def get_overall_rating(self) -> Optional[RatingValue]:
        """
        Calculate overall rating from individual attribute ratings

        Returns:
            Overall rating if ratings exist, None otherwise

        Note: Actual calculation delegated to domain service
        """
        if not self._ratings:
            return None

        # This would be delegated to RatingCalculator domain service
        # For now, return average
        total = sum(float(r) for r in self._ratings.values())
        count = len(self._ratings)

        if count == 0:
            return None

        avg = total / count
        # Round to 0.25 step
        rounded = round(avg / 0.25) * 0.25
        return RatingValue(rounded)

    def is_regular_starter(self, min_start_ratio: float = 0.5) -> bool:
        """
        Determine if player is a regular starter

        Args:
            min_start_ratio: Minimum ratio of starts/appearances to be considered regular

        Returns:
            True if player is regular starter
        """
        if self.stats.appearances == 0:
            return False

        start_ratio = self.stats.starts / self.stats.appearances
        return start_ratio >= min_start_ratio

    def get_form_score(self) -> float:
        """
        Calculate form score (0-10) based on recent performance

        Returns:
            Form score from 0.0 to 10.0

        Business Logic:
        - Base score: 5.0
        - Playing time bonus: +1.5 (>500 min), +0.5 (>200 min)
        - Attack bonus: goals * 0.3 + assists * 0.2 (max +3.0)
        - Defense bonus: clean sheets * 0.1 (max +0.5) for defensive positions
        """
        base_score = 5.0

        # Playing time bonus
        if self.stats.minutes > 500:
            base_score += 1.5
        elif self.stats.minutes > 200:
            base_score += 0.5

        # Attack points
        attack_points = (self.stats.goals * 0.3) + (self.stats.assists * 0.2)
        base_score += min(attack_points, 3.0)

        # Defensive bonus (for GK/DF only)
        if self.position.is_defensive():
            clean_sheet_bonus = self.stats.clean_sheets * 0.1
            base_score += min(clean_sheet_bonus, 0.5)

        # Disciplinary penalty
        disciplinary_penalty = (self.stats.yellow_cards * 0.1) + (self.stats.red_cards * 0.5)
        base_score -= disciplinary_penalty

        return min(max(base_score, 0.0), 10.0)

    def has_ratings(self) -> bool:
        """Check if player has ratings"""
        return self._ratings is not None and len(self._ratings) > 0

    def get_photo_url(self, base_url: str = "https://resources.premierleague.com/premierleague/photos/players/110x140") -> Optional[str]:
        """
        Get player photo URL

        Args:
            base_url: Base URL for player photos

        Returns:
            Full photo URL or None if no photo code
        """
        if not self.photo_code:
            return None
        return f"{base_url}/p{self.photo_code}.png"

    # ========== Entity Equality ==========

    def __eq__(self, other) -> bool:
        """
        Entity equality based on ID

        Two players are equal if they have the same ID.
        """
        if not isinstance(other, Player):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID for use in sets/dicts"""
        return hash(self.id)

    def __str__(self) -> str:
        return f"{self.name} ({self.position.general.value})"

    def __repr__(self) -> str:
        return f"Player(id={self.id}, name='{self.name}', position={self.position})"
