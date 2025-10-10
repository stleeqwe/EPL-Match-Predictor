# -*- coding: utf-8 -*-
"""
Event Detector
Detects match events (goals, shots, passes, tackles, etc.)

Responsibilities:
- Goal detection
- Shot detection (on/off target)
- Pass completion detection
- Tackle/interception detection
- Out of bounds detection
"""

import numpy as np
from typing import List, Optional, Dict
from dataclasses import dataclass
from enum import Enum

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from physics.ball_physics import BallState
from physics.player_physics import PlayerState
from physics.constants import (
    FIELD_X_MIN, FIELD_X_MAX, FIELD_Y_MIN, FIELD_Y_MAX,
    GOAL_Y_MIN, GOAL_Y_MAX, GOAL_HEIGHT,
    is_in_goal, distance_2d
)


class EventType(Enum):
    """Match event types"""
    GOAL = 'goal'
    SHOT_ON_TARGET = 'shot_on_target'
    SHOT_OFF_TARGET = 'shot_off_target'
    SHOT_BLOCKED = 'shot_blocked'
    PASS_COMPLETED = 'pass_completed'
    PASS_FAILED = 'pass_failed'
    TACKLE_WON = 'tackle_won'
    TACKLE_LOST = 'tackle_lost'
    INTERCEPTION = 'interception'
    SAVE = 'save'
    CORNER = 'corner'
    THROW_IN = 'throw_in'
    GOAL_KICK = 'goal_kick'
    POSSESSION_CHANGE = 'possession_change'
    KICK_OFF = 'kick_off'


@dataclass
class MatchEvent:
    """Single match event"""
    event_type: EventType
    time: float  # Seconds into match
    team: str  # 'home' or 'away'
    player_id: Optional[str] = None
    position: Optional[np.ndarray] = None
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        result = {
            'event_type': self.event_type.value,
            'time': float(self.time),
            'team': self.team,
            'metadata': self.metadata
        }

        if self.player_id:
            result['player_id'] = self.player_id

        if self.position is not None:
            result['position'] = {
                'x': float(self.position[0]),
                'y': float(self.position[1])
            }

        return result


