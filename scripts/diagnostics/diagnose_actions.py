#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Diagnostic: Track Player Actions
See what actions players are choosing when ball is stuck
"""

import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from simulation.game_simulator import GameSimulator, SimulationConfig
from physics.ball_physics import BallState
from agents.actions import ActionType

def create_test_player_dict(player_id='p1', position=(0, 0), role='CM'):
    return {
        'id': player_id,
        'position': position,
        'role': role,
        'attributes': {
            'pace': 75,
            'shooting': 70,
            'passing': 80,
            'dribbling': 75,
            'defending': 60,
            'physical': 70,
            'stamina': 80
        }
    }

def create_test_formation(team_prefix='h', x_offset=0):
    players = []
    # GK
    players.append(create_test_player_dict(f'{team_prefix}_gk', (x_offset - 40, 0), 'GK'))
    # Defenders
    for i, y in enumerate([-20, -7, 7, 20]):
        players.append(create_test_player_dict(
            f'{team_prefix}_df{i}',
            (x_offset - 30, y),
            'CB' if abs(y) < 15 else 'FB'
        ))
    # Midfielders
    for i, y in enumerate([-10, 0, 10]):
        players.append(create_test_player_dict(
            f'{team_prefix}_mf{i}',
            (x_offset - 15, y),
            'CM'
        ))
    # Forwards
    for i, y in enumerate([-15, 0, 15]):
        players.append(create_test_player_dict(
            f'{team_prefix}_fw{i}',
            (x_offset + 15, y),
            'ST' if y == 0 else 'WG'
        ))
    return players

# Create teams
home_players = create_test_formation('h', x_offset=0)
away_players = create_test_formation('a', x_offset=0)

# Mirror away team
for player in away_players:
    player['position'] = (-player['position'][0], player['position'][1])

# Very short simulation for detailed action logging
config = SimulationConfig(
    duration_seconds=60.0,  # 1 minute
    dt=0.1,
    enable_agents=True,
    enable_position_behaviors=True,
    collect_statistics=True,
    verbose=False
)

print("="*70)
print("ADVANCED DIAGNOSTIC: Player Action Tracking (1 minute)")
print("="*70)

# Custom simulator to track actions
class ActionDiagnosticSimulator(GameSimulator):
    def __init__(self, config):
        super().__init__(config)
        self.action_log = []
        self.last_sample_time = 0

    def _get_player_action(self, player_state, player_id, player_attrs, player_role,
                          team, all_player_states, all_player_ids, ball_state):
        # Call parent to get action
        action = super()._get_player_action(
            player_state, player_id, player_attrs, player_role,
            team, all_player_states, all_player_ids, ball_state
        )

        # Sample actions starting at 48s (every tick)
        if self.current_time >= 48.0:
            # Check if this player is close to ball
            ball_pos = ball_state.position[:2]
            player_pos = player_state.position
            dist_to_ball = np.sqrt((player_pos[0] - ball_pos[0])**2 + (player_pos[1] - ball_pos[1])**2)

            if dist_to_ball < 15.0:  # Log players within 15m of ball
                # Calculate has_ball manually
                from physics.constants import PLAYER_CONTROL_RADIUS
                has_ball = (ball_state.position[2] < 0.5 and dist_to_ball < PLAYER_CONTROL_RADIUS)

                self.action_log.append({
                    'time': self.current_time,
                    'player_id': player_id,
                    'team': team,
                    'role': player_role,
                    'position': (float(player_pos[0]), float(player_pos[1])),
                    'ball_position': (float(ball_pos[0]), float(ball_pos[1])),
                    'distance_to_ball': float(dist_to_ball),
                    'action_type': action.action_type.value if action else 'none',
                    'has_ball': has_ball
                })

        return action

    def _simulate_tick(self, player_states, player_ids, player_attrs, player_roles, ball_state):
        # Sample ball state every 5 seconds starting at 45s
        if self.current_time >= 45 and (self.current_time - self.last_sample_time >= 5.0 or
                                        (self.current_time >= 50 and self.last_sample_time == 0)):
            x, y, h = ball_state.position
            speed = np.linalg.norm(ball_state.velocity)
            print(f"\n[{self.current_time:.1f}s] Ball: ({x:.1f}, {y:.1f}, {h:.2f}), Speed: {speed:.1f} m/s")

            # Print player actions
            if self.action_log:
                print(f"  Player Actions (within 20m of ball):")
                recent_actions = [log for log in self.action_log if abs(log['time'] - self.current_time) < 1.0]
                for log in sorted(recent_actions, key=lambda x: x['distance_to_ball'])[:10]:
                    print(f"    {log['player_id']} ({log['role']}): {log['action_type']}, dist={log['distance_to_ball']:.1f}m")

            self.last_sample_time = self.current_time

        return super()._simulate_tick(player_states, player_ids, player_attrs, player_roles, ball_state)

# Run diagnostic simulation
simulator = ActionDiagnosticSimulator(config)
results = simulator.simulate_match(home_players, away_players, 'Home', 'Away')

print("\n" + "="*70)
print("ACTION DIAGNOSTIC SUMMARY")
print("="*70)

# Group actions by type
action_counts = {}
for log in simulator.action_log:
    action_type = log['action_type']
    action_counts[action_type] = action_counts.get(action_type, 0) + 1

print("\nAction Distribution (players within 20m of ball, after 45s):")
for action_type, count in sorted(action_counts.items(), key=lambda x: -x[1]):
    print(f"  {action_type}: {count}")

# Find ball-stuck period actions
stuck_period_actions = [log for log in simulator.action_log if log['time'] >= 45]
print(f"\nTotal action samples during stuck period (45s+): {len(stuck_period_actions)}")

if stuck_period_actions:
    # Check if players are choosing CHASE_BALL
    chase_actions = [log for log in stuck_period_actions if log['action_type'] == 'chase_ball']
    print(f"CHASE_BALL actions: {len(chase_actions)}/{len(stuck_period_actions)} ({len(chase_actions)/max(1,len(stuck_period_actions))*100:.1f}%)")

    # Check average distance to ball
    avg_dist = sum(log['distance_to_ball'] for log in stuck_period_actions) / len(stuck_period_actions)
    print(f"Average distance to ball: {avg_dist:.1f}m")

print("\n" + "="*70)
