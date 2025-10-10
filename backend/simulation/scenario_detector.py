# -*- coding: utf-8 -*-
"""
ScenarioDetector - Identify Game Scenarios

Part of Phase 2.0 Architecture Redesign
Detects current game scenario to apply appropriate logic

Scenarios:
- OPEN_MIDFIELD: Low density, space available
- CROWDED_MIDFIELD: High density, contested
- WING_PLAY: Near sideline
- PENALTY_BOX_ATTACK: Attacking in opponent's box
- PENALTY_BOX_DEFENSE: Defending own box
- COUNTER_ATTACK: Just won ball, space ahead
- ORGANIZED_DEFENSE: Team shape maintained
- PRESSING: Multiple defenders converging
- TRANSITION: Just lost/won ball
- AERIAL: Ball in air
- LOOSE_BALL: No clear possessor
"""

import numpy as np
from enum import Enum
from typing import Optional, Dict, List
from dataclasses import dataclass


class Scenario(Enum):
    """Game scenario types"""
    OPEN_MIDFIELD = "open_midfield"
    CROWDED_MIDFIELD = "crowded_midfield"
    WING_PLAY = "wing_play"
    PENALTY_BOX_ATTACK = "penalty_box_attack"
    PENALTY_BOX_DEFENSE = "penalty_box_defense"
    COUNTER_ATTACK = "counter_attack"
    ORGANIZED_DEFENSE = "organized_defense"
    PRESSING = "pressing"
    TRANSITION = "transition"
    AERIAL = "aerial"
    LOOSE_BALL = "loose_ball"


@dataclass
class ScenarioContext:
    """
    Context information about current scenario

    Provides additional details that may be useful for
    resolvers to make decisions
    """
    scenario: Scenario
    location: str  # 'defensive_third', 'midfield', 'attacking_third'
    density: int  # Number of players nearby
    pressure: float  # Pressure level (0.0 to 1.0+)
    space_ahead: float  # Space available in attack direction
    possession_team: Optional[str]  # 'home', 'away', or None
    is_transition: bool  # Just changed possession
    time_since_transition: float  # Seconds since last possession change


# Field zones (in meters from center)
# Field is 105m long (-52.5 to +52.5)
DEFENSIVE_THIRD_THRESHOLD = -35.0  # Own defensive third
ATTACKING_THIRD_THRESHOLD = 35.0   # Opponent's defensive third
WING_THRESHOLD = 20.0  # Distance from sideline (field is 68m wide, ±34m from center)
PENALTY_BOX_LENGTH = 16.5  # Standard penalty box is 16.5m from goal line
PENALTY_BOX_WIDTH = 20.15  # Standard penalty box width (40.3m total / 2)

# Density thresholds
LOW_DENSITY = 3   # ≤3 players in 10m radius
HIGH_DENSITY = 6  # ≥6 players in 10m radius

# Aerial threshold
AERIAL_HEIGHT_THRESHOLD = 2.0  # Ball above 2m considered aerial

# Pressing detection
PRESSING_CONVERGE_COUNT = 3  # 3+ defenders within 5m = pressing
PRESSING_RADIUS = 5.0

# Counter-attack detection
COUNTER_ATTACK_SPACE = 20.0  # 20m+ of space ahead
TRANSITION_TIME_LIMIT = 3.0  # 3 seconds after possession change


