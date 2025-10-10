# -*- coding: utf-8 -*-
"""
Match Statistics
Collects and analyzes match statistics

Tracks:
- Goals, shots, passes
- Possession %
- Distance covered
- Sprint statistics
- Event counts
"""

import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass, field

from .event_detector import MatchEvent, EventType


@dataclass
class PlayerStatistics:
    """Statistics for a single player"""
    player_id: str
    distance_covered: float = 0.0  # meters
    sprints: int = 0
    passes_attempted: int = 0
    passes_completed: int = 0
    shots: int = 0
    shots_on_target: int = 0
    goals: int = 0
    tackles_attempted: int = 0
    tackles_won: int = 0
    possessions: int = 0
    time_with_ball: float = 0.0  # seconds

    @property
    def pass_accuracy(self) -> float:
        """Calculate pass accuracy"""
        if self.passes_attempted == 0:
            return 0.0
        return self.passes_completed / self.passes_attempted

    @property
    def shot_accuracy(self) -> float:
        """Calculate shot accuracy"""
        if self.shots == 0:
            return 0.0
        return self.shots_on_target / self.shots

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'player_id': self.player_id,
            'distance_covered': round(self.distance_covered, 1),
            'sprints': self.sprints,
            'passes_attempted': self.passes_attempted,
            'passes_completed': self.passes_completed,
            'pass_accuracy': round(self.pass_accuracy * 100, 1),
            'shots': self.shots,
            'shots_on_target': self.shots_on_target,
            'shot_accuracy': round(self.shot_accuracy * 100, 1),
            'goals': self.goals,
            'tackles_attempted': self.tackles_attempted,
            'tackles_won': self.tackles_won,
            'possessions': self.possessions,
            'time_with_ball': round(self.time_with_ball, 1)
        }


@dataclass
class TeamStatistics:
    """Statistics for a team"""
    team_name: str
    goals: int = 0
    shots: int = 0
    shots_on_target: int = 0
    possession_time: float = 0.0  # seconds
    passes_attempted: int = 0
    passes_completed: int = 0
    tackles_won: int = 0
    corners: int = 0
    fouls: int = 0
    player_stats: Dict[str, PlayerStatistics] = field(default_factory=dict)

    @property
    def possession_percent(self) -> float:
        """Calculate possession percentage (set by MatchStatistics)"""
        return getattr(self, '_possession_percent', 0.0)

    @possession_percent.setter
    def possession_percent(self, value: float):
        self._possession_percent = value

    @property
    def pass_accuracy(self) -> float:
        """Calculate pass accuracy"""
        if self.passes_attempted == 0:
            return 0.0
        return self.passes_completed / self.passes_attempted

    @property
    def shot_accuracy(self) -> float:
        """Calculate shot accuracy"""
        if self.shots == 0:
            return 0.0
        return self.shots_on_target / self.shots

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'team_name': self.team_name,
            'goals': self.goals,
            'shots': self.shots,
            'shots_on_target': self.shots_on_target,
            'shot_accuracy': round(self.shot_accuracy * 100, 1),
            'possession_percent': round(self.possession_percent * 100, 1),
            'passes_attempted': self.passes_attempted,
            'passes_completed': self.passes_completed,
            'pass_accuracy': round(self.pass_accuracy * 100, 1),
            'tackles_won': self.tackles_won,
            'corners': self.corners,
            'fouls': self.fouls
        }


