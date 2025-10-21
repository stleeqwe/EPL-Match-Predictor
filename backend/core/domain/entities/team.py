"""
Team Entity
Represents a football team with squad and tactics
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime

from core.domain.value_objects.player_id import TeamId, PlayerId
from core.domain.value_objects.formation import Formation


@dataclass
class TeamStats:
    """Team statistics"""
    matches_played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0

    @property
    def points(self) -> int:
        """Calculate total points (3 for win, 1 for draw)"""
        return (self.wins * 3) + self.draws

    @property
    def goal_difference(self) -> int:
        """Calculate goal difference"""
        return self.goals_for - self.goals_against

    @property
    def win_rate(self) -> float:
        """Calculate win rate percentage"""
        if self.matches_played == 0:
            return 0.0
        return (self.wins / self.matches_played) * 100

    @property
    def goals_per_game(self) -> float:
        """Calculate average goals scored per game"""
        if self.matches_played == 0:
            return 0.0
        return self.goals_for / self.matches_played

    @property
    def goals_conceded_per_game(self) -> float:
        """Calculate average goals conceded per game"""
        if self.matches_played == 0:
            return 0.0
        return self.goals_against / self.matches_played


@dataclass
class Team:
    """
    Team Entity - Aggregate Root

    Represents a football team with squad, formation, and tactics.
    """
    # Identity
    id: TeamId
    external_id: int  # External API ID
    name: str
    short_name: str

    # Basic Info
    emblem_url: Optional[str] = None
    stadium: Optional[str] = None

    # Squad (player IDs - actual Player entities loaded separately)
    player_ids: List[PlayerId] = field(default_factory=list)

    # Formation and Tactics
    default_formation: Optional[Formation] = None
    tactics: Optional[Dict[str, any]] = field(default=None)

    # Statistics
    stats: TeamStats = field(default_factory=TeamStats)

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate team entity"""
        if not self.name or len(self.name.strip()) == 0:
            raise ValueError("Team name cannot be empty")

        if not self.short_name or len(self.short_name.strip()) == 0:
            raise ValueError("Team short name cannot be empty")

        if self.external_id <= 0:
            raise ValueError(f"Invalid external_id: {self.external_id}")

    # ========== Squad Management ==========

    def add_player(self, player_id: PlayerId) -> None:
        """
        Add player to squad

        Args:
            player_id: Player ID to add

        Raises:
            ValueError: If player already in squad
        """
        if player_id in self.player_ids:
            raise ValueError(f"Player {player_id} already in squad")

        self.player_ids.append(player_id)
        self.updated_at = datetime.utcnow()

    def remove_player(self, player_id: PlayerId) -> None:
        """
        Remove player from squad

        Args:
            player_id: Player ID to remove

        Raises:
            ValueError: If player not in squad
        """
        if player_id not in self.player_ids:
            raise ValueError(f"Player {player_id} not in squad")

        self.player_ids.remove(player_id)
        self.updated_at = datetime.utcnow()

    def has_player(self, player_id: PlayerId) -> bool:
        """Check if player is in squad"""
        return player_id in self.player_ids

    def get_squad_size(self) -> int:
        """Get total squad size"""
        return len(self.player_ids)

    # ========== Formation and Tactics ==========

    def set_formation(self, formation: Formation) -> None:
        """
        Set default formation

        Args:
            formation: Formation to set
        """
        self.default_formation = formation
        self.updated_at = datetime.utcnow()

    def update_tactics(self, tactics: Dict[str, any]) -> None:
        """
        Update team tactics

        Args:
            tactics: Tactical configuration dictionary
        """
        self.tactics = tactics
        self.updated_at = datetime.utcnow()

    # ========== Statistics ==========

    def record_match_result(
        self,
        goals_for: int,
        goals_against: int
    ) -> None:
        """
        Record match result and update statistics

        Args:
            goals_for: Goals scored by team
            goals_against: Goals conceded by team
        """
        self.stats.matches_played += 1
        self.stats.goals_for += goals_for
        self.stats.goals_against += goals_against

        # Determine result
        if goals_for > goals_against:
            self.stats.wins += 1
        elif goals_for == goals_against:
            self.stats.draws += 1
        else:
            self.stats.losses += 1

        self.updated_at = datetime.utcnow()

    def reset_stats(self) -> None:
        """Reset all statistics (e.g., new season)"""
        self.stats = TeamStats()
        self.updated_at = datetime.utcnow()

    # ========== Queries ==========

    def get_form_score(self) -> float:
        """
        Calculate team form score (0-10)

        Returns:
            Form score based on recent performance
        """
        if self.stats.matches_played == 0:
            return 5.0

        # Base on win rate and goal difference
        base_score = 5.0

        # Win rate bonus (0 to +3)
        win_rate_bonus = (self.stats.win_rate / 100) * 3

        # Goal difference bonus/penalty (-2 to +2)
        gd_per_game = self.stats.goal_difference / self.stats.matches_played
        gd_bonus = max(min(gd_per_game, 2.0), -2.0)

        total = base_score + win_rate_bonus + gd_bonus
        return min(max(total, 0.0), 10.0)

    def is_in_form(self, min_score: float = 6.0) -> bool:
        """
        Check if team is in good form

        Args:
            min_score: Minimum form score to be considered in form

        Returns:
            True if team is in form
        """
        return self.get_form_score() >= min_score

    # ========== Entity Equality ==========

    def __eq__(self, other) -> bool:
        """Entity equality based on ID"""
        if not isinstance(other, Team):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID"""
        return hash(self.id)

    def __str__(self) -> str:
        return f"{self.name}"

    def __repr__(self) -> str:
        return f"Team(id={self.id}, name='{self.name}', players={len(self.player_ids)})"
