# -*- coding: utf-8 -*-
"""
DribbleResolver - Realistic Dribble/1v1 Duel Resolution

Part of Phase 2.0 Architecture Redesign
Resolves dribble attempts with spatial influence calculation

Key Innovation:
- Models dribbler vs defender as influence contest
- Considers positioning, attributes, space, support
- Realistic outcomes: Success, Loose Ball, Tackled, Foul
- Multiple defenders create cumulative pressure

This directly addresses user feedback:
> "Dribble should consider: field location, direction, how many defenders,
   defender attributes, calculate influence (attacker vs defenders), outcome
   based on spatial contest not pure probability"
"""

import numpy as np
from enum import Enum
from typing import List, Optional, Tuple
from dataclasses import dataclass


class DribbleOutcomeType(Enum):
    """Possible dribble outcomes"""
    SUCCESS = "success"  # Beat defender, maintain possession
    LOOSE_BALL = "loose_ball"  # Lost control, ball loose nearby
    TACKLED = "tackled"  # Defender won ball cleanly
    FOUL = "foul"  # Defender fouled attacker


@dataclass
class DribbleOutcome:
    """
    Result of a dribble attempt

    Contains:
    - Outcome type
    - Ball position after dribble
    - Ball velocity
    - Tackler (if tackled)
    - Attacker win probability (for analysis)
    """
    outcome_type: DribbleOutcomeType
    ball_position: np.ndarray  # [x, y, z]
    ball_velocity: np.ndarray  # [vx, vy, vz]
    tackler: Optional[any] = None
    attacker_influence: float = 0.0
    defender_influence: float = 0.0
    win_probability: float = 0.0


