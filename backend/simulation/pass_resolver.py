# -*- coding: utf-8 -*-
"""
PassResolver - Realistic Pass Resolution with Interception

Part of Phase 2.0 Architecture Redesign
Resolves pass attempts with spatial awareness and realistic interception

Key Innovation:
- Analyzes passing lane for opponents
- Calculates interception probability for each opponent in lane
- Considers distance, positioning, attributes, ball speed
- Realistic outcomes: Success, Intercepted, Loose Ball, Out of Bounds
"""

import numpy as np
from enum import Enum
from typing import Optional, List, Tuple
from dataclasses import dataclass


class PassOutcomeType(Enum):
    """Possible pass outcomes"""
    SUCCESS = "success"  # Pass completed to target
    INTERCEPTED = "intercepted"  # Opponent intercepted
    LOOSE_BALL = "loose_ball"  # Failed, ball loose
    OUT_OF_BOUNDS = "out_of_bounds"  # Went off field
    TOO_LONG = "too_long"  # Overhit pass


@dataclass
class PassOutcome:
    """
    Result of a pass attempt

    Contains:
    - Outcome type
    - Target position (where ball ends up)
    - Ball velocity
    - Interceptor (if intercepted)
    - Success probability (for analysis)
    """
    outcome_type: PassOutcomeType
    ball_target: np.ndarray  # [x, y, z]
    ball_velocity: np.ndarray  # [vx, vy, vz]
    interceptor: Optional[any] = None
    success_probability: float = 0.0
    interception_probability: float = 0.0


