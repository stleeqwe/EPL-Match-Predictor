# -*- coding: utf-8 -*-
"""
Simple Rule-Based Agent
Handles 80% of decisions without LLM calls

Decision tree based on:
- Ball possession
- Position on field
- Distance to goal/ball
- Teammate/opponent positions
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .actions import (
    Action, ActionType,
    is_in_shooting_range,
    calculate_pass_power,
    calculate_shot_direction
)

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from physics.constants import (
    FIELD_X_MIN, FIELD_X_MAX, FIELD_Y_MIN, FIELD_Y_MAX,
    GOAL_Y_MIN, GOAL_Y_MAX,
    PLAYER_CONTROL_RADIUS,
    SHOOTING_RANGE_MAX, SHOOTING_RANGE_OPTIMAL,
    PASSING_RANGE_SHORT, PASSING_RANGE_MEDIUM,
    distance_2d
)


@dataclass
class PlayerGameState:
    """
    Player's current game state for decision-making

    Attributes:
        player_id: Unique player identifier
        position: Current position [x, y]
        velocity: Current velocity [vx, vy]
        stamina: Current stamina (0-100)
        has_ball: Whether player has ball possession
        team_id: Team identifier ('home' or 'away')
        role: Position role (GK, CB, FB, DM, CM, CAM, WG, ST)
        attributes: Player technical attributes (pace, shooting, passing, etc.)
    """
    player_id: str
    position: np.ndarray
    velocity: np.ndarray
    stamina: float
    has_ball: bool
    team_id: str
    role: str
    attributes: Dict[str, float]

    def __post_init__(self):
        """Ensure numpy arrays"""
        if not isinstance(self.position, np.ndarray):
            self.position = np.array(self.position, dtype=float)
        if not isinstance(self.velocity, np.ndarray):
            self.velocity = np.array(self.velocity, dtype=float)


@dataclass
class GameContext:
    """
    Current game context for decision-making

    Attributes:
        ball_position: Ball position [x, y, h]
        ball_velocity: Ball velocity [vx, vy, vh]
        teammates: List of teammate states
        opponents: List of opponent states
        score: Current score {'home': int, 'away': int}
        time_remaining: Seconds remaining in match
        is_attacking_left: Whether attacking left goal (x=-52.5)
    """
    ball_position: np.ndarray
    ball_velocity: np.ndarray
    teammates: List[PlayerGameState]
    opponents: List[PlayerGameState]
    score: Dict[str, int]
    time_remaining: float
    is_attacking_left: bool

    def __post_init__(self):
        """Ensure numpy arrays"""
        if not isinstance(self.ball_position, np.ndarray):
            self.ball_position = np.array(self.ball_position, dtype=float)
        if not isinstance(self.ball_velocity, np.ndarray):
            self.ball_velocity = np.array(self.ball_velocity, dtype=float)


class SimpleAgent:
    """
    Rule-based agent for football decisions

    Implements 80% of decisions using simple rules:
    - If has ball → shoot/pass/dribble
    - If no ball → chase/mark/position
    - Position-specific behaviors via PositionBehaviors

    No LLM calls - purely algorithmic

    V6 IMPROVEMENTS:
    - Decision cooldown to prevent oscillation
    - Enhanced ball chase priority when ball is loose
    """

    def __init__(self, position_behaviors=None):
        """
        Initialize simple agent

        Args:
            position_behaviors: Optional PositionBehaviors instance
        """
        self.position_behaviors = position_behaviors

        # V6: Decision cooldown system to prevent oscillation
        # V11 TUNING: Reduced cooldown (0.5s → 0.2s) for faster reactions
        self.last_action = {}  # player_id -> Action
        self.last_decision_time = {}  # player_id -> float (game time)
        self.decision_cooldown = 0.2  # seconds - allow faster reactions to loose balls

    def decide_action(
        self,
        player_state: PlayerGameState,
        game_context: GameContext,
        team_adjustments: Optional[Dict[str, float]] = None
    ) -> Action:
        """
        Main decision-making entry point

        Args:
            player_state: Current player state
            game_context: Current game context
            team_adjustments: PHASE 1 - Dynamic balance adjustments for this team

        Returns:
            Action to perform
        """
        # PHASE 1: Store adjustments for use in decision logic
        if team_adjustments is None:
            team_adjustments = {
                'tackle_range_multiplier': 1.0,
                'pass_accuracy_multiplier': 1.0,
                'interception_multiplier': 1.0,
                'speed_multiplier': 1.0
            }
        self._current_adjustments = team_adjustments

        player_id = player_state.player_id
        current_game_time = game_context.time_remaining  # Use time_remaining as proxy for game time

        # V6.2: Check for CRITICAL situations that bypass cooldown
        ball_pos = game_context.ball_position
        distance_to_ball = distance_2d(player_state.position[0], player_state.position[1],
                                        ball_pos[0], ball_pos[1])
        ball_speed = np.linalg.norm(game_context.ball_velocity[:2])

        # V6.2 CRITICAL: If ball is close, slow, and on ground, BYPASS cooldown!
        # This ensures players immediately react to loose balls nearby
        ball_is_critical = (distance_to_ball < 10.0 and ball_speed < 3.0 and ball_pos[2] < 0.5)

        # V6: Check if we should make a new decision (cooldown expired)
        if player_id in self.last_decision_time and not ball_is_critical:
            time_since_last_decision = abs(
                self.last_decision_time[player_id] - current_game_time
            )

            # If cooldown hasn't expired and we have a cached action, reuse it
            # UNLESS player now has ball (high priority state change)
            # V6.1 FIX: ALWAYS update CHASE_BALL actions with current ball position
            if time_since_last_decision < self.decision_cooldown:
                if player_id in self.last_action and not player_state.has_ball:
                    last_action = self.last_action[player_id]

                    # Special case: Update chase ball actions with current ball position
                    if last_action.action_type == ActionType.CHASE_BALL:
                        # Update to current ball position (ball moves, need to update target)
                        ball_pos_2d = ball_pos[:2]
                        updated_action = Action.create_chase_ball(ball_pos_2d, speed=last_action.power or 90.0)
                        self.last_action[player_id] = updated_action
                        return updated_action

                    # Other actions can be reused as-is
                    return last_action

        # Make new decision
        if player_state.has_ball:
            action = self._decide_with_ball(player_state, game_context)
        else:
            action = self._decide_without_ball(player_state, game_context)

        # Cache decision
        self.last_action[player_id] = action
        self.last_decision_time[player_id] = current_game_time

        return action

    # =========================================================================
    # WITH BALL DECISIONS
    # =========================================================================

    def _decide_with_ball(
        self,
        player_state: PlayerGameState,
        game_context: GameContext
    ) -> Action:
        """
        Decide action when player has ball

        Priority:
        1. Shoot if in range and clear
        2. Pass if teammate open
        3. Dribble forward
        4. Shield ball if under pressure
        """
        pos = player_state.position
        goal_pos = self._get_opponent_goal_position(game_context.is_attacking_left)

        # 1. Check shooting opportunity
        in_range, shot_quality = is_in_shooting_range(
            pos, goal_pos[:2],
            max_range=SHOOTING_RANGE_MAX,
            optimal_range=SHOOTING_RANGE_OPTIMAL
        )

        # IMPROVED V3: Balanced threshold (0.35) - middle ground between V1 (0.3) and V2 (0.2)
        if in_range and shot_quality > 0.35:
            # Check if path to goal is clear
            if self._is_path_clear_to_goal(pos, goal_pos[:2], game_context.opponents):
                return self._create_shot_action(player_state, goal_pos, shot_quality)

        # 2. Check passing options
        open_teammates = self._find_open_teammates(
            player_state, game_context.teammates, game_context.opponents
        )

        if len(open_teammates) > 0:
            # Pick best teammate (furthest forward or closest to goal)
            best_teammate = self._select_best_pass_target(
                player_state, open_teammates, goal_pos[:2]
            )

            if best_teammate is not None:
                return self._create_pass_action(player_state, best_teammate)

        # 3. Dribble forward
        if not self._is_under_pressure(player_state, game_context.opponents):
            dribble_direction = self._calculate_dribble_direction(
                player_state, goal_pos[:2], game_context.opponents
            )
            return Action.create_dribble(dribble_direction, power=60.0)

        # 4. Shield ball (under pressure, no options)
        return Action.create_dribble(
            direction=np.array([0.0, 0.0]),  # Stay in place
            power=30.0
        )

    def _create_shot_action(
        self,
        player_state: PlayerGameState,
        goal_position: np.ndarray,
        shot_quality: float
    ) -> Action:
        """Create a shot action with appropriate power"""
        shooting_attr = player_state.attributes.get('shooting', 70) / 100.0
        accuracy = shooting_attr * shot_quality

        # Power based on distance and shooting attribute
        distance = distance_2d(player_state.position[0], player_state.position[1],
                              goal_position[0], goal_position[1])
        power = min(100.0, 60.0 + distance * 1.5 + shooting_attr * 20.0)

        # Target goal with some spread
        goal_target = goal_position.copy()
        goal_target[1] += np.random.uniform(-2.0, 2.0)  # Aim within goal

        return Action.create_shoot(goal_target[:2], power=power)

    def _create_pass_action(
        self,
        player_state: PlayerGameState,
        target_teammate: PlayerGameState
    ) -> Action:
        """Create a pass action to teammate"""
        distance = distance_2d(
            player_state.position[0], player_state.position[1],
            target_teammate.position[0], target_teammate.position[1]
        )

        # Determine pass type
        if distance < PASSING_RANGE_SHORT:
            pass_type = 'short'
        elif distance < PASSING_RANGE_MEDIUM:
            pass_type = 'medium'
        else:
            pass_type = 'long'

        power = calculate_pass_power(distance, pass_type)

        return Action.create_pass(
            target_player_id=target_teammate.player_id,
            target_position=target_teammate.position,
            power=power
        )

    # =========================================================================
    # WITHOUT BALL DECISIONS
    # =========================================================================

    def _decide_without_ball(
        self,
        player_state: PlayerGameState,
        game_context: GameContext
    ) -> Action:
        """
        Decide action when player doesn't have ball

        V7 IMPROVED Priority (FIX: Added TACKLE):
        0. TACKLE: If opponent has ball and within tackle range
        1. CRITICAL: If ball is very close and slow, CHASE IT (no conditions!)
        2. URGENT: Chase loose ball if close
        3. Chase ball if closest teammate
        4. Mark opponent if defending
        5. Make run if attacking
        6. Return to formation position
        """
        pos = player_state.position
        ball_pos = game_context.ball_position[:2]  # x, y only

        distance_to_ball = distance_2d(pos[0], pos[1], ball_pos[0], ball_pos[1])
        ball_speed = np.linalg.norm(game_context.ball_velocity[:2])

        # V7 FIX: Check if should tackle opponent with ball (HIGHEST PRIORITY)
        # V10 IMPROVED: More aggressive tackle triggers to increase frequency
        # V11 TUNING: Even more aggressive (5.0m → 7.0m)
        # PHASE 1: Apply dynamic tackle range boost (losing teams get wider range)
        from physics.constants import PLAYER_TACKLE_RADIUS
        tackle_range_multiplier = self._current_adjustments.get('tackle_range_multiplier', 1.0)
        effective_tackle_range = PLAYER_TACKLE_RADIUS * 2.33 * tackle_range_multiplier

        if distance_to_ball < effective_tackle_range and ball_speed < 20.0:
            # Ball is within tackle range - check if opponent has it
            opponent_has_ball = self._opponent_has_ball(game_context)
            if opponent_has_ball:
                # TACKLE! This is critical for winning ball back
                return Action.create_tackle(ball_pos, power=100.0)

        # V6.2 CRITICAL FIX: If ball is close and slow, ALWAYS chase it
        # This prevents players from ignoring a stationary ball nearby
        if distance_to_ball < 10.0 and ball_speed < 3.0 and game_context.ball_position[2] < 0.5:
            # Ball is close, slow, and on ground - DEFINITELY chase it!
            return Action.create_chase_ball(ball_pos, speed=100.0)

        # V6: Check if ball is loose (no one has it) and we're close
        # CRITICAL: If ball is loose and player is reasonably close, chase with HIGH priority
        if self._is_ball_loose(game_context):
            if distance_to_ball < 15.0:  # Within 15m of loose ball
                # Very urgent chase - use max speed
                return Action.create_chase_ball(ball_pos, speed=100.0)

        # 1. Check if should chase ball (normal priority)
        if self._should_chase_ball(player_state, game_context):
            return Action.create_chase_ball(ball_pos, speed=90.0)

        # 2. Check if should mark opponent (defenders/midfielders)
        if player_state.role in ['GK', 'CB', 'FB', 'DM', 'CM']:
            opponent_to_mark = self._find_opponent_to_mark(player_state, game_context)
            if opponent_to_mark is not None:
                return Action.create_mark_opponent(
                    opponent_id=opponent_to_mark.player_id,
                    opponent_position=opponent_to_mark.position
                )

        # 3. Make attacking run (forwards/wingers)
        if player_state.role in ['ST', 'WG', 'CAM']:
            if self._should_make_run(player_state, game_context):
                run_target = self._calculate_run_position(player_state, game_context)
                return Action.create_move_to_position(run_target, speed=80.0)

        # 4. Return to formation position
        formation_pos = self._get_formation_position(player_state, game_context)
        return Action.create_move_to_position(formation_pos, speed=60.0)

    def _opponent_has_ball(self, game_context: GameContext) -> bool:
        """
        V7: Check if an opponent has the ball

        Returns True if any opponent is within control radius of ball
        """
        ball_pos = game_context.ball_position[:2]

        # Ball in air - no one has it
        if game_context.ball_position[2] > 0.5:
            return False

        # Check all opponents
        for opponent in game_context.opponents:
            dist = distance_2d(opponent.position[0], opponent.position[1],
                              ball_pos[0], ball_pos[1])
            if dist < PLAYER_CONTROL_RADIUS:  # Opponent has ball
                return True

        return False

    def _is_ball_loose(self, game_context: GameContext) -> bool:
        """
        V6: Check if ball is loose (no one has it)

        Ball is considered loose if:
        - Ball is on ground (height < 0.5m)
        - Ball speed is low (< 5 m/s)
        - No player from either team is very close to it (< 2.5m)
        """
        ball_pos = game_context.ball_position
        ball_vel = game_context.ball_velocity

        # Ball in air - not loose
        if ball_pos[2] > 0.5:
            return False

        # Ball moving fast - someone just kicked it
        ball_speed = np.linalg.norm(ball_vel[:2])
        if ball_speed > 5.0:
            return False

        # Check if any player is close to ball (has control)
        ball_pos_2d = ball_pos[:2]

        # Check all teammates
        for teammate in game_context.teammates:
            dist = distance_2d(teammate.position[0], teammate.position[1],
                              ball_pos_2d[0], ball_pos_2d[1])
            if dist < 2.5:  # Someone has it or very close
                return False

        # Check all opponents
        for opponent in game_context.opponents:
            dist = distance_2d(opponent.position[0], opponent.position[1],
                              ball_pos_2d[0], ball_pos_2d[1])
            if dist < 2.5:  # Someone has it or very close
                return False

        # Ball is loose!
        return True

    def _should_chase_ball(
        self,
        player_state: PlayerGameState,
        game_context: GameContext
    ) -> bool:
        """Check if player should chase ball (is closest)"""
        ball_pos = game_context.ball_position[:2]
        player_pos = player_state.position

        distance_to_ball = distance_2d(player_pos[0], player_pos[1],
                                       ball_pos[0], ball_pos[1])

        # IMPROVED V4: Increased from 20.0m to 30.0m so forwards can chase after ball resets
        if distance_to_ball > 30.0:
            return False

        # V6: If ball is loose, be more aggressive about chasing
        if self._is_ball_loose(game_context):
            # Don't require being closest - multiple players can chase loose ball
            return True

        # Normal case: Check if closest teammate to ball
        for teammate in game_context.teammates:
            teammate_dist = distance_2d(
                teammate.position[0], teammate.position[1],
                ball_pos[0], ball_pos[1]
            )
            if teammate_dist < distance_to_ball - 2.0:  # Someone closer
                return False

        return True

    # =========================================================================
    # HELPER FUNCTIONS
    # =========================================================================

    def _get_opponent_goal_position(self, is_attacking_left: bool) -> np.ndarray:
        """Get opponent goal center position"""
        if is_attacking_left:
            return np.array([FIELD_X_MIN, 0.0, 1.2])  # Left goal
        else:
            return np.array([FIELD_X_MAX, 0.0, 1.2])  # Right goal

    def _is_path_clear_to_goal(
        self,
        player_pos: np.ndarray,
        goal_pos: np.ndarray,
        opponents: List[PlayerGameState]
    ) -> bool:
        """Check if shooting path is clear"""
        # Simple check: no opponent directly between player and goal
        for opp in opponents:
            # Check if opponent is in shooting cone
            to_goal = goal_pos - player_pos
            to_opp = opp.position - player_pos

            # Project opponent onto shooting line
            projection = np.dot(to_opp, to_goal) / np.linalg.norm(to_goal)

            # If opponent is in front and close to line
            if 0 < projection < np.linalg.norm(to_goal):
                # Distance from shooting line
                perp_distance = np.linalg.norm(to_opp - projection * to_goal / np.linalg.norm(to_goal))
                # IMPROVED V3: Balanced 4.0m - middle ground between V1 (3.0m) and V2 (5.0m)
                if perp_distance < 4.0:  # Within 4m of shooting line
                    return False

        return True

    def _find_open_teammates(
        self,
        player_state: PlayerGameState,
        teammates: List[PlayerGameState],
        opponents: List[PlayerGameState]
    ) -> List[PlayerGameState]:
        """Find teammates that are open for a pass"""
        open_teammates = []

        for teammate in teammates:
            if teammate.player_id == player_state.player_id:
                continue

            # Check distance
            distance = distance_2d(
                player_state.position[0], player_state.position[1],
                teammate.position[0], teammate.position[1]
            )

            if distance > 40.0:  # Too far
                continue

            # Check if teammate is marked
            is_marked = False
            for opp in opponents:
                opp_dist = distance_2d(
                    teammate.position[0], teammate.position[1],
                    opp.position[0], opp.position[1]
                )
                if opp_dist < 2.0:  # Closely marked
                    is_marked = True
                    break

            if not is_marked:
                open_teammates.append(teammate)

        return open_teammates

    def _select_best_pass_target(
        self,
        player_state: PlayerGameState,
        candidates: List[PlayerGameState],
        goal_position: np.ndarray
    ) -> Optional[PlayerGameState]:
        """Select best teammate to pass to"""
        if len(candidates) == 0:
            return None

        # Score each candidate
        best_score = -float('inf')  # V9 FIX: Use -inf instead of -1
        best_teammate = None

        for teammate in candidates:
            # Prefer teammates closer to goal
            distance_to_goal = distance_2d(
                teammate.position[0], teammate.position[1],
                goal_position[0], goal_position[1]
            )

            # V9 FIX: Calculate forward progress based on goal direction
            # Forward is toward goal, regardless of x-direction
            teammate_to_goal = goal_position[0] - teammate.position[0]
            player_to_goal = goal_position[0] - player_state.position[0]

            # Positive if teammate is closer to goal than player
            forward_progress = abs(player_to_goal) - abs(teammate_to_goal)

            # Combined score (lower distance to goal + forward progress)
            score = -distance_to_goal + forward_progress * 2.0

            if score > best_score:
                best_score = score
                best_teammate = teammate

        return best_teammate

    def _is_under_pressure(
        self,
        player_state: PlayerGameState,
        opponents: List[PlayerGameState]
    ) -> bool:
        """Check if player is under pressure from opponents"""
        for opp in opponents:
            distance = distance_2d(
                player_state.position[0], player_state.position[1],
                opp.position[0], opp.position[1]
            )
            if distance < 3.0:  # Opponent within 3m
                return True
        return False

    def _calculate_dribble_direction(
        self,
        player_state: PlayerGameState,
        goal_position: np.ndarray,
        opponents: List[PlayerGameState]
    ) -> np.ndarray:
        """Calculate best direction to dribble"""
        # Base direction: toward goal
        to_goal = goal_position - player_state.position

        # Avoid nearby opponents
        avoidance_vector = np.zeros(2)
        for opp in opponents:
            to_opp = opp.position - player_state.position
            distance = np.linalg.norm(to_opp)

            if distance < 5.0:  # Nearby opponent
                # Push away from opponent
                avoidance_vector -= to_opp / (distance + 0.1) ** 2

        # Combine goal direction + avoidance
        direction = to_goal + avoidance_vector * 3.0

        # Normalize
        norm = np.linalg.norm(direction)
        if norm > 0:
            direction = direction / norm

        return direction

    def _find_opponent_to_mark(
        self,
        player_state: PlayerGameState,
        game_context: GameContext
    ) -> Optional[PlayerGameState]:
        """Find closest dangerous opponent to mark"""
        ball_pos = game_context.ball_position[:2]

        closest_opp = None
        closest_dist = float('inf')

        for opp in game_context.opponents:
            # Prioritize opponents near ball or in dangerous positions
            dist_to_ball = distance_2d(opp.position[0], opp.position[1],
                                       ball_pos[0], ball_pos[1])

            dist_to_player = distance_2d(
                player_state.position[0], player_state.position[1],
                opp.position[0], opp.position[1]
            )

            # Score: prefer close opponents who are also near ball
            score = dist_to_player + dist_to_ball * 0.5

            if score < closest_dist and dist_to_player < 15.0:
                closest_dist = score
                closest_opp = opp

        return closest_opp

    def _should_make_run(
        self,
        player_state: PlayerGameState,
        game_context: GameContext
    ) -> bool:
        """Check if forward should make attacking run"""
        # Make run if ball is in midfield or attacking third
        ball_x = game_context.ball_position[0]

        if game_context.is_attacking_left:
            # Attacking left, ball should be in left half
            return ball_x < 0
        else:
            # Attacking right, ball should be in right half
            return ball_x > 0

    def _calculate_run_position(
        self,
        player_state: PlayerGameState,
        game_context: GameContext
    ) -> np.ndarray:
        """Calculate position for attacking run"""
        goal_pos = self._get_opponent_goal_position(game_context.is_attacking_left)

        # Run toward goal, slightly offset
        target_x = goal_pos[0] + (10.0 if game_context.is_attacking_left else -10.0)
        target_y = player_state.position[1] + np.random.uniform(-5.0, 5.0)

        # Clamp to field
        target_x = max(FIELD_X_MIN + 5, min(FIELD_X_MAX - 5, target_x))
        target_y = max(FIELD_Y_MIN + 5, min(FIELD_Y_MAX - 5, target_y))

        return np.array([target_x, target_y])

    def _get_formation_position(
        self,
        player_state: PlayerGameState,
        game_context: GameContext
    ) -> np.ndarray:
        """Get player's formation position"""
        # Simplified: return current position with slight adjustment
        # In full implementation, this would use team formation data

        # Move slightly toward own half
        target_x = player_state.position[0] * 0.8
        target_y = player_state.position[1] * 0.9

        # Clamp to field
        target_x = max(FIELD_X_MIN + 5, min(FIELD_X_MAX - 5, target_x))
        target_y = max(FIELD_Y_MIN + 5, min(FIELD_Y_MAX - 5, target_y))

        return np.array([target_x, target_y])


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    'PlayerGameState',
    'GameContext',
    'SimpleAgent'
]
