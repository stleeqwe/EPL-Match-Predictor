"""
Match Entity
Represents a football match between two teams
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

from core.domain.value_objects.player_id import MatchId, TeamId
from core.domain.value_objects.formation import Formation


class MatchStatus(Enum):
    """Match status"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"


class MatchResult(Enum):
    """Match result from home team perspective"""
    HOME_WIN = "home_win"
    DRAW = "draw"
    AWAY_WIN = "away_win"
    NOT_DECIDED = "not_decided"


@dataclass
class MatchScore:
    """Match score"""
    home: int = 0
    away: int = 0

    def __post_init__(self):
        """Validate score"""
        if self.home < 0 or self.away < 0:
            raise ValueError("Score cannot be negative")

    @property
    def total(self) -> int:
        """Total goals in match"""
        return self.home + self.away

    def get_result(self) -> MatchResult:
        """Get match result"""
        if self.home > self.away:
            return MatchResult.HOME_WIN
        elif self.home < self.away:
            return MatchResult.AWAY_WIN
        else:
            return MatchResult.DRAW

    def __str__(self) -> str:
        return f"{self.home}-{self.away}"


@dataclass
class MatchEvent:
    """Single match event (goal, card, substitution, etc.)"""
    minute: int
    event_type: str
    team: str  # "home" or "away"
    player_id: Optional[int] = None
    description: str = ""

    def __post_init__(self):
        """Validate event"""
        if self.minute < 0 or self.minute > 120:  # Including extra time
            raise ValueError(f"Invalid minute: {self.minute}")

        if self.team not in ["home", "away"]:
            raise ValueError(f"Invalid team: {self.team}. Must be 'home' or 'away'")


@dataclass
class Match:
    """
    Match Entity - Aggregate Root

    Represents a football match with all associated data.
    """
    # Identity
    id: MatchId

    # Teams
    home_team_id: TeamId
    away_team_id: TeamId

    # Match Details
    scheduled_date: datetime
    venue: Optional[str] = None
    competition: str = "Premier League"

    # Formation
    home_formation: Optional[Formation] = None
    away_formation: Optional[Formation] = None

    # Status and Score
    status: MatchStatus = MatchStatus.SCHEDULED
    score: MatchScore = field(default_factory=MatchScore)

    # Events
    events: List[MatchEvent] = field(default_factory=list)

    # Statistics
    stats: Optional[Dict[str, any]] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate match"""
        if self.home_team_id == self.away_team_id:
            raise ValueError("Home and away teams cannot be the same")

    # ========== Match Status Management ==========

    def start_match(self) -> None:
        """Start the match"""
        if self.status != MatchStatus.SCHEDULED:
            raise ValueError(f"Cannot start match with status: {self.status.value}")

        self.status = MatchStatus.IN_PROGRESS
        self.updated_at = datetime.utcnow()

    def finish_match(self) -> None:
        """Finish the match"""
        if self.status != MatchStatus.IN_PROGRESS:
            raise ValueError(f"Cannot finish match with status: {self.status.value}")

        self.status = MatchStatus.FINISHED
        self.updated_at = datetime.utcnow()

    def postpone_match(self) -> None:
        """Postpone the match"""
        if self.status not in [MatchStatus.SCHEDULED, MatchStatus.IN_PROGRESS]:
            raise ValueError(f"Cannot postpone match with status: {self.status.value}")

        self.status = MatchStatus.POSTPONED
        self.updated_at = datetime.utcnow()

    def cancel_match(self) -> None:
        """Cancel the match"""
        self.status = MatchStatus.CANCELLED
        self.updated_at = datetime.utcnow()

    # ========== Score Management ==========

    def record_goal(self, team: str, minute: int, player_id: Optional[int] = None) -> None:
        """
        Record a goal

        Args:
            team: "home" or "away"
            minute: Minute of goal
            player_id: Scorer's player ID (optional)
        """
        if team == "home":
            self.score.home += 1
        elif team == "away":
            self.score.away += 1
        else:
            raise ValueError(f"Invalid team: {team}")

        # Add goal event
        self.add_event(
            minute=minute,
            event_type="goal",
            team=team,
            player_id=player_id,
            description="Goal"
        )

        self.updated_at = datetime.utcnow()

    def set_score(self, home_score: int, away_score: int) -> None:
        """
        Set final score

        Args:
            home_score: Home team score
            away_score: Away team score
        """
        self.score = MatchScore(home=home_score, away=away_score)
        self.updated_at = datetime.utcnow()

    # ========== Event Management ==========

    def add_event(
        self,
        minute: int,
        event_type: str,
        team: str,
        player_id: Optional[int] = None,
        description: str = ""
    ) -> None:
        """
        Add match event

        Args:
            minute: Event minute
            event_type: Type of event (goal, yellow_card, substitution, etc.)
            team: "home" or "away"
            player_id: Player involved (optional)
            description: Event description
        """
        event = MatchEvent(
            minute=minute,
            event_type=event_type,
            team=team,
            player_id=player_id,
            description=description
        )
        self.events.append(event)
        # Sort events by minute
        self.events.sort(key=lambda e: e.minute)
        self.updated_at = datetime.utcnow()

    def get_events_by_type(self, event_type: str) -> List[MatchEvent]:
        """Get all events of specific type"""
        return [e for e in self.events if e.event_type == event_type]

    def get_goals(self) -> List[MatchEvent]:
        """Get all goal events"""
        return self.get_events_by_type("goal")

    # ========== Formation Management ==========

    def set_formations(self, home: Formation, away: Formation) -> None:
        """
        Set formations for both teams

        Args:
            home: Home team formation
            away: Away team formation
        """
        self.home_formation = home
        self.away_formation = away
        self.updated_at = datetime.utcnow()

    # ========== Queries ==========

    def get_result(self) -> MatchResult:
        """Get match result"""
        if self.status != MatchStatus.FINISHED:
            return MatchResult.NOT_DECIDED
        return self.score.get_result()

    def is_finished(self) -> bool:
        """Check if match is finished"""
        return self.status == MatchStatus.FINISHED

    def is_in_progress(self) -> bool:
        """Check if match is in progress"""
        return self.status == MatchStatus.IN_PROGRESS

    def get_winner_team_id(self) -> Optional[TeamId]:
        """
        Get winning team ID

        Returns:
            TeamId of winner, or None if draw/not finished
        """
        result = self.get_result()
        if result == MatchResult.HOME_WIN:
            return self.home_team_id
        elif result == MatchResult.AWAY_WIN:
            return self.away_team_id
        return None

    def get_duration_minutes(self) -> int:
        """Get match duration in minutes"""
        if not self.events:
            return 0
        return max(e.minute for e in self.events)

    # ========== Entity Equality ==========

    def __eq__(self, other) -> bool:
        """Entity equality based on ID"""
        if not isinstance(other, Match):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID"""
        return hash(self.id)

    def __str__(self) -> str:
        return f"{self.home_team_id} vs {self.away_team_id} - {self.score}"

    def __repr__(self) -> str:
        return f"Match(id={self.id}, home={self.home_team_id}, away={self.away_team_id}, status={self.status.value})"