class PassResolver:
    """
    Resolves pass attempts with spatial awareness

    This is the CRITICAL component that addresses the user's feedback:
    > "You need to consider which defenders are where, passing lanes,
       spatial influence - not just random success probability!"

    Process:
    1. Analyze passing lane (opponents in path)
    2. Calculate base pass success (distance, passer skill, pressure)
    3. For each opponent in lane: calculate interception chance
    4. Roll for interception first (realistic - defenders react)
    5. If no interception: roll for completion
    6. Return realistic outcome with ball trajectory
    """

    def __init__(self):
        """Initialize pass resolver"""
        # Tuning parameters
        self.intercept_max_distance = 3.0  # 3m from lane to attempt intercept
        self.max_pass_distance = 50.0  # Realistic max pass distance
        self.min_ball_speed = 8.0  # m/s
        self.max_ball_speed = 25.0  # m/s

    def resolve(self, passer: any, target_player: any,
                opponents: List[any], field_state: any,
                scenario_context: any, power: float = 80.0) -> PassOutcome:
        """
        Resolve a pass attempt

        Args:
            passer: Player making the pass
            target_player: Intended receiver
            opponents: List of opponent player states
            field_state: FieldState object
            scenario_context: ScenarioContext object
            power: Pass power (0-100)

        Returns:
            PassOutcome with result and ball trajectory
        """
        # 1. Calculate pass parameters
        passer_pos = np.array(passer.position)
        target_pos = np.array(target_player.position)

        distance = np.linalg.norm(target_pos[:2] - passer_pos[:2])
        direction = (target_pos - passer_pos)
        if np.linalg.norm(direction) > 0.001:
            direction = direction / np.linalg.norm(direction)
        else:
            # Degenerate case - pass to self
            return self._create_loose_ball_outcome(passer_pos, np.array([0, 0, 0]))

        # 2. Calculate ball speed based on distance and power
        ball_speed = self._calculate_ball_speed(distance, power)

        # 3. Analyze passing lane
        passing_lane = field_state.analyze_passing_lane(
            passer_pos, target_pos, opponents
        )

        # 4. Calculate base success probability
        base_success = self._calculate_base_success(
            passer, target_player, distance, passing_lane,
            field_state, scenario_context
        )

        # 5. Check for interceptions (MOST IMPORTANT)
        # Each opponent in lane gets a chance to intercept
        for opponent in passing_lane.interceptors:
            intercept_prob = self._calculate_intercept_probability(
                opponent, passer_pos, target_pos, ball_speed,
                distance, field_state
            )

            # Roll for interception
            if np.random.random() < intercept_prob:
                # INTERCEPTED!
                return self._create_intercepted_outcome(
                    opponent, passer_pos, target_pos, ball_speed,
                    base_success, intercept_prob
                )

        # 6. No interception - check if pass completes
        if np.random.random() < base_success:
            # SUCCESS!
            return self._create_success_outcome(
                target_pos, direction, ball_speed,
                base_success
            )
        else:
            # FAILED - inaccurate pass creates loose ball
            return self._create_failed_pass_outcome(
                passer_pos, target_pos, direction, ball_speed,
                base_success
            )

    def _calculate_ball_speed(self, distance: float, power: float) -> float:
        """
        Calculate ball speed based on pass distance and power

        Args:
            distance: Pass distance in meters
            power: Pass power (0-100)

        Returns:
            Ball speed in m/s
        """
        # Base speed from power
        power_speed = self.min_ball_speed + (
            (power / 100.0) * (self.max_ball_speed - self.min_ball_speed)
        )

        # Adjust for distance (longer passes need more power)
        distance_factor = min(1.0, distance / 30.0)  # Normalize to 30m
        required_speed = self.min_ball_speed + distance_factor * (self.max_ball_speed - self.min_ball_speed)

        # Use higher of power-based and distance-required
        return max(power_speed, required_speed * 0.8)  # 80% of required minimum

    def _calculate_base_success(self, passer: any, receiver: any,
                                distance: float, passing_lane: any,
                                field_state: any, scenario_context: any) -> float:
        """
        Calculate base pass success probability

        Factors:
        - Passer passing attribute
        - Distance (longer = harder)
        - Pressure on passer
        - Scenario (penalty box = harder, open field = easier)
        - Number of defenders in lane
        """
        # 1. Passer skill (40% weight)
        passing_attr = 70.0  # Default
        if hasattr(passer, 'attributes') and hasattr(passer.attributes, 'passing'):
            passing_attr = passer.attributes.passing
        skill_factor = passing_attr / 100.0

        # 2. Distance factor (30% weight)
        # Optimal: 5-15m (100% success)
        # Harder: <5m or >15m
        # Very hard: >30m
        if distance < 5:
            distance_factor = 0.7 + (distance / 5.0) * 0.3
        elif distance <= 15:
            distance_factor = 1.0
        elif distance <= 30:
            distance_factor = 1.0 - ((distance - 15) / 15) * 0.3
        else:
            distance_factor = 0.5 - ((distance - 30) / 20) * 0.3
            distance_factor = max(0.2, distance_factor)

        # 3. Pressure factor (20% weight)
        pressure = field_state.get_pressure_on_player(
            np.array(passer.position), []  # Will be calculated in FieldState
        )
        pressure_factor = 1.0 - min(0.5, pressure * 0.15)

        # 4. Lane clarity (10% weight)
        lane_factor = 1.0 - (passing_lane.risk * 0.5)

        # 5. Scenario modifier
        scenario_mod = self._get_scenario_modifier(scenario_context)

        # Combine factors
        base_success = (
            skill_factor * 0.40 +
            distance_factor * 0.30 +
            pressure_factor * 0.20 +
            lane_factor * 0.10
        ) * scenario_mod

        # Clamp to reasonable range
        return np.clip(base_success, 0.1, 0.95)

    def _calculate_intercept_probability(self, opponent: any,
                                         passer_pos: np.ndarray,
                                         target_pos: np.ndarray,
                                         ball_speed: float,
                                         pass_distance: float,
                                         field_state: any) -> float:
        """
        Calculate opponent's interception probability

        This is the CORE of realistic pass resolution.

        Factors:
        - Distance from passing lane (closer = better)
        - Position along lane (ahead of ball = better)
        - Interception attribute
        - Ball speed (faster = harder to intercept)
        - Reaction time
        """
        opp_pos = np.array(opponent.position[:2])
        p1 = passer_pos[:2]
        p2 = target_pos[:2]

        # 1. Distance from lane
        lane_distance = self._point_to_line_distance(opp_pos, p1, p2)

        if lane_distance > self.intercept_max_distance:
            return 0.0  # Too far to intercept

        # Distance factor (0.0 to 1.0)
        # 0m from lane = 1.0, 3m from lane = 0.0
        distance_factor = 1.0 - (lane_distance / self.intercept_max_distance)

        # 2. Position along lane
        # Ahead of ball = better, behind = worse
        projection = self._project_point_on_line(opp_pos, p1, p2)
        projection = np.clip(projection, 0.0, 1.0)

        # Position factor (0.5 to 1.0)
        # At 0% (near passer) = 0.5
        # At 50% (midpoint) = 1.0
        # At 100% (near receiver) = 0.8
        if projection <= 0.5:
            position_factor = 0.5 + projection
        else:
            position_factor = 1.0 - (projection - 0.5) * 0.4

        # 3. Interception attribute (35% weight)
        intercept_attr = 70.0  # Default
        if hasattr(opponent, 'attributes') and hasattr(opponent.attributes, 'interception'):
            intercept_attr = opponent.attributes.interception
        attr_factor = intercept_attr / 100.0

        # 4. Ball speed factor (faster = harder)
        # 10 m/s = easy (1.0)
        # 25 m/s = hard (0.5)
        speed_factor = 1.0 - ((ball_speed - self.min_ball_speed) /
                              (self.max_ball_speed - self.min_ball_speed)) * 0.5

        # 5. Reaction time based on distance
        # Time ball takes to reach interception point
        ball_travel_time = (pass_distance * projection) / ball_speed

        # Time opponent needs to reach interception point
        opponent_distance_to_intercept = lane_distance
        opponent_speed = 7.0  # m/s default
        if hasattr(opponent, 'attributes') and hasattr(opponent.attributes, 'speed'):
            opponent_speed = (opponent.attributes.speed / 100.0) * 10.0  # Scale to m/s

        opponent_time_needed = opponent_distance_to_intercept / opponent_speed

        # Can opponent reach in time?
        if opponent_time_needed > ball_travel_time:
            time_factor = 0.3  # Unlikely but possible with anticipation
        else:
            time_factor = 1.0 - (opponent_time_needed / ball_travel_time) * 0.5

        # Combine factors
        intercept_prob = (
            distance_factor * 0.30 +
            position_factor * 0.20 +
            attr_factor * 0.35 +
            speed_factor * 0.10 +
            time_factor * 0.05
        )

        # Clamp
        return np.clip(intercept_prob, 0.0, 0.90)

    def _get_scenario_modifier(self, scenario_context: any) -> float:
        """
        Get pass success modifier based on scenario

        Different scenarios have different base pass success rates
        """
        from backend.simulation.scenario_detector import Scenario

        scenario = scenario_context.scenario

        modifiers = {
            Scenario.OPEN_MIDFIELD: 1.2,  # Easier in open space
            Scenario.CROWDED_MIDFIELD: 0.8,  # Harder when crowded
            Scenario.WING_PLAY: 1.0,  # Normal
            Scenario.PENALTY_BOX_ATTACK: 0.7,  # Very hard in box
            Scenario.PENALTY_BOX_DEFENSE: 0.8,  # Hard defending
            Scenario.COUNTER_ATTACK: 1.1,  # Easier when space ahead
            Scenario.ORGANIZED_DEFENSE: 0.9,  # Harder vs organized defense
            Scenario.PRESSING: 0.6,  # Very hard under press
            Scenario.TRANSITION: 0.9,  # Harder in chaos
            Scenario.AERIAL: 0.8,  # N/A for ground passes
            Scenario.LOOSE_BALL: 0.8  # N/A
        }

        return modifiers.get(scenario, 1.0)

    def _create_success_outcome(self, target_pos: np.ndarray,
                               direction: np.ndarray, ball_speed: float,
                               success_prob: float) -> PassOutcome:
        """Create a successful pass outcome"""
        # Ball velocity towards target
        velocity = direction * ball_speed

        return PassOutcome(
            outcome_type=PassOutcomeType.SUCCESS,
            ball_target=target_pos.copy(),
            ball_velocity=velocity,
            interceptor=None,
            success_probability=success_prob,
            interception_probability=0.0
        )

    def _create_intercepted_outcome(self, interceptor: any,
                                   passer_pos: np.ndarray,
                                   target_pos: np.ndarray,
                                   ball_speed: float,
                                   success_prob: float,
                                   intercept_prob: float) -> PassOutcome:
        """Create an intercepted pass outcome"""
        # Ball ends up at interceptor position
        intercept_pos = np.array(interceptor.position).copy()

        # Ball velocity reduced (interception slows ball)
        direction = (target_pos - passer_pos)
        if np.linalg.norm(direction) > 0.001:
            direction = direction / np.linalg.norm(direction)

        velocity = direction * (ball_speed * 0.3)  # Reduced speed after intercept

        return PassOutcome(
            outcome_type=PassOutcomeType.INTERCEPTED,
            ball_target=intercept_pos,
            ball_velocity=velocity,
            interceptor=interceptor,
            success_probability=success_prob,
            interception_probability=intercept_prob
        )

    def _create_failed_pass_outcome(self, passer_pos: np.ndarray,
                                   target_pos: np.ndarray,
                                   direction: np.ndarray,
                                   ball_speed: float,
                                   success_prob: float) -> PassOutcome:
        """
        Create a failed pass outcome (inaccurate, becomes loose ball)

        Failed passes go in roughly the right direction but with error
        """
        # Calculate error (worse success = more error)
        max_angle_error = np.pi / 6  # 30 degrees max
        angle_error = (1.0 - success_prob) * max_angle_error
        actual_error = np.random.uniform(-angle_error, angle_error)

        # Rotate direction
        cos_e = np.cos(actual_error)
        sin_e = np.sin(actual_error)
        dx, dy = direction[0], direction[1]
        new_dx = dx * cos_e - dy * sin_e
        new_dy = dx * sin_e + dy * cos_e
        error_direction = np.array([new_dx, new_dy, 0])

        # Ball travels some distance (60-90% of intended)
        travel_factor = np.random.uniform(0.6, 0.9)
        distance = np.linalg.norm(target_pos[:2] - passer_pos[:2])
        ball_target = passer_pos + error_direction * distance * travel_factor

        # Reduced speed
        velocity = error_direction * ball_speed * 0.6

        return PassOutcome(
            outcome_type=PassOutcomeType.LOOSE_BALL,
            ball_target=ball_target,
            ball_velocity=velocity,
            interceptor=None,
            success_probability=success_prob,
            interception_probability=0.0
        )

    def _create_loose_ball_outcome(self, position: np.ndarray,
                                  velocity: np.ndarray) -> PassOutcome:
        """Create a loose ball outcome"""
        return PassOutcome(
            outcome_type=PassOutcomeType.LOOSE_BALL,
            ball_target=position.copy(),
            ball_velocity=velocity,
            interceptor=None,
            success_probability=0.0,
            interception_probability=0.0
        )

    def _point_to_line_distance(self, point: np.ndarray,
                               line_start: np.ndarray,
                               line_end: np.ndarray) -> float:
        """Calculate perpendicular distance from point to line segment"""
        line_vec = line_end - line_start
        line_len = np.linalg.norm(line_vec)

        if line_len < 0.001:
            return np.linalg.norm(point - line_start)

        line_dir = line_vec / line_len
        start_to_point = point - line_start
        projection = np.dot(start_to_point, line_dir)

        if projection < 0:
            closest = line_start
        elif projection > line_len:
            closest = line_end
        else:
            closest = line_start + line_dir * projection

        return np.linalg.norm(point - closest)

    def _project_point_on_line(self, point: np.ndarray,
                              line_start: np.ndarray,
                              line_end: np.ndarray) -> float:
        """
        Project point onto line and return normalized position

        Returns:
            0.0 = at line_start, 1.0 = at line_end
        """
        line_vec = line_end - line_start
        line_len = np.linalg.norm(line_vec)

        if line_len < 0.001:
            return 0.0

        line_dir = line_vec / line_len
        start_to_point = point - line_start
        projection = np.dot(start_to_point, line_dir)

        return np.clip(projection / line_len, 0.0, 1.0)


# =============================================================================
# EXPORT
# =============================================================================

__all__ = ['PassResolver', 'PassOutcome', 'PassOutcomeType']
