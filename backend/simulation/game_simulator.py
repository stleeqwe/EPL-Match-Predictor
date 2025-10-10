# -*- coding: utf-8 -*-
"""
Game Simulator
Main simulation loop integrating physics + agents

Responsibilities:
- Run complete 90-minute match
- Coordinate physics engine + agents
- Detect events
- Collect statistics
- Handle ball resets (kickoff, goal kick, etc.)
"""

import time
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from physics.player_physics import PlayerState, PlayerPhysicsEngine
from physics.ball_physics import BallState, BallPhysicsEngine
from physics.constants import (
    DT, TICKS_PER_SECOND, MATCH_DURATION_SECONDS,
    FIELD_X_MIN, FIELD_X_MAX, FIELD_Y_MIN, FIELD_Y_MAX,
    PLAYER_CONTROL_RADIUS, distance_2d
)

from agents.simple_agent import SimpleAgent, PlayerGameState, GameContext
from agents.position_behaviors import get_position_action

from .action_executor import ActionExecutor, BallInteraction
from .event_detector import EventDetector, MatchEvent, EventType
from .match_statistics import MatchStatistics
from .global_context import GlobalContext
from .dynamic_balancer import DynamicBalancer


@dataclass
class SimulationConfig:
    """Simulation configuration"""
    duration_seconds: float = MATCH_DURATION_SECONDS  # 5400 (90 min)
    dt: float = DT  # 0.1s
    enable_agents: bool = True
    enable_position_behaviors: bool = True
    collect_statistics: bool = True
    verbose: bool = False


