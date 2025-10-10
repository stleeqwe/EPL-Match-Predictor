# -*- coding: utf-8 -*-
"""
Position-Specific Behaviors
Specialized decision-making for each position (GK, CB, FB, DM, CM, CAM, WG, ST)

Each position has unique priorities and behaviors:
- GK: Save shots, distribute ball
- CB: Defend, clear danger, mark strikers
- FB: Defend wide, overlap attacks
- DM: Shield defense, break up play
- CM: Link play, control midfield
- CAM: Create chances, support attack
- WG: Width, crosses, cutting inside
- ST: Score goals, hold up play
"""

import numpy as np
from typing import Optional, List
from dataclasses import dataclass

from .actions import Action, ActionType
from .simple_agent import PlayerGameState, GameContext

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from physics.constants import (
    FIELD_X_MIN, FIELD_X_MAX, FIELD_Y_MIN, FIELD_Y_MAX,
    GOAL_Y_MIN, GOAL_Y_MAX, GOAL_HEIGHT,
    PENALTY_AREA_LENGTH,
    distance_2d
)


class PositionBehaviors:
    """
    Position-specific behaviors for all 8 positions

    Implements specialized decision trees for each role
    """

    @staticmethod
    def goalkeeper_behavior(
        player_state: PlayerGameState,
        game_context: GameContext
    ) -> Optional[Action]:
        """
        Goalkeeper behavior

        Priority:
        1. Save shot if ball coming toward goal
        2. Catch ball if in penalty area
        3. Distribute ball if has possession
        4. Position for shot
        5. Stay on goal line
        """
        pos = player_state.position
        ball_pos = game_context.ball_position[:2]
        ball_vel = game_context.ball_velocity[:2]

        # Own goal position
        own_goal_x = FIELD_X_MIN if not game_context.is_attacking_left else FIELD_X_MAX

        # 1. Ball coming toward goal - SAVE
        if abs(ball_pos[0] - own_goal_x) < PENALTY_AREA_LENGTH:
            # Ball in penalty area
            ball_speed = np.linalg.norm(ball_vel)

            if ball_speed > 5.0:  # Fast moving ball (shot)
                # Check if heading toward goal
                if game_context.is_attacking_left:
                    toward_goal = ball_vel[0] > 0  # Moving right toward goal
                else:
                    toward_goal = ball_vel[0] < 0  # Moving left toward goal

                if toward_goal:
                    return Action.create_save_shot(ball_pos)

        # 2. Catch ball if close and has possession
        distance_to_ball = distance_2d(pos[0], pos[1], ball_pos[0], ball_pos[1])

        if distance_to_ball < 2.0 and player_state.has_ball:
            # Look for distribution target
            best_target = PositionBehaviors._find_gk_distribution_target(
                player_state, game_context
            )

            if best_target is not None:
                return Action.create_pass(
                    target_player_id=best_target.player_id,
                    target_position=best_target.position,
                    power=70.0
                )

        # 3. Chase ball if in penalty area
        if distance_to_ball < 5.0 and abs(ball_pos[0] - own_goal_x) < PENALTY_AREA_LENGTH:
            return Action.create_chase_ball(ball_pos, speed=90.0)

        # 4. Position for shot - stay on goal line
        ideal_x = own_goal_x + (2.0 if game_context.is_attacking_left else -2.0)
        ideal_y = 0.0  # Center of goal

        # Adjust y position based on ball position
        if abs(ball_pos[1]) < 20.0:
            ideal_y = ball_pos[1] * 0.3  # Slight offset toward ball

        # Clamp to goal width
        ideal_y = max(GOAL_Y_MIN + 0.5, min(GOAL_Y_MAX - 0.5, ideal_y))

        return Action.create_move_to_position(
            np.array([ideal_x, ideal_y]),
            speed=60.0
        )

    @staticmethod
    def center_back_behavior(
        player_state: PlayerGameState,
        game_context: GameContext
    ) -> Optional[Action]:
        """
        Center Back behavior

        Priority:
        1. Clear ball if in defensive third
        2. Mark closest striker
        3. Intercept passes
        4. Hold defensive line
        """
        pos = player_state.position
        ball_pos = game_context.ball_position[:2]

        own_goal_x = FIELD_X_MIN if not game_context.is_attacking_left else FIELD_X_MAX

        # 1. Clear ball if in danger zone
        if player_state.has_ball and abs(pos[0] - own_goal_x) < 30.0:
            # Clear toward sideline and forward
            clear_direction = np.array([
                1.0 if game_context.is_attacking_left else -1.0,
                1.0 if pos[1] < 0 else -1.0
            ])
            clear_direction = clear_direction / np.linalg.norm(clear_direction)

            return Action.create_clear_ball(clear_direction, power=90.0)

        # 2. Mark dangerous opponent (striker)
        dangerous_opponent = PositionBehaviors._find_dangerous_opponent(
            player_state, game_context, roles=['ST', 'CAM', 'WG']
        )

        if dangerous_opponent is not None:
            opp_distance = distance_2d(
                pos[0], pos[1],
                dangerous_opponent.position[0], dangerous_opponent.position[1]
            )

            # If very close, tackle
            if opp_distance < 1.5 and not player_state.has_ball:
                return Action.create_tackle(dangerous_opponent.position, power=80.0)

            # Otherwise mark
            if opp_distance < 10.0:
                return Action.create_mark_opponent(
                    opponent_id=dangerous_opponent.player_id,
                    opponent_position=dangerous_opponent.position
                )

        # 3. Hold defensive line
        defensive_line_x = own_goal_x + (25.0 if game_context.is_attacking_left else -25.0)

        return Action.create_move_to_position(
            np.array([defensive_line_x, pos[1]]),
            speed=50.0
        )

    @staticmethod
    def full_back_behavior(
        player_state: PlayerGameState,
        game_context: GameContext
    ) -> Optional[Action]:
        """
        Full Back behavior

        Priority:
        1. Defend wide areas
        2. Overlap on attack
        3. Track back when defending
        4. Support center backs
        """
        pos = player_state.position
        ball_pos = game_context.ball_position[:2]

        own_goal_x = FIELD_X_MIN if not game_context.is_attacking_left else FIELD_X_MAX

        # Determine side (left or right)
        is_left_side = pos[1] < 0

        # 1. If has ball, overlap attack
        if player_state.has_ball:
            # Look for winger to pass to
            winger = PositionBehaviors._find_teammate_by_role(
                game_context.teammates, ['WG']
            )

            if winger is not None:
                winger_distance = distance_2d(
                    pos[0], pos[1], winger.position[0], winger.position[1]
                )
                if winger_distance < 25.0:
                    return Action.create_pass(
                        target_player_id=winger.player_id,
                        target_position=winger.position,
                        power=60.0
                    )

            # Otherwise, dribble forward along sideline
            dribble_dir = np.array([
                1.0 if game_context.is_attacking_left else -1.0,
                0.0
            ])
            return Action.create_dribble(dribble_dir, power=60.0)

        # 2. Defend wide areas - mark wingers
        opponent_winger = PositionBehaviors._find_dangerous_opponent(
            player_state, game_context, roles=['WG']
        )

        if opponent_winger is not None:
            return Action.create_mark_opponent(
                opponent_id=opponent_winger.player_id,
                opponent_position=opponent_winger.position
            )

        # 3. Track back to defensive position
        defensive_x = own_goal_x + (20.0 if game_context.is_attacking_left else -20.0)
        defensive_y = FIELD_Y_MAX - 10.0 if is_left_side else FIELD_Y_MIN + 10.0

        return Action.create_move_to_position(
            np.array([defensive_x, defensive_y]),
            speed=70.0
        )

    @staticmethod
    def defensive_midfielder_behavior(
        player_state: PlayerGameState,
        game_context: GameContext
    ) -> Optional[Action]:
        """
        Defensive Midfielder behavior

        Priority:
        1. Shield defense
        2. Break up opposition play
        3. Distribute to attackers
        4. Control tempo
        """
        pos = player_state.position
        ball_pos = game_context.ball_position[:2]

        # 1. If has ball, distribute
        if player_state.has_ball:
            # Look for forward pass to CAM or ST
            forward_target = PositionBehaviors._find_teammate_by_role(
                game_context.teammates, ['CAM', 'ST', 'WG']
            )

            if forward_target is not None:
                return Action.create_pass(
                    target_player_id=forward_target.player_id,
                    target_position=forward_target.position,
                    power=65.0
                )

            # Otherwise, safe pass to CM
            cm_target = PositionBehaviors._find_teammate_by_role(
                game_context.teammates, ['CM']
            )

            if cm_target is not None:
                return Action.create_pass(
                    target_player_id=cm_target.player_id,
                    target_position=cm_target.position,
                    power=50.0
                )

        # 2. Intercept opposition attacks
        ball_distance = distance_2d(pos[0], pos[1], ball_pos[0], ball_pos[1])

        if ball_distance < 10.0:
            # Close to ball, press
            opponent_with_ball = PositionBehaviors._find_opponent_with_ball(
                game_context.opponents
            )

            if opponent_with_ball is not None:
                return Action(
                    action_type=ActionType.PRESS_OPPONENT,
                    target_position=opponent_with_ball.position,
                    power=80.0
                )

        # 3. Shield defense - position between ball and goal
        own_goal_x = FIELD_X_MIN if not game_context.is_attacking_left else FIELD_X_MAX

        # Position halfway between ball and defense
        shield_x = (ball_pos[0] + own_goal_x) / 2.0
        shield_y = pos[1] * 0.5  # Slight adjustment toward center

        return Action.create_move_to_position(
            np.array([shield_x, shield_y]),
            speed=65.0
        )

    @staticmethod
    def center_midfielder_behavior(
        player_state: PlayerGameState,
        game_context: GameContext
    ) -> Optional[Action]:
        """
        Center Midfielder behavior

        Priority:
        0. V6 FIX: Fall back to SimpleAgent for critical ball situations
        1. Link defense and attack
        2. Control possession
        3. Support both phases
        4. Cover ground
        """
        pos = player_state.position
        ball_pos = game_context.ball_position

        # V6 FIX: If ball is loose and close, let SimpleAgent handle it (chase priority)
        # This prevents CMs from moving to "support position" instead of chasing loose ball
        distance_to_ball = distance_2d(pos[0], pos[1], ball_pos[0], ball_pos[1])
        ball_speed = np.linalg.norm(game_context.ball_velocity[:2])

        # Ball is critical: close, slow, on ground
        if distance_to_ball < 10.0 and ball_speed < 3.0 and ball_pos[2] < 0.5:
            # Return None to fall back to SimpleAgent which has better ball chase logic
            return None

        # 1. If has ball, look for forward pass
        if player_state.has_ball:
            # Prefer attacking players
            forward_target = PositionBehaviors._find_teammate_by_role(
                game_context.teammates, ['ST', 'CAM', 'WG']
            )

            if forward_target is not None:
                return Action.create_pass(
                    target_player_id=forward_target.player_id,
                    target_position=forward_target.position,
                    power=60.0
                )

            # Otherwise, keep possession with DM or other CM
            safe_target = PositionBehaviors._find_teammate_by_role(
                game_context.teammates, ['DM', 'CM']
            )

            if safe_target is not None:
                return Action.create_pass(
                    target_player_id=safe_target.player_id,
                    target_position=safe_target.position,
                    power=50.0
                )

        # 2. Support play - move toward ball
        # NOTE: ball_pos and distance_to_ball already calculated above in V6 fix
        ball_pos_2d = ball_pos[:2]

        if distance_to_ball < 15.0:
            # V6 FIX: If ball is slow, move closer (don't just support from offset)
            if ball_speed < 3.0 and distance_to_ball > 3.0:
                # Move directly toward ball
                return Action.create_chase_ball(ball_pos_2d, speed=80.0)

            # Normal case: Move to support position (when ball is moving)
            support_pos = ball_pos_2d + np.array([
                -5.0 if game_context.is_attacking_left else 5.0,
                5.0 if pos[1] < 0 else -5.0
            ])

            return Action.create_move_to_position(support_pos, speed=70.0)

        # 3. Hold central position
        return Action.create_move_to_position(
            np.array([0.0, 0.0]),  # Center circle
            speed=60.0
        )

    @staticmethod
    def attacking_midfielder_behavior(
        player_state: PlayerGameState,
        game_context: GameContext
    ) -> Optional[Action]:
        """
        Attacking Midfielder behavior

        Priority:
        1. Create chances
        2. Support strikers
        3. Shoot from distance
        4. Thread through balls
        """
        pos = player_state.position
        ball_pos = game_context.ball_position[:2]

        opp_goal = FIELD_X_MIN if game_context.is_attacking_left else FIELD_X_MAX
        goal_pos = np.array([opp_goal, 0.0])

        # 1. If has ball in shooting range, try shot
        if player_state.has_ball:
            distance_to_goal = distance_2d(pos[0], pos[1], goal_pos[0], goal_pos[1])

            if distance_to_goal < 25.0:
                # Check if shot is on
                from .actions import is_in_shooting_range
                in_range, quality = is_in_shooting_range(pos, goal_pos)

                if in_range and quality > 0.4:
                    return Action.create_shoot(goal_pos, power=80.0)

            # Look for striker to pass to
            striker = PositionBehaviors._find_teammate_by_role(
                game_context.teammates, ['ST']
            )

            if striker is not None:
                # Check if striker is in good position
                striker_dist_to_goal = distance_2d(
                    striker.position[0], striker.position[1],
                    goal_pos[0], goal_pos[1]
                )

                if striker_dist_to_goal < 20.0:
                    return Action.create_pass(
                        target_player_id=striker.player_id,
                        target_position=striker.position,
                        power=65.0
                    )

        # 2. Make run into box
        if not player_state.has_ball:
            # Position between midfield and attack
            run_x = opp_goal + (15.0 if game_context.is_attacking_left else -15.0)
            run_y = pos[1] * 0.8

            return Action.create_move_to_position(
                np.array([run_x, run_y]),
                speed=75.0
            )

        return None

    @staticmethod
    def winger_behavior(
        player_state: PlayerGameState,
        game_context: GameContext
    ) -> Optional[Action]:
        """
        Winger behavior

        Priority:
        1. Provide width
        2. Cross to strikers
        3. Cut inside and shoot
        4. Beat full back 1v1
        """
        pos = player_state.position
        is_left_winger = pos[1] < 0

        opp_goal_x = FIELD_X_MIN if game_context.is_attacking_left else FIELD_X_MAX

        # 1. If has ball near byline, cross
        if player_state.has_ball:
            near_byline = abs(pos[0] - opp_goal_x) < 20.0

            if near_byline:
                # Look for striker in box
                striker = PositionBehaviors._find_teammate_by_role(
                    game_context.teammates, ['ST', 'CAM']
                )

                if striker is not None:
                    return Action(
                        action_type=ActionType.CROSS,
                        target_player_id=striker.player_id,
                        target_position=striker.position,
                        power=70.0,
                        metadata={'action': 'cross'}
                    )

            # Otherwise, dribble toward byline
            dribble_dir = np.array([
                1.0 if game_context.is_attacking_left else -1.0,
                0.0
            ])
            return Action.create_dribble(dribble_dir, power=70.0)

        # 2. Stay wide
        wide_y = FIELD_Y_MAX - 5.0 if is_left_winger else FIELD_Y_MIN + 5.0
        attacking_x = opp_goal_x + (25.0 if game_context.is_attacking_left else -25.0)

        return Action.create_move_to_position(
            np.array([attacking_x, wide_y]),
            speed=70.0
        )

    @staticmethod
    def striker_behavior(
        player_state: PlayerGameState,
        game_context: GameContext
    ) -> Optional[Action]:
        """
        Striker behavior

        Priority:
        1. Shoot when in range
        2. Make runs into box
        3. Hold up play
        4. Pressure defenders
        """
        pos = player_state.position

        opp_goal_x = FIELD_X_MIN if game_context.is_attacking_left else FIELD_X_MAX
        goal_pos = np.array([opp_goal_x, 0.0])

        # 1. If has ball, shoot
        if player_state.has_ball:
            from .actions import is_in_shooting_range
            in_range, quality = is_in_shooting_range(pos, goal_pos)

            if in_range:
                return Action.create_shoot(goal_pos, power=90.0)

            # Hold up play - shield ball
            return Action.create_dribble(
                direction=np.array([0.0, 0.0]),
                power=40.0
            )

        # 2. Make run into box
        ball_pos = game_context.ball_position[:2]

        # If ball is in attacking third, make run
        ball_in_attacking_third = (
            (game_context.is_attacking_left and ball_pos[0] < -17.5) or
            (not game_context.is_attacking_left and ball_pos[0] > 17.5)
        )

        if ball_in_attacking_third:
            # Run to position for through ball
            run_x = opp_goal_x + (12.0 if game_context.is_attacking_left else -12.0)
            run_y = pos[1] + np.random.uniform(-3.0, 3.0)

            return Action.create_move_to_position(
                np.array([run_x, run_y]),
                speed=85.0
            )

        # 3. Stay high up pitch
        return Action.create_move_to_position(
            np.array([opp_goal_x + (20.0 if game_context.is_attacking_left else -20.0), pos[1]]),
            speed=60.0
        )

    # =========================================================================
    # HELPER FUNCTIONS
    # =========================================================================

    @staticmethod
    def _find_gk_distribution_target(
        player_state: PlayerGameState,
        game_context: GameContext
    ) -> Optional[PlayerGameState]:
        """Find best target for goalkeeper distribution"""
        # Prefer full backs or defensive midfielders
        targets = [t for t in game_context.teammates
                  if t.role in ['FB', 'DM', 'CM']]

        if len(targets) == 0:
            return None

        # Pick closest
        best_target = min(targets, key=lambda t: distance_2d(
            player_state.position[0], player_state.position[1],
            t.position[0], t.position[1]
        ))

        return best_target

    @staticmethod
    def _find_dangerous_opponent(
        player_state: PlayerGameState,
        game_context: GameContext,
        roles: List[str]
    ) -> Optional[PlayerGameState]:
        """Find closest dangerous opponent with given roles"""
        candidates = [opp for opp in game_context.opponents if opp.role in roles]

        if len(candidates) == 0:
            return None

        # Find closest
        best_opp = min(candidates, key=lambda opp: distance_2d(
            player_state.position[0], player_state.position[1],
            opp.position[0], opp.position[1]
        ))

        return best_opp

    @staticmethod
    def _find_teammate_by_role(
        teammates: List[PlayerGameState],
        roles: List[str]
    ) -> Optional[PlayerGameState]:
        """Find first teammate matching role"""
        for teammate in teammates:
            if teammate.role in roles:
                return teammate
        return None

    @staticmethod
    def _find_opponent_with_ball(
        opponents: List[PlayerGameState]
    ) -> Optional[PlayerGameState]:
        """Find opponent who has the ball"""
        for opp in opponents:
            if opp.has_ball:
                return opp
        return None