class ScenarioDetector:
    """
    Detects current game scenario

    Uses ball position, player positions, and recent history
    to identify the current game situation. This allows
    different resolvers and logic to be applied based on context.
    """

    def __init__(self):
        """Initialize scenario detector"""
        self.last_possessor = None
        self.time_since_transition = 0.0
        self.possession_history = []  # [(time, team)]

    def detect(self, ball_state: any, home_players: List[any],
               away_players: List[any], field_state: any,
               current_time: float = 0.0) -> ScenarioContext:
        """
        Detect current scenario

        Args:
            ball_state: Current ball state (position, velocity)
            home_players: List of home team player states
            away_players: List of away team player states
            field_state: FieldState object with spatial analysis
            current_time: Current simulation time

        Returns:
            ScenarioContext with detected scenario and metadata
        """
        # Get ball position
        ball_pos = ball_state.position
        ball_x, ball_y, ball_z = ball_pos[0], ball_pos[1], ball_pos[2]

        # Determine possession
        possession_team = self._determine_possession(
            ball_state, home_players, away_players
        )

        # Check for possession transition
        is_transition = False
        if possession_team != self.last_possessor and possession_team is not None:
            is_transition = True
            self.time_since_transition = 0.0
            self.possession_history.append((current_time, possession_team))
        else:
            self.time_since_transition += 0.1  # Assuming 0.1s tick

        self.last_possessor = possession_team

        # Get local density
        density_info = field_state.get_local_density(
            ball_pos, radius=10.0,
            home_players=home_players,
            away_players=away_players
        )
        density = density_info['total']

        # Get pressure on ball possessor
        pressure = 0.0
        if possession_team:
            possessing_players = home_players if possession_team == 'home' else away_players
            opponents = away_players if possession_team == 'home' else home_players

            # Find player with ball
            ball_holder = self._find_ball_holder(ball_state, possessing_players)
            if ball_holder:
                pressure = field_state.get_pressure_on_player(
                    ball_holder.position, opponents
                )

        # Determine field location
        location = self._determine_location(ball_x, possession_team)

        # Calculate space ahead
        space_ahead = self._calculate_space_ahead(
            ball_pos, possession_team, home_players, away_players
        )

        # PRIMARY SCENARIO DETECTION
        # Priority order: Aerial > Loose Ball > Penalty Box > Pressing > Counter-Attack > Midfield/Wing

        # 1. AERIAL - Ball in air
        if ball_z > AERIAL_HEIGHT_THRESHOLD:
            scenario = Scenario.AERIAL

        # 2. LOOSE_BALL - No clear possession
        elif possession_team is None:
            scenario = Scenario.LOOSE_BALL

        # 3. PENALTY_BOX - In penalty area
        elif self._is_in_penalty_box(ball_x, ball_y, possession_team):
            if possession_team == 'home':
                # Home attacking or defending?
                if ball_x > ATTACKING_THIRD_THRESHOLD:
                    scenario = Scenario.PENALTY_BOX_ATTACK
                else:
                    scenario = Scenario.PENALTY_BOX_DEFENSE
            else:  # away
                if ball_x < -ATTACKING_THIRD_THRESHOLD:
                    scenario = Scenario.PENALTY_BOX_ATTACK
                else:
                    scenario = Scenario.PENALTY_BOX_DEFENSE

        # 4. PRESSING - Multiple opponents converging
        elif self._is_pressing_scenario(ball_state, possession_team,
                                       home_players, away_players):
            scenario = Scenario.PRESSING

        # 5. COUNTER_ATTACK - Just won ball + space ahead
        elif (is_transition and
              self.time_since_transition < TRANSITION_TIME_LIMIT and
              space_ahead > COUNTER_ATTACK_SPACE):
            scenario = Scenario.COUNTER_ATTACK

        # 6. TRANSITION - Just changed possession (but no counter-attack)
        elif is_transition and self.time_since_transition < TRANSITION_TIME_LIMIT:
            scenario = Scenario.TRANSITION

        # 7. WING_PLAY - Near sideline
        elif abs(ball_y) > WING_THRESHOLD:
            scenario = Scenario.WING_PLAY

        # 8. MIDFIELD - Based on density
        elif density >= HIGH_DENSITY:
            scenario = Scenario.CROWDED_MIDFIELD
        elif density <= LOW_DENSITY:
            scenario = Scenario.OPEN_MIDFIELD
        else:
            # Medium density - default to organized defense if defending, open if attacking
            if location == 'defensive_third':
                scenario = Scenario.ORGANIZED_DEFENSE
            else:
                scenario = Scenario.OPEN_MIDFIELD

        # Build context
        context = ScenarioContext(
            scenario=scenario,
            location=location,
            density=density,
            pressure=pressure,
            space_ahead=space_ahead,
            possession_team=possession_team,
            is_transition=is_transition,
            time_since_transition=self.time_since_transition
        )

        return context

    def _determine_possession(self, ball_state: any,
                             home_players: List[any],
                             away_players: List[any]) -> Optional[str]:
        """
        Determine which team has possession

        Returns:
            'home', 'away', or None (loose ball)
        """
        CONTROL_RADIUS = 2.0  # Ball must be within 2m of player

        ball_pos = ball_state.position
        ball_x, ball_y, ball_z = ball_pos[0], ball_pos[1], ball_pos[2]

        # If ball is in air and high, no clear possession
        if ball_z > 1.0:
            return None

        # Check home team
        for player in home_players:
            dist = self._distance_2d(
                player.position[0], player.position[1],
                ball_x, ball_y
            )
            if dist < CONTROL_RADIUS:
                return 'home'

        # Check away team
        for player in away_players:
            dist = self._distance_2d(
                player.position[0], player.position[1],
                ball_x, ball_y
            )
            if dist < CONTROL_RADIUS:
                return 'away'

        # No one in control
        return None

    def _find_ball_holder(self, ball_state: any,
                         players: List[any]) -> Optional[any]:
        """Find player closest to ball (assumed to be holder)"""
        CONTROL_RADIUS = 2.0

        ball_pos = ball_state.position
        ball_x, ball_y = ball_pos[0], ball_pos[1]

        closest_player = None
        closest_dist = CONTROL_RADIUS

        for player in players:
            dist = self._distance_2d(
                player.position[0], player.position[1],
                ball_x, ball_y
            )
            if dist < closest_dist:
                closest_dist = dist
                closest_player = player

        return closest_player

    def _determine_location(self, ball_x: float,
                           possession_team: Optional[str]) -> str:
        """
        Determine field location relative to possession

        Returns:
            'defensive_third', 'midfield', 'attacking_third'
        """
        if possession_team == 'home':
            # Home attacks towards +X
            if ball_x < DEFENSIVE_THIRD_THRESHOLD:
                return 'defensive_third'
            elif ball_x > ATTACKING_THIRD_THRESHOLD:
                return 'attacking_third'
            else:
                return 'midfield'
        elif possession_team == 'away':
            # Away attacks towards -X
            if ball_x > -DEFENSIVE_THIRD_THRESHOLD:
                return 'defensive_third'
            elif ball_x < -ATTACKING_THIRD_THRESHOLD:
                return 'attacking_third'
            else:
                return 'midfield'
        else:
            # No possession - absolute location
            if abs(ball_x) > ATTACKING_THIRD_THRESHOLD:
                return 'attacking_third'  # Near a goal
            else:
                return 'midfield'

    def _is_in_penalty_box(self, ball_x: float, ball_y: float,
                           possession_team: Optional[str]) -> bool:
        """
        Check if ball is in a penalty box

        Penalty box:
        - 16.5m from goal line
        - 40.3m wide (±20.15m from center)
        """
        # Check if within width
        if abs(ball_y) > PENALTY_BOX_WIDTH:
            return False

        # Check home penalty box (at x = -52.5, goal line at -52.5)
        if ball_x < -52.5 + PENALTY_BOX_LENGTH:
            return True

        # Check away penalty box (at x = +52.5)
        if ball_x > 52.5 - PENALTY_BOX_LENGTH:
            return True

        return False

    def _is_pressing_scenario(self, ball_state: any,
                             possession_team: Optional[str],
                             home_players: List[any],
                             away_players: List[any]) -> bool:
        """
        Detect if defending team is pressing

        Pressing = 3+ opponents within 5m of ball
        """
        if possession_team is None:
            return False

        opponents = away_players if possession_team == 'home' else home_players

        ball_pos = ball_state.position
        ball_x, ball_y = ball_pos[0], ball_pos[1]

        # Count opponents within pressing radius
        pressing_count = 0
        for opponent in opponents:
            dist = self._distance_2d(
                opponent.position[0], opponent.position[1],
                ball_x, ball_y
            )
            if dist < PRESSING_RADIUS:
                pressing_count += 1

        return pressing_count >= PRESSING_CONVERGE_COUNT

    def _calculate_space_ahead(self, ball_pos: np.ndarray,
                              possession_team: Optional[str],
                              home_players: List[any],
                              away_players: List[any]) -> float:
        """
        Calculate space available in attack direction

        Returns:
            Distance in meters to nearest opponent ahead
        """
        if possession_team is None:
            return 0.0

        ball_x, ball_y = ball_pos[0], ball_pos[1]
        opponents = away_players if possession_team == 'home' else home_players

        # Attack direction
        attack_direction = 1.0 if possession_team == 'home' else -1.0

        # Find nearest opponent in attack direction
        min_distance = 100.0  # Large default

        for opponent in opponents:
            opp_x = opponent.position[0]
            opp_y = opponent.position[1]

            # Check if opponent is ahead
            if attack_direction > 0:
                ahead = opp_x > ball_x
            else:
                ahead = opp_x < ball_x

            if ahead:
                # Calculate distance (considering lateral position too)
                dx = abs(opp_x - ball_x)
                dy = abs(opp_y - ball_y)
                distance = np.sqrt(dx*dx + dy*dy)
                min_distance = min(min_distance, distance)

        return min_distance

    def _distance_2d(self, x1: float, y1: float, x2: float, y2: float) -> float:
        """Calculate 2D distance"""
        dx = x2 - x1
        dy = y2 - y1
        return np.sqrt(dx*dx + dy*dy)

    def get_scenario_description(self, context: ScenarioContext) -> str:
        """
        Get human-readable description of scenario

        Args:
            context: ScenarioContext object

        Returns:
            String description
        """
        desc_map = {
            Scenario.OPEN_MIDFIELD: "Open midfield - space available",
            Scenario.CROWDED_MIDFIELD: "Crowded midfield - contested",
            Scenario.WING_PLAY: "Wing play - near sideline",
            Scenario.PENALTY_BOX_ATTACK: "Penalty box attack - high pressure",
            Scenario.PENALTY_BOX_DEFENSE: "Defending penalty box - critical",
            Scenario.COUNTER_ATTACK: "Counter-attack - space ahead",
            Scenario.ORGANIZED_DEFENSE: "Organized defense - team shape",
            Scenario.PRESSING: "High press - multiple defenders converging",
            Scenario.TRANSITION: "Transition - just changed possession",
            Scenario.AERIAL: "Aerial duel - ball in air",
            Scenario.LOOSE_BALL: "Loose ball - no clear possession"
        }

        base = desc_map.get(context.scenario, "Unknown scenario")

        details = []
        details.append(f"Location: {context.location}")
        details.append(f"Density: {context.density} players nearby")
        details.append(f"Pressure: {context.pressure:.1f}")

        if context.possession_team:
            details.append(f"Possession: {context.possession_team.upper()}")

        if context.is_transition:
            details.append(f"TRANSITION ({context.time_since_transition:.1f}s ago)")

        return f"{base}\n  " + "\n  ".join(details)


# =============================================================================
# EXPORT
# =============================================================================

__all__ = ['ScenarioDetector', 'Scenario', 'ScenarioContext']