class GameSimulator:
    """
    Complete match simulator

    Integrates:
    - Physics engine (player + ball)
    - Agent system (decisions)
    - Event detection
    - Statistics collection
    """

    def __init__(self, config: Optional[SimulationConfig] = None):
        """
        Initialize game simulator

        Args:
            config: Simulation configuration
        """
        self.config = config or SimulationConfig()

        # Physics engines
        self.player_engine = PlayerPhysicsEngine(dt=self.config.dt)
        self.ball_engine = BallPhysicsEngine(dt=self.config.dt)

        # Agent system
        self.simple_agent = SimpleAgent()
        self.action_executor = ActionExecutor()

        # Event detection & statistics
        self.event_detector = EventDetector()
        self.statistics = None

        # PHASE 1: Team intelligence layer
        self.global_context = GlobalContext()
        self.dynamic_balancer = DynamicBalancer()
        self.current_adjustments = None  # Cached dynamic adjustments

        # Match state
        self.current_time = 0.0
        self.tick_count = 0
        self.score = {'home': 0, 'away': 0}
        self.reset_count = 0  # V8: Track resets for alternating ball placement

        # Performance tracking
        self.performance_stats = {
            'total_ticks': 0,
            'total_time': 0.0,
            'agent_time': 0.0,
            'physics_time': 0.0,
            'event_time': 0.0
        }

    def simulate_match(
        self,
        home_players: List[Dict],
        away_players: List[Dict],
        home_team_name: str = 'Home',
        away_team_name: str = 'Away'
    ) -> Dict:
        """
        Simulate complete match

        Args:
            home_players: List of home player dicts with id, position, role, attributes
            away_players: List of away player dicts with id, position, role, attributes
            home_team_name: Home team name
            away_team_name: Away team name

        Returns:
            Match results with statistics and events
        """
        print(f"\n{'='*70}")
        print(f"Match Simulation: {home_team_name} vs {away_team_name}")
        print(f"{'='*70}")

        # Initialize match
        player_states, player_ids, player_attrs, player_roles = self._initialize_match(
            home_players, away_players
        )

        ball_state = self._initialize_ball()

        # Initialize statistics
        if self.config.collect_statistics:
            self.statistics = MatchStatistics(
                home_team_name=home_team_name,
                away_team_name=away_team_name,
                home_player_ids=player_ids['home'],
                away_player_ids=player_ids['away']
            )

        # Simulation loop
        start_time = time.time()
        total_ticks = int(self.config.duration_seconds / self.config.dt)

        print(f"Simulating {self.config.duration_seconds}s ({total_ticks} ticks)...")

        for tick in range(total_ticks):
            # Update simulation
            player_states, ball_state, events = self._simulate_tick(
                player_states, player_ids, player_attrs, player_roles,
                ball_state
            )

            # Process events
            if events:
                for event in events:
                    self._handle_event(event, player_states, ball_state)

            # Progress update every 10% (900 ticks for 90min)
            if tick % (total_ticks // 10) == 0 and tick > 0:
                progress = (tick / total_ticks) * 100
                print(f"  Progress: {progress:.0f}% - Time: {self.current_time/60:.1f}min - Score: {self.score['home']}-{self.score['away']}")

        elapsed = time.time() - start_time
        self.performance_stats['total_time'] = elapsed
        self.performance_stats['total_ticks'] = total_ticks

        print(f"\nSimulation complete!")
        print(f"  Real time: {elapsed:.2f}s")
        print(f"  Simulation speed: {self.config.duration_seconds/elapsed:.1f}x real-time")
        print(f"  Final score: {self.score['home']}-{self.score['away']}")

        # Generate results
        results = self._generate_results()

        return results

    def _initialize_match(
        self,
        home_players: List[Dict],
        away_players: List[Dict]
    ) -> Tuple[Dict, Dict, Dict, Dict]:
        """Initialize match state"""
        player_states = {'home': [], 'away': []}
        player_ids = {'home': [], 'away': []}
        player_attrs = {'home': [], 'away': []}
        player_roles = {'home': [], 'away': []}

        # Home team
        for player in home_players:
            state = PlayerState(
                player_id=player['id'],
                position=np.array(player['position']),
                velocity=np.zeros(2),
                acceleration=np.zeros(2),
                stamina=100.0,
                is_moving=False
            )
            player_states['home'].append(state)
            player_ids['home'].append(player['id'])
            player_attrs['home'].append(player['attributes'])
            player_roles['home'].append(player['role'])

        # Away team
        for player in away_players:
            state = PlayerState(
                player_id=player['id'],
                position=np.array(player['position']),
                velocity=np.zeros(2),
                acceleration=np.zeros(2),
                stamina=100.0,
                is_moving=False
            )
            player_states['away'].append(state)
            player_ids['away'].append(player['id'])
            player_attrs['away'].append(player['attributes'])
            player_roles['away'].append(player['role'])

        return player_states, player_ids, player_attrs, player_roles

    def _initialize_ball(self) -> BallState:
        """
        Initialize ball at kickoff position

        V8 FIX: Randomize initial kickoff to prevent one team always starting with advantage
        """
        # Randomize which team gets initial kickoff advantage
        x_offset = np.random.choice([10.0, -10.0])  # Favor home (+) or away (-)
        y_offset = np.random.uniform(-3.0, 3.0)

        return BallState(
            position=np.array([x_offset, y_offset, 0.11]),
            velocity=np.zeros(3),
            spin=0.0
        )

    def _simulate_tick(
        self,
        player_states: Dict,
        player_ids: Dict,
        player_attrs: Dict,
        player_roles: Dict,
        ball_state: BallState
    ) -> Tuple[Dict, BallState, List[MatchEvent]]:
        """Simulate single tick"""
        tick_start = time.time()

        # PHASE 1: Update global context and get dynamic adjustments
        current_possessor = self._determine_ball_possessor(ball_state, player_states, player_ids)
        self.global_context.update(
            self.config.dt,
            ball_state.position,
            current_possessor,
            self.current_time
        )

        # Get dynamic balance adjustments
        self.current_adjustments = self.dynamic_balancer.calculate_adjustments(
            self.global_context.possession_balance,
            self.global_context.match_phase
        )

        # 1. Agent decisions
        agent_start = time.time()

        if self.config.enable_agents:
            # V6.3 FIX: Track which player is closest to ball (only they can kick it)
            closest_player_team = None
            closest_player_idx = None
            closest_distance = float('inf')

            # Find closest player to ball
            for team in ['home', 'away']:
                for i in range(len(player_states[team])):
                    dist = distance_2d(
                        player_states[team][i].position[0],
                        player_states[team][i].position[1],
                        ball_state.position[0],
                        ball_state.position[1]
                    )
                    if dist < closest_distance:
                        closest_distance = dist
                        closest_player_team = team
                        closest_player_idx = i

            # Process all players
            for team in ['home', 'away']:
                for i in range(len(player_states[team])):
                    # Get action from agent
                    action = self._get_player_action(
                        player_states[team][i],
                        player_ids[team][i],
                        player_attrs[team][i],
                        player_roles[team][i],
                        team,
                        player_states,
                        player_ids,
                        ball_state
                    )

                    # Execute action
                    # PHASE 1: Pass team-specific dynamic adjustments
                    team_adjustments = self.current_adjustments[team] if self.current_adjustments else None

                    target_velocity, ball_interaction = self.action_executor.execute_action(
                        action,
                        player_states[team][i],
                        player_attrs[team][i],
                        ball_state,
                        self.config.dt,
                        team_adjustments=team_adjustments
                    )

                    # Update player physics
                    player_states[team][i] = self.player_engine.update_player_state(
                        player_states[team][i],
                        player_attrs[team][i],
                        target_velocity,
                        self.config.dt
                    )

                    # V6.3 FIX: Only closest player can kick ball (prevent multiple kicks per frame)
                    # V7 EXCEPTION: Allow tackles to work even if not closest (enables pressing)
                    is_closest = (team == closest_player_team and i == closest_player_idx)
                    is_tackle = (ball_interaction and ball_interaction.interaction_type == 'tackle')

                    # Allow ball kick if: (1) closest player OR (2) tackle action
                    if ball_interaction and ball_interaction.ball_kicked and (is_closest or is_tackle):
                        ball_state.velocity = ball_interaction.new_ball_velocity
                        ball_state.spin = ball_interaction.new_ball_spin

                        # V12 DISABLED: Pass interception was too chaotic
                        # Instead using pressure-based pass failure in action_executor
                        pass

        self.performance_stats['agent_time'] += time.time() - agent_start

        # 2. Update ball physics
        physics_start = time.time()
        ball_state = self.ball_engine.update_ball_state(ball_state, self.config.dt)

        # TUNING: Removed ball velocity damping to allow more contested possession
        # Previously: ball slowed when player near, making retention too easy
        # Now: ball moves freely, enabling opponent to challenge for possession

        self.performance_stats['physics_time'] += time.time() - physics_start

        # 3. Detect events
        event_start = time.time()
        events = self.event_detector.detect_events(
            self.current_time,
            ball_state,
            player_states['home'],
            player_states['away'],
            player_ids['home'],
            player_ids['away'],
            is_home_attacking_left=False  # Home attacks right goal
        )
        self.performance_stats['event_time'] += time.time() - event_start

        # Update time
        self.current_time += self.config.dt
        self.tick_count += 1

        return player_states, ball_state, events

    def _get_player_action(
        self,
        player_state: PlayerState,
        player_id: str,
        player_attrs: Dict,
        player_role: str,
        team: str,
        all_player_states: Dict,
        all_player_ids: Dict,
        ball_state: BallState
    ):
        """Get action for player from agent"""
        # Create PlayerGameState
        has_ball = self._player_has_ball(player_state, ball_state)

        game_player_state = PlayerGameState(
            player_id=player_id,
            position=player_state.position.copy(),
            velocity=player_state.velocity.copy(),
            stamina=player_state.stamina,
            has_ball=has_ball,
            team_id=team,
            role=player_role,
            attributes=player_attrs
        )

        # Create GameContext
        teammates = []
        opponents = []

        # Add teammates
        teammate_team = team
        for i, pid in enumerate(all_player_ids[teammate_team]):
            if pid != player_id:
                teammate = PlayerGameState(
                    player_id=pid,
                    position=all_player_states[teammate_team][i].position.copy(),
                    velocity=all_player_states[teammate_team][i].velocity.copy(),
                    stamina=all_player_states[teammate_team][i].stamina,
                    has_ball=False,
                    team_id=teammate_team,
                    role='CM',  # Simplified
                    attributes={}
                )
                teammates.append(teammate)

        # Add opponents
        opponent_team = 'away' if team == 'home' else 'home'
        for i, pid in enumerate(all_player_ids[opponent_team]):
            opponent = PlayerGameState(
                player_id=pid,
                position=all_player_states[opponent_team][i].position.copy(),
                velocity=all_player_states[opponent_team][i].velocity.copy(),
                stamina=all_player_states[opponent_team][i].stamina,
                has_ball=False,
                team_id=opponent_team,
                role='CM',
                attributes={}
            )
            opponents.append(opponent)

        context = GameContext(
            ball_position=ball_state.position.copy(),
            ball_velocity=ball_state.velocity.copy(),
            teammates=teammates,
            opponents=opponents,
            score=self.score.copy(),
            time_remaining=self.config.duration_seconds - self.current_time,
            is_attacking_left=False if team == 'home' else True
        )

        # PHASE 1: Get team-specific adjustments
        team_adjustments = self.current_adjustments[team] if self.current_adjustments else None

        # Get action (position-specific if enabled)
        if self.config.enable_position_behaviors:
            action = get_position_action(game_player_state, context)
            if action is None:
                action = self.simple_agent.decide_action(game_player_state, context, team_adjustments)
        else:
            action = self.simple_agent.decide_action(game_player_state, context, team_adjustments)

        return action

    def _player_has_ball(self, player_state: PlayerState, ball_state: BallState) -> bool:
        """Check if player has ball"""
        if ball_state.position[2] > 0.5:
            return False

        distance = distance_2d(
            player_state.position[0], player_state.position[1],
            ball_state.position[0], ball_state.position[1]
        )

        return distance < PLAYER_CONTROL_RADIUS

    def _determine_ball_possessor(
        self,
        ball_state: BallState,
        player_states: Dict,
        player_ids: Dict
    ) -> Optional[str]:
        """
        Determine which team (if any) possesses the ball

        Returns:
            'home', 'away', or None
        """
        # Ball in air - no possession
        if ball_state.position[2] > 0.5:
            return None

        ball_pos = ball_state.position[:2]

        # Check all players
        for team in ['home', 'away']:
            for player_state in player_states[team]:
                distance = distance_2d(
                    player_state.position[0],
                    player_state.position[1],
                    ball_pos[0],
                    ball_pos[1]
                )

                if distance < PLAYER_CONTROL_RADIUS:
                    return team

        return None

    def _check_pass_interception(
        self,
        passer_state: PlayerState,
        ball_state: BallState,
        all_player_states: Dict,
        passing_team: str
    ) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        V12: Check if opponents can intercept the pass

        Args:
            passer_state: State of player making the pass
            ball_state: Current ball state (with pass velocity)
            all_player_states: All player states
            passing_team: Team making the pass ('home' or 'away')

        Returns:
            (intercepted, interceptor_team, interceptor_idx)
        """
        # Get pass trajectory
        passer_pos = passer_state.position[:2]
        pass_velocity = ball_state.velocity[:2]
        pass_speed = np.linalg.norm(pass_velocity)

        if pass_speed < 0.1:
            return False, None, None

        pass_direction = pass_velocity / pass_speed

        # Calculate pass distance (assume 1 second of travel for interception check)
        pass_distance = min(pass_speed * 1.0, 40.0)  # Max 40m check distance
        pass_end = passer_pos + pass_direction * pass_distance

        # Check all opponents
        opponent_team = 'away' if passing_team == 'home' else 'home'
        best_interception_prob = 0.0
        best_interceptor_idx = None

        for i, opponent_state in enumerate(all_player_states[opponent_team]):
            opponent_pos = opponent_state.position[:2]

            # Calculate distance from pass line
            # Using vector projection: distance = ||(P - A) - ((P - A) · d) * d||
            to_opponent = opponent_pos - passer_pos
            projection_length = np.dot(to_opponent, pass_direction)

            # Skip if opponent is behind passer or past pass end
            if projection_length < 0 or projection_length > pass_distance:
                continue

            # Distance from pass line
            projection_point = passer_pos + pass_direction * projection_length
            distance_from_line = np.linalg.norm(opponent_pos - projection_point)

            # V12 TUNING: Reduced interception probabilities for better balance
            # Within 2m: moderate chance, 2-5m: low chance, >5m: no chance
            if distance_from_line > 5.0:
                continue

            # Base probability from distance (reduced from original)
            if distance_from_line < 1.5:
                base_prob = 0.35 - (distance_from_line / 1.5) * 0.2  # 35% at 0m, 15% at 1.5m
            elif distance_from_line < 3.0:
                base_prob = 0.15 - ((distance_from_line - 1.5) / 1.5) * 0.1  # 15% at 1.5m, 5% at 3m
            else:
                base_prob = 0.05 - ((distance_from_line - 3.0) / 2.0) * 0.05  # 5% at 3m, 0% at 5m

            # Position along pass (early = easier to intercept)
            position_factor = 1.0 - (projection_length / pass_distance) * 0.2

            # Final probability
            interception_prob = base_prob * position_factor

            if interception_prob > best_interception_prob:
                best_interception_prob = interception_prob
                best_interceptor_idx = i

        # Check if interception occurs
        if best_interceptor_idx is not None and np.random.random() < best_interception_prob:
            return True, opponent_team, best_interceptor_idx

        return False, None, None

    def _handle_event(
        self,
        event: MatchEvent,
        player_states: Dict,
        ball_state: BallState
    ):
        """Handle match event (goal, out of bounds, etc.)"""
        if event.event_type == EventType.GOAL:
            # Update score
            self.score[event.team] += 1

            if self.config.verbose:
                print(f"  ⚽ GOAL! {event.team.upper()} scores at {event.time/60:.1f}min")

            # V8 FIX: Randomize kickoff position to prevent consistent advantage
            # Alternate x position to give each team fair chance
            self.reset_count += 1
            x_offset = 10.0 if self.reset_count % 2 == 0 else -10.0
            y_offset = np.random.uniform(-3.0, 3.0)

            ball_state.position = np.array([x_offset, y_offset, 0.11])
            ball_state.velocity = np.zeros(3)
            ball_state.spin = 0.0

        # V8 FIX: Randomize out-of-bounds resets to prevent one team dominating
        elif event.event_type in [EventType.THROW_IN, EventType.GOAL_KICK, EventType.CORNER]:
            self.reset_count += 1
            # Alternate which team gets advantage (x position closer to their forwards)
            x_offset = 15.0 if self.reset_count % 2 == 0 else -15.0
            y_offset = np.random.uniform(-15.0, 15.0)

            ball_state.position = np.array([x_offset, y_offset, 0.11])
            ball_state.velocity = np.zeros(3)
            ball_state.spin = 0.0

    def _generate_results(self) -> Dict:
        """Generate match results"""
        results = {
            'score': self.score,
            'duration': self.current_time,
            'events': [e.to_dict() for e in self.event_detector.get_all_events()],
            'performance': {
                'total_time': round(self.performance_stats['total_time'], 2),
                'simulation_speed': round(
                    self.config.duration_seconds / max(0.001, self.performance_stats['total_time']),
                    1
                ),
                'ticks': self.performance_stats['total_ticks'],
                'avg_tick_time': round(
                    self.performance_stats['total_time'] * 1000 / max(1, self.performance_stats['total_ticks']),
                    3
                )
            }
        }

        # Add statistics if collected
        if self.statistics:
            self.statistics.process_events(
                self.event_detector.get_all_events(),
                self.current_time
            )
            results['statistics'] = self.statistics.get_summary()
            results['validation'] = self.statistics.validate_realism()

        return results


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    'SimulationConfig',
    'GameSimulator'
]