# =============================================================================
# POSITION DISPATCHER
# =============================================================================

def get_position_action(
    player_state: PlayerGameState,
    game_context: GameContext
) -> Optional[Action]:
    """
    Get position-specific action for player

    Args:
        player_state: Current player state
        game_context: Current game context

    Returns:
        Position-specific action, or None to fall back to SimpleAgent
    """
    role = player_state.role

    if role == 'GK':
        return PositionBehaviors.goalkeeper_behavior(player_state, game_context)
    elif role == 'CB':
        return PositionBehaviors.center_back_behavior(player_state, game_context)
    elif role == 'FB':
        return PositionBehaviors.full_back_behavior(player_state, game_context)
    elif role == 'DM':
        return PositionBehaviors.defensive_midfielder_behavior(player_state, game_context)
    elif role == 'CM':
        return PositionBehaviors.center_midfielder_behavior(player_state, game_context)
    elif role == 'CAM':
        return PositionBehaviors.attacking_midfielder_behavior(player_state, game_context)
    elif role == 'WG':
        return PositionBehaviors.winger_behavior(player_state, game_context)
    elif role == 'ST':
        return PositionBehaviors.striker_behavior(player_state, game_context)
    else:
        return None  # Unknown role, fall back to SimpleAgent


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    'PositionBehaviors',
    'get_position_action'
]