class EventDetector:
    """
    Detects match events from simulation state

    Tracks:
    - Goals scored
    - Shots taken
    - Passes made
    - Tackles/interceptions
    - Out of bounds
    """

    def __init__(self):
        """Initialize event detector"""
        self.events: List[MatchEvent] = []
        self.last_ball_position = None
        self.last_ball_owner = None
        self.last_shot_time = 0.0
        self.consecutive_passes = 0

    def detect_events(
        self,
        current_time: float,
        ball_state: BallState,
        home_players: List[PlayerState],
        away_players: List[PlayerState],
        home_player_ids: List[str],
        away_player_ids: List[str],
        is_home_attacking_left: bool
    ) -> List[MatchEvent]:
        """
        Detect all events for current frame

        Args:
            current_time: Current match time (seconds)
            ball_state: Current ball state
            home_players: Home team player states
            away_players: Away team player states
            home_player_ids: Home team player IDs
            away_player_ids: Away team player IDs
            is_home_attacking_left: True if home attacks left goal

        Returns:
            List of detected events
        """
        frame_events = []

        # 1. Check for goal
        goal_event = self._detect_goal(
            current_time, ball_state, is_home_attacking_left
        )
        if goal_event:
            frame_events.append(goal_event)
            self.events.append(goal_event)

        # 2. Check for shots
        shot_event = self._detect_shot(
            current_time, ball_state,
            home_players, away_players,
            home_player_ids, away_player_ids,
            is_home_attacking_left
        )
        if shot_event:
            frame_events.append(shot_event)
            self.events.append(shot_event)

        # 3. Check for out of bounds
        out_event = self._detect_out_of_bounds(
            current_time, ball_state, is_home_attacking_left
        )
        if out_event:
            frame_events.append(out_event)
            self.events.append(out_event)

        # 4. Check for possession change
        possession_event = self._detect_possession_change(
            current_time, ball_state,
            home_players, away_players,
            home_player_ids, away_player_ids
        )
        if possession_event:
            frame_events.append(possession_event)
            self.events.append(possession_event)

        # Update tracking
        self.last_ball_position = ball_state.position.copy()

        return frame_events

    def _detect_goal(
        self,
        current_time: float,
        ball_state: BallState,
        is_home_attacking_left: bool
    ) -> Optional[MatchEvent]:
        """Detect if goal was scored"""
        x, y, h = ball_state.position

        # Check left goal (home defends if attacking_left)
        if is_in_goal(x, y, h, attacking_left=True):
            # Away team scored (attacking right goal)
            return MatchEvent(
                event_type=EventType.GOAL,
                time=current_time,
                team='away',
                position=ball_state.position.copy(),
                metadata={'goal_position': {'x': x, 'y': y, 'h': h}}
            )

        # Check right goal (away defends if attacking_left)
        if is_in_goal(x, y, h, attacking_left=False):
            # Home team scored (attacking left goal)
            return MatchEvent(
                event_type=EventType.GOAL,
                time=current_time,
                team='home',
                position=ball_state.position.copy(),
                metadata={'goal_position': {'x': x, 'y': y, 'h': h}}
            )

        return None

    def _detect_shot(
        self,
        current_time: float,
        ball_state: BallState,
        home_players: List[PlayerState],
        away_players: List[PlayerState],
        home_player_ids: List[str],
        away_player_ids: List[str],
        is_home_attacking_left: bool
    ) -> Optional[MatchEvent]:
        """Detect shots on/off target"""
        # Shot detection: fast ball moving toward goal
        speed = np.linalg.norm(ball_state.velocity[:2])

        if speed < 10.0:  # Too slow to be a shot
            return None

        # Cooldown between shots (0.5s)
        if current_time - self.last_shot_time < 0.5:
            return None

        x, y, h = ball_state.position
        vx, vy = ball_state.velocity[:2]

        # Determine which goal ball is heading toward
        heading_left = vx < 0
        heading_right = vx > 0

        # Check if shot toward goal
        is_shot = False
        shooting_team = None

        if heading_left and is_home_attacking_left:
            # Home team shooting at left goal
            is_shot = True
            shooting_team = 'home'
            goal_x = FIELD_X_MIN
        elif heading_right and not is_home_attacking_left:
            # Home team shooting at right goal
            is_shot = True
            shooting_team = 'home'
            goal_x = FIELD_X_MAX
        elif heading_left and not is_home_attacking_left:
            # Away team shooting at left goal
            is_shot = True
            shooting_team = 'away'
            goal_x = FIELD_X_MIN
        elif heading_right and is_home_attacking_left:
            # Away team shooting at right goal
            is_shot = True
            shooting_team = 'away'
            goal_x = FIELD_X_MAX

        if not is_shot:
            return None

        # Check if on target (would hit goal if continues)
        # Simple projection: where will ball be at goal line?
        distance_to_goal = abs(x - goal_x)
        if distance_to_goal < 1.0:
            return None  # Already at goal

        time_to_goal = distance_to_goal / abs(vx) if abs(vx) > 0.1 else 999

        # Project ball position at goal line
        projected_y = y + vy * time_to_goal
        projected_h = h + ball_state.velocity[2] * time_to_goal - 0.5 * 9.81 * time_to_goal**2

        # Check if within goal dimensions
        on_target = (
            GOAL_Y_MIN <= projected_y <= GOAL_Y_MAX and
            0 <= projected_h <= GOAL_HEIGHT
        )

        # Update last shot time
        self.last_shot_time = current_time

        event_type = EventType.SHOT_ON_TARGET if on_target else EventType.SHOT_OFF_TARGET

        return MatchEvent(
            event_type=event_type,
            time=current_time,
            team=shooting_team,
            position=ball_state.position.copy(),
            metadata={
                'speed': float(speed),
                'on_target': on_target
            }
        )

    def _detect_out_of_bounds(
        self,
        current_time: float,
        ball_state: BallState,
        is_home_attacking_left: bool
    ) -> Optional[MatchEvent]:
        """Detect ball going out of bounds"""
        x, y, h = ball_state.position

        # Ball must be on ground
        if h > 1.0:
            return None

        # Check sidelines (throw-in)
        if y < FIELD_Y_MIN or y > FIELD_Y_MAX:
            return MatchEvent(
                event_type=EventType.THROW_IN,
                time=current_time,
                team='neutral',
                position=ball_state.position.copy(),
                metadata={'side': 'left' if y < 0 else 'right'}
            )

        # Check goal lines
        if x < FIELD_X_MIN or x > FIELD_X_MAX:
            # Determine if corner or goal kick
            # (simplified: random for now)
            if abs(y) > GOAL_Y_MAX / 2:
                event_type = EventType.CORNER
            else:
                event_type = EventType.GOAL_KICK

            return MatchEvent(
                event_type=event_type,
                time=current_time,
                team='neutral',
                position=ball_state.position.copy()
            )

        return None

    def _detect_possession_change(
        self,
        current_time: float,
        ball_state: BallState,
        home_players: List[PlayerState],
        away_players: List[PlayerState],
        home_player_ids: List[str],
        away_player_ids: List[str]
    ) -> Optional[MatchEvent]:
        """Detect possession change"""
        # Find closest player to ball
        closest_player = None
        closest_distance = float('inf')
        closest_team = None

        ball_pos = ball_state.position[:2]

        for i, player in enumerate(home_players):
            distance = distance_2d(player.position[0], player.position[1],
                                  ball_pos[0], ball_pos[1])
            if distance < closest_distance:
                closest_distance = distance
                closest_player = home_player_ids[i]
                closest_team = 'home'

        for i, player in enumerate(away_players):
            distance = distance_2d(player.position[0], player.position[1],
                                  ball_pos[0], ball_pos[1])
            if distance < closest_distance:
                closest_distance = distance
                closest_player = away_player_ids[i]
                closest_team = 'away'

        # Check if possession changed
        if closest_player and closest_player != self.last_ball_owner:
            old_owner = self.last_ball_owner
            self.last_ball_owner = closest_player

            # Only count as possession change if close enough (IMPROVED: 3.0m from 2.0m)
            if closest_distance < 3.0 and old_owner is not None:
                return MatchEvent(
                    event_type=EventType.POSSESSION_CHANGE,
                    time=current_time,
                    team=closest_team,
                    player_id=closest_player,
                    position=ball_state.position.copy()
                )

        return None

    def get_all_events(self) -> List[MatchEvent]:
        """Get all detected events"""
        return self.events

    def get_events_by_type(self, event_type: EventType) -> List[MatchEvent]:
        """Get events of specific type"""
        return [e for e in self.events if e.event_type == event_type]

    def get_events_by_team(self, team: str) -> List[MatchEvent]:
        """Get events for specific team"""
        return [e for e in self.events if e.team == team]

    def clear_events(self):
        """Clear all events"""
        self.events.clear()
        self.last_ball_owner = None
        self.last_shot_time = 0.0


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    'EventType',
    'MatchEvent',
    'EventDetector'
]