class DribbleResolver:
    """
    Resolves dribble attempts (1v1 or 1vMany duels)

    This implements the user's vision:
    > "Two players exert influence on area, outcome based on who has
       stronger influence considering position, attributes, teammates nearby"

    Process:
    1. Find primary defender (closest)
    2. Calculate attacker influence (dribbling, agility, speed, space)
    3. Calculate defender influence (defending, speed, positioning, proximity)
    4. Add secondary pressure (other defenders nearby)
    5. Resolve based on influence ratio
    6. Return realistic outcome with ball trajectory
    """

    def __init__(self):
        """Initialize dribble resolver"""
        # Tuning parameters
        self.challenge_distance = 5.0  # Defender within 5m can challenge
        self.immediate_contest_distance = 2.0  # Within 2m = immediate contest
        self.space_bonus_range = 10.0  # Check space in 10m radius
        self.dribble_speed = 6.0  # m/s when dribbling successfully

    def resolve(self, attacker: any, defenders: List[any],
                field_state: any, scenario_context: any,
                dribble_direction: np.ndarray) -> DribbleOutcome:
        """
        Resolve a dribble attempt

        Args:
            attacker: Player attempting dribble
            defenders: List of opponent player states
            field_state: FieldState object
            scenario_context: ScenarioContext object
            dribble_direction: Direction attacker wants to go [x, y, z]

        Returns:
            DribbleOutcome with result and ball trajectory
        """
        attacker_pos = np.array(attacker.position)

        # 1. Find defenders in range
        nearby_defenders = self._find_nearby_defenders(
            attacker_pos, defenders, self.challenge_distance
        )

        # If no defenders nearby - free dribble!
        if len(nearby_defenders) == 0:
            return self._create_success_outcome(
                attacker_pos, dribble_direction, self.dribble_speed,
                attacker_influence=1.0, defender_influence=0.0, win_prob=1.0
            )

        # 2. Find primary challenger (closest)
        primary_defender = self._find_primary_defender(attacker_pos, nearby_defenders)
        distance_to_primary = self._distance_3d(
            attacker_pos, np.array(primary_defender.position)
        )

        # 3. Calculate attacker influence
        attacker_influence = self._calculate_attacker_influence(
            attacker, attacker_pos, dribble_direction,
            field_state, scenario_context
        )

        # 4. Calculate primary defender influence
        defender_influence = self._calculate_defender_influence(
            primary_defender, attacker_pos, distance_to_primary,
            field_state, scenario_context
        )

        # 5. Add secondary pressure from other defenders
        secondary_defenders = [d for d in nearby_defenders if d != primary_defender]
        secondary_pressure = self._calculate_secondary_pressure(
            attacker_pos, secondary_defenders
        )
        defender_influence += secondary_pressure

        # 6. Calculate win probabilities
        total_influence = attacker_influence + defender_influence
        if total_influence < 0.001:
            # Edge case
            attacker_win_prob = 0.5
        else:
            attacker_win_prob = attacker_influence / total_influence

        # 7. Resolve outcome based on probabilities
        return self._resolve_outcome(
            attacker, primary_defender, attacker_pos, dribble_direction,
            attacker_win_prob, attacker_influence, defender_influence,
            distance_to_primary
        )

    def _find_nearby_defenders(self, attacker_pos: np.ndarray,
                              defenders: List[any],
                              max_distance: float) -> List[any]:
        """Find all defenders within challenge distance"""
        nearby = []
        for defender in defenders:
            dist = self._distance_3d(attacker_pos, np.array(defender.position))
            if dist < max_distance:
                nearby.append(defender)
        return nearby

    def _find_primary_defender(self, attacker_pos: np.ndarray,
                              defenders: List[any]) -> any:
        """Find closest defender (primary challenger)"""
        closest = None
        min_dist = float('inf')

        for defender in defenders:
            dist = self._distance_3d(attacker_pos, np.array(defender.position))
            if dist < min_dist:
                min_dist = dist
                closest = defender

        return closest

    def _calculate_attacker_influence(self, attacker: any,
                                     attacker_pos: np.ndarray,
                                     dribble_direction: np.ndarray,
                                     field_state: any,
                                     scenario_context: any) -> float:
        """
        Calculate attacker's influence in the dribble contest

        Factors:
        - Dribbling attribute (35%)
        - Agility attribute (20%)
        - Speed attribute (20%)
        - Space available in dribble direction (15%)
        - Scenario modifier (10%)
        """
        # 1. Dribbling skill (35% weight)
        dribbling = 70.0  # Default
        if hasattr(attacker, 'attributes') and hasattr(attacker.attributes, 'dribbling'):
            dribbling = attacker.attributes.dribbling
        dribbling_factor = dribbling / 100.0

        # 2. Agility (20% weight)
        agility = 70.0  # Default
        if hasattr(attacker, 'attributes') and hasattr(attacker.attributes, 'agility'):
            agility = attacker.attributes.agility
        agility_factor = agility / 100.0

        # 3. Speed (20% weight)
        speed = 70.0  # Default
        if hasattr(attacker, 'attributes') and hasattr(attacker.attributes, 'speed'):
            speed = attacker.attributes.speed
        speed_factor = speed / 100.0

        # 4. Space available (15% weight)
        # More space = easier to dribble
        space = field_state.get_space_available(
            attacker_pos, dribble_direction,
            opponents=[],  # Will check in FieldState
            distance=self.space_bonus_range
        )
        space_factor = space  # Already 0.0 to 1.0

        # 5. Scenario modifier (10% weight)
        scenario_mod = self._get_attacker_scenario_modifier(scenario_context)

        # Combine factors
        influence = (
            dribbling_factor * 0.35 +
            agility_factor * 0.20 +
            speed_factor * 0.20 +
            space_factor * 0.15 +
            scenario_mod * 0.10
        )

        return influence

    def _calculate_defender_influence(self, defender: any,
                                     attacker_pos: np.ndarray,
                                     distance: float,
                                     field_state: any,
                                     scenario_context: any) -> float:
        """
        Calculate defender's influence in the dribble contest

        Factors:
        - Defending attribute (35%)
        - Speed attribute (20%)
        - Positioning/anticipation (20%)
        - Proximity bonus (15%)
        - Scenario modifier (10%)
        """
        # 1. Defending skill (35% weight)
        defending = 70.0  # Default
        if hasattr(defender, 'attributes') and hasattr(defender.attributes, 'defending'):
            defending = defender.attributes.defending
        defending_factor = defending / 100.0

        # 2. Speed (20% weight)
        speed = 70.0  # Default
        if hasattr(defender, 'attributes') and hasattr(defender.attributes, 'speed'):
            speed = defender.attributes.speed
        speed_factor = speed / 100.0

        # 3. Positioning (20% weight)
        positioning = 70.0  # Default
        if hasattr(defender, 'attributes') and hasattr(defender.attributes, 'positioning'):
            positioning = defender.attributes.positioning
        positioning_factor = positioning / 100.0

        # 4. Proximity bonus (15% weight)
        # Closer = stronger influence (inverse relationship)
        # 0m = 1.0, 5m = 0.0
        proximity_factor = 1.0 - (distance / self.challenge_distance)
        proximity_factor = np.clip(proximity_factor, 0.0, 1.0)

        # 5. Scenario modifier (10% weight)
        scenario_mod = self._get_defender_scenario_modifier(scenario_context)

        # Combine factors
        influence = (
            defending_factor * 0.35 +
            speed_factor * 0.20 +
            positioning_factor * 0.20 +
            proximity_factor * 0.15 +
            scenario_mod * 0.10
        )

        return influence

    def _calculate_secondary_pressure(self, attacker_pos: np.ndarray,
                                     secondary_defenders: List[any]) -> float:
        """
        Calculate additional pressure from nearby defenders

        Each secondary defender within 5m adds bonus to defender influence
        """
        pressure = 0.0

        for defender in secondary_defenders:
            dist = self._distance_3d(attacker_pos, np.array(defender.position))
            if dist < self.challenge_distance:
                # Each defender adds pressure (diminishing)
                contribution = 0.1 * (1.0 - dist / self.challenge_distance)
                pressure += contribution

        return pressure

    def _get_attacker_scenario_modifier(self, scenario_context: any) -> float:
        """
        Get attacker advantage based on scenario

        Open space = easier to dribble
        Crowded = harder
        """
        from backend.simulation.scenario_detector import Scenario

        scenario = scenario_context.scenario

        modifiers = {
            Scenario.OPEN_MIDFIELD: 0.9,  # Good space
            Scenario.CROWDED_MIDFIELD: 0.5,  # Very hard when crowded
            Scenario.WING_PLAY: 0.8,  # Decent (1v1 opportunity)
            Scenario.PENALTY_BOX_ATTACK: 0.6,  # Hard in box
            Scenario.PENALTY_BOX_DEFENSE: 0.7,  # Moderate
            Scenario.COUNTER_ATTACK: 1.0,  # Excellent (space)
            Scenario.ORGANIZED_DEFENSE: 0.6,  # Hard vs organized
            Scenario.PRESSING: 0.4,  # Very hard under press
            Scenario.TRANSITION: 0.7,  # Moderate
            Scenario.AERIAL: 0.5,  # N/A
            Scenario.LOOSE_BALL: 0.5  # N/A
        }

        return modifiers.get(scenario, 0.7)

    def _get_defender_scenario_modifier(self, scenario_context: any) -> float:
        """
        Get defender advantage based on scenario

        Organized defense = easier to defend
        Open space = harder
        """
        from backend.simulation.scenario_detector import Scenario

        scenario = scenario_context.scenario

        modifiers = {
            Scenario.OPEN_MIDFIELD: 0.6,  # Hard to defend in space
            Scenario.CROWDED_MIDFIELD: 0.9,  # Easy to defend when crowded
            Scenario.WING_PLAY: 0.7,  # Moderate
            Scenario.PENALTY_BOX_ATTACK: 0.8,  # Easier in crowded box
            Scenario.PENALTY_BOX_DEFENSE: 0.9,  # Very important to win
            Scenario.COUNTER_ATTACK: 0.5,  # Hard to catch attacker
            Scenario.ORGANIZED_DEFENSE: 0.9,  # Good support
            Scenario.PRESSING: 1.0,  # Excellent (team press)
            Scenario.TRANSITION: 0.6,  # Harder in chaos
            Scenario.AERIAL: 0.5,  # N/A
            Scenario.LOOSE_BALL: 0.5  # N/A
        }

        return modifiers.get(scenario, 0.7)

    def _resolve_outcome(self, attacker: any, defender: any,
                        attacker_pos: np.ndarray,
                        dribble_direction: np.ndarray,
                        attacker_win_prob: float,
                        attacker_influence: float,
                        defender_influence: float,
                        distance: float) -> DribbleOutcome:
        """
        Resolve dribble outcome based on probabilities

        Outcome distribution:
        - If attacker wins strongly (>70%): Success
        - If attacker wins moderately (50-70%): Success or Loose Ball
        - If close contest (40-60%): Loose Ball or Foul
        - If defender wins (< 40%): Tackled or Foul
        """
        roll = np.random.random()

        # Very close contest = higher foul chance
        contest_closeness = abs(attacker_win_prob - 0.5) / 0.5  # 0.0 = very close, 1.0 = one-sided
        foul_chance_bonus = (1.0 - contest_closeness) * 0.15  # Up to 15% bonus for close contests

        # Immediate contest (very close) = more likely to be physical
        if distance < self.immediate_contest_distance:
            foul_chance_bonus += 0.10

        # Outcome thresholds
        if attacker_win_prob > 0.7:
            # Attacker dominant
            if roll < 0.85:
                return self._create_success_outcome(
                    attacker_pos, dribble_direction, self.dribble_speed,
                    attacker_influence, defender_influence, attacker_win_prob
                )
            elif roll < 0.95:
                return self._create_loose_ball_outcome(
                    attacker_pos, dribble_direction, self.dribble_speed * 0.7,
                    attacker_influence, defender_influence, attacker_win_prob
                )
            else:
                return self._create_foul_outcome(
                    defender, attacker_pos,
                    attacker_influence, defender_influence, attacker_win_prob
                )

        elif attacker_win_prob >= 0.5:
            # Attacker slight advantage
            success_threshold = 0.50
            loose_threshold = 0.85
            foul_threshold = 0.85 + foul_chance_bonus

            if roll < success_threshold:
                return self._create_success_outcome(
                    attacker_pos, dribble_direction, self.dribble_speed,
                    attacker_influence, defender_influence, attacker_win_prob
                )
            elif roll < loose_threshold:
                return self._create_loose_ball_outcome(
                    attacker_pos, dribble_direction, self.dribble_speed * 0.6,
                    attacker_influence, defender_influence, attacker_win_prob
                )
            elif roll < foul_threshold:
                return self._create_foul_outcome(
                    defender, attacker_pos,
                    attacker_influence, defender_influence, attacker_win_prob
                )
            else:
                return self._create_tackled_outcome(
                    defender, attacker_pos,
                    attacker_influence, defender_influence, attacker_win_prob
                )

        elif attacker_win_prob >= 0.3:
            # Defender slight advantage
            success_threshold = 0.20
            loose_threshold = 0.50
            foul_threshold = 0.50 + foul_chance_bonus

            if roll < success_threshold:
                return self._create_success_outcome(
                    attacker_pos, dribble_direction, self.dribble_speed * 0.8,
                    attacker_influence, defender_influence, attacker_win_prob
                )
            elif roll < loose_threshold:
                return self._create_loose_ball_outcome(
                    attacker_pos, dribble_direction, self.dribble_speed * 0.5,
                    attacker_influence, defender_influence, attacker_win_prob
                )
            elif roll < foul_threshold:
                return self._create_foul_outcome(
                    defender, attacker_pos,
                    attacker_influence, defender_influence, attacker_win_prob
                )
            else:
                return self._create_tackled_outcome(
                    defender, attacker_pos,
                    attacker_influence, defender_influence, attacker_win_prob
                )

        else:
            # Defender dominant
            foul_threshold = 0.10 + foul_chance_bonus

            if roll < foul_threshold:
                return self._create_foul_outcome(
                    defender, attacker_pos,
                    attacker_influence, defender_influence, attacker_win_prob
                )
            elif roll < 0.25:
                return self._create_loose_ball_outcome(
                    attacker_pos, dribble_direction, self.dribble_speed * 0.4,
                    attacker_influence, defender_influence, attacker_win_prob
                )
            else:
                return self._create_tackled_outcome(
                    defender, attacker_pos,
                    attacker_influence, defender_influence, attacker_win_prob
                )

    def _create_success_outcome(self, attacker_pos: np.ndarray,
                               direction: np.ndarray, speed: float,
                               attacker_inf: float, defender_inf: float,
                               win_prob: float) -> DribbleOutcome:
        """Create successful dribble outcome"""
        # Normalize direction
        if np.linalg.norm(direction) > 0.001:
            direction = direction / np.linalg.norm(direction)

        # Ball moves ahead of attacker
        new_pos = attacker_pos + direction * 2.0  # 2m ahead
        velocity = direction * speed

        return DribbleOutcome(
            outcome_type=DribbleOutcomeType.SUCCESS,
            ball_position=new_pos,
            ball_velocity=velocity,
            tackler=None,
            attacker_influence=attacker_inf,
            defender_influence=defender_inf,
            win_probability=win_prob
        )

    def _create_loose_ball_outcome(self, attacker_pos: np.ndarray,
                                  direction: np.ndarray, speed: float,
                                  attacker_inf: float, defender_inf: float,
                                  win_prob: float) -> DribbleOutcome:
        """Create loose ball outcome (both can contest)"""
        # Normalize direction
        if np.linalg.norm(direction) > 0.001:
            direction = direction / np.linalg.norm(direction)

        # Ball gets away slightly
        error = np.random.uniform(-0.3, 0.3)  # Small angle error
        cos_e = np.cos(error)
        sin_e = np.sin(error)
        dx, dy = direction[0], direction[1]
        new_dx = dx * cos_e - dy * sin_e
        new_dy = dx * sin_e + dy * cos_e
        error_direction = np.array([new_dx, new_dy, 0])

        new_pos = attacker_pos + error_direction * 2.5  # 2.5m away
        velocity = error_direction * speed

        return DribbleOutcome(
            outcome_type=DribbleOutcomeType.LOOSE_BALL,
            ball_position=new_pos,
            ball_velocity=velocity,
            tackler=None,
            attacker_influence=attacker_inf,
            defender_influence=defender_inf,
            win_probability=win_prob
        )

    def _create_tackled_outcome(self, defender: any, attacker_pos: np.ndarray,
                               attacker_inf: float, defender_inf: float,
                               win_prob: float) -> DribbleOutcome:
        """Create tackled outcome (defender wins ball)"""
        # Ball goes to defender
        defender_pos = np.array(defender.position)

        # Ball velocity towards defender
        direction = defender_pos - attacker_pos
        if np.linalg.norm(direction) > 0.001:
            direction = direction / np.linalg.norm(direction)

        velocity = direction * 3.0  # Slow speed after tackle

        return DribbleOutcome(
            outcome_type=DribbleOutcomeType.TACKLED,
            ball_position=defender_pos,
            ball_velocity=velocity,
            tackler=defender,
            attacker_influence=attacker_inf,
            defender_influence=defender_inf,
            win_probability=win_prob
        )

    def _create_foul_outcome(self, defender: any, attacker_pos: np.ndarray,
                            attacker_inf: float, defender_inf: float,
                            win_prob: float) -> DribbleOutcome:
        """Create foul outcome (free kick)"""
        # Ball stays near attacker (dead ball)
        velocity = np.array([0, 0, 0])

        return DribbleOutcome(
            outcome_type=DribbleOutcomeType.FOUL,
            ball_position=attacker_pos.copy(),
            ball_velocity=velocity,
            tackler=defender,
            attacker_influence=attacker_inf,
            defender_influence=defender_inf,
            win_probability=win_prob
        )

    def _distance_3d(self, pos1: np.ndarray, pos2: np.ndarray) -> float:
        """Calculate 3D distance"""
        return np.linalg.norm(pos2 - pos1)


# =============================================================================
# EXPORT
# =============================================================================

__all__ = ['DribbleResolver', 'DribbleOutcome', 'DribbleOutcomeType']