class MatchStatistics:
    """
    Collects and analyzes match statistics

    Processes events and player data to generate comprehensive statistics
    """

    def __init__(
        self,
        home_team_name: str = 'Home',
        away_team_name: str = 'Away',
        home_player_ids: List[str] = None,
        away_player_ids: List[str] = None
    ):
        """
        Initialize match statistics

        Args:
            home_team_name: Home team name
            away_team_name: Away team name
            home_player_ids: List of home player IDs
            away_player_ids: List of away player IDs
        """
        self.home_stats = TeamStatistics(team_name=home_team_name)
        self.away_stats = TeamStatistics(team_name=away_team_name)

        # Initialize player stats
        if home_player_ids:
            for player_id in home_player_ids:
                self.home_stats.player_stats[player_id] = PlayerStatistics(player_id)

        if away_player_ids:
            for player_id in away_player_ids:
                self.away_stats.player_stats[player_id] = PlayerStatistics(player_id)

        # Possession tracking
        self.current_possessing_team = None
        self.last_possession_change_time = 0.0

    def process_events(self, events: List[MatchEvent], match_duration: float):
        """
        Process list of events to update statistics

        Args:
            events: List of match events
            match_duration: Total match duration (seconds)
        """
        for event in events:
            self._process_event(event)

        # FIX: Add final possession period (from last change to match end)
        if self.current_possessing_team and match_duration > 0:
            final_possession_duration = match_duration - self.last_possession_change_time
            if self.current_possessing_team == 'home':
                self.home_stats.possession_time += final_possession_duration
            else:
                self.away_stats.possession_time += final_possession_duration

        # Calculate possession percentages
        if match_duration > 0:
            total_possession = self.home_stats.possession_time + self.away_stats.possession_time
            if total_possession > 0:
                self.home_stats.possession_percent = self.home_stats.possession_time / match_duration
                self.away_stats.possession_percent = self.away_stats.possession_time / match_duration
            else:
                self.home_stats.possession_percent = 0.5
                self.away_stats.possession_percent = 0.5

    def _process_event(self, event: MatchEvent):
        """Process single event"""
        event_type = event.event_type
        team = event.team

        # Get team stats
        if team == 'home':
            team_stats = self.home_stats
        elif team == 'away':
            team_stats = self.away_stats
        else:
            return  # Neutral event

        # Process by type
        if event_type == EventType.GOAL:
            team_stats.goals += 1
            if event.player_id and event.player_id in team_stats.player_stats:
                team_stats.player_stats[event.player_id].goals += 1

        elif event_type == EventType.SHOT_ON_TARGET:
            team_stats.shots += 1
            team_stats.shots_on_target += 1
            if event.player_id and event.player_id in team_stats.player_stats:
                team_stats.player_stats[event.player_id].shots += 1
                team_stats.player_stats[event.player_id].shots_on_target += 1

        elif event_type == EventType.SHOT_OFF_TARGET:
            team_stats.shots += 1
            if event.player_id and event.player_id in team_stats.player_stats:
                team_stats.player_stats[event.player_id].shots += 1

        elif event_type == EventType.PASS_COMPLETED:
            team_stats.passes_attempted += 1
            team_stats.passes_completed += 1
            if event.player_id and event.player_id in team_stats.player_stats:
                team_stats.player_stats[event.player_id].passes_attempted += 1
                team_stats.player_stats[event.player_id].passes_completed += 1

        elif event_type == EventType.PASS_FAILED:
            team_stats.passes_attempted += 1
            if event.player_id and event.player_id in team_stats.player_stats:
                team_stats.player_stats[event.player_id].passes_attempted += 1

        elif event_type == EventType.TACKLE_WON:
            team_stats.tackles_won += 1
            if event.player_id and event.player_id in team_stats.player_stats:
                team_stats.player_stats[event.player_id].tackles_attempted += 1
                team_stats.player_stats[event.player_id].tackles_won += 1

        elif event_type == EventType.CORNER:
            team_stats.corners += 1

        elif event_type == EventType.POSSESSION_CHANGE:
            # Update possession time
            if self.current_possessing_team:
                possession_duration = event.time - self.last_possession_change_time
                if self.current_possessing_team == 'home':
                    self.home_stats.possession_time += possession_duration
                else:
                    self.away_stats.possession_time += possession_duration

            self.current_possessing_team = team
            self.last_possession_change_time = event.time

            # Update player possession count
            if event.player_id:
                if team == 'home' and event.player_id in self.home_stats.player_stats:
                    self.home_stats.player_stats[event.player_id].possessions += 1
                elif team == 'away' and event.player_id in self.away_stats.player_stats:
                    self.away_stats.player_stats[event.player_id].possessions += 1

    def update_player_movement(
        self,
        player_id: str,
        team: str,
        distance: float,
        is_sprinting: bool = False
    ):
        """
        Update player movement statistics

        Args:
            player_id: Player ID
            team: 'home' or 'away'
            distance: Distance moved (meters)
            is_sprinting: Whether player is sprinting
        """
        team_stats = self.home_stats if team == 'home' else self.away_stats

        if player_id in team_stats.player_stats:
            player_stats = team_stats.player_stats[player_id]
            player_stats.distance_covered += distance

            if is_sprinting:
                player_stats.sprints += 1

    def get_summary(self) -> Dict:
        """Get match statistics summary"""
        return {
            'home': self.home_stats.to_dict(),
            'away': self.away_stats.to_dict(),
            'score': {
                'home': self.home_stats.goals,
                'away': self.away_stats.goals
            }
        }

    def get_player_stats(self, player_id: str, team: str) -> Optional[Dict]:
        """Get statistics for specific player"""
        team_stats = self.home_stats if team == 'home' else self.away_stats

        if player_id in team_stats.player_stats:
            return team_stats.player_stats[player_id].to_dict()

        return None

    def validate_realism(self) -> Dict[str, bool]:
        """
        Validate if statistics are realistic (EPL standards)

        Returns:
            Dictionary of validation results
        """
        validation = {}

        # Goals (0-8 per match)
        total_goals = self.home_stats.goals + self.away_stats.goals
        validation['goals_realistic'] = 0 <= total_goals <= 8

        # Shots per team (5-25)
        validation['home_shots_realistic'] = 5 <= self.home_stats.shots <= 25
        validation['away_shots_realistic'] = 5 <= self.away_stats.shots <= 25

        # Possession (30-70%)
        validation['possession_balanced'] = (
            0.30 <= self.home_stats.possession_percent <= 0.70 and
            0.30 <= self.away_stats.possession_percent <= 0.70
        )

        # Pass accuracy (65-92%)
        if self.home_stats.passes_attempted > 0:
            validation['home_pass_accuracy_realistic'] = (
                0.65 <= self.home_stats.pass_accuracy <= 0.92
            )
        else:
            validation['home_pass_accuracy_realistic'] = False

        if self.away_stats.passes_attempted > 0:
            validation['away_pass_accuracy_realistic'] = (
                0.65 <= self.away_stats.pass_accuracy <= 0.92
            )
        else:
            validation['away_pass_accuracy_realistic'] = False

        # Overall
        validation['all_realistic'] = all(validation.values())

        return validation


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    'PlayerStatistics',
    'TeamStatistics',
    'MatchStatistics'
]
