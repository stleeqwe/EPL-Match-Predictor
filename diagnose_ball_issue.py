#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnostic Script: Track Ball Behavior
Find out why ball control collapses after first minute
"""

import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from simulation.game_simulator import GameSimulator, SimulationConfig
from physics.ball_physics import BallState

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

# Short 2-minute simulation with diagnostics
config = SimulationConfig(
    duration_seconds=120.0,  # 2 minutes
    dt=0.1,
    enable_agents=True,
    enable_position_behaviors=True,
    collect_statistics=True,
    verbose=True  # Enable verbose to see goals
)

print("="*70)
print("DIAGNOSTIC: Ball Position Tracking (2 minutes)")
print("="*70)

# Create custom simulator to intercept ball state
class DiagnosticSimulator(GameSimulator):
    def __init__(self, config):
        super().__init__(config)
        self.ball_positions = []
        self.ball_out_of_bounds_count = 0
        self.last_sample_time = 0

    def _simulate_tick(self, player_states, player_ids, player_attrs, player_roles, ball_state):
        # Sample every 10 seconds
        if self.current_time - self.last_sample_time >= 10.0:
            x, y, h = ball_state.position
            speed = np.linalg.norm(ball_state.velocity)

            # Check if out of bounds
            out_of_bounds = (
                x < -52.5 or x > 52.5 or
                y < -34.0 or y > 34.0
            )

            if out_of_bounds:
                self.ball_out_of_bounds_count += 1

            print(f"\n[{self.current_time:.1f}s] Ball position: ({x:.1f}, {y:.1f}, {h:.2f})")
            print(f"  Speed: {speed:.1f} m/s")
            print(f"  Out of bounds: {out_of_bounds}")
            print(f"  Total OOB events: {self.ball_out_of_bounds_count}")

            # Find closest players
            min_dist_home = float('inf')
            min_dist_away = float('inf')

            for player in player_states['home']:
                dist = np.sqrt((player.position[0] - x)**2 + (player.position[1] - y)**2)
                min_dist_home = min(min_dist_home, dist)

            for player in player_states['away']:
                dist = np.sqrt((player.position[0] - x)**2 + (player.position[1] - y)**2)
                min_dist_away = min(min_dist_away, dist)

            print(f"  Closest home player: {min_dist_home:.1f}m")
            print(f"  Closest away player: {min_dist_away:.1f}m")

            self.last_sample_time = self.current_time
            self.ball_positions.append((self.current_time, x, y, h, speed, out_of_bounds))

        # Call parent implementation
        return super()._simulate_tick(player_states, player_ids, player_attrs, player_roles, ball_state)

# Run diagnostic simulation
simulator = DiagnosticSimulator(config)
results = simulator.simulate_match(home_players, away_players, 'Home', 'Away')

print("\n" + "="*70)
print("DIAGNOSTIC SUMMARY")
print("="*70)

print(f"\nBall Samples: {len(simulator.ball_positions)}")
print(f"Total OOB detections: {simulator.ball_out_of_bounds_count}")

# Count how many times ball was truly out of bounds
oob_count = sum(1 for _, x, y, h, speed, oob in simulator.ball_positions if oob)
print(f"Samples with ball OOB: {oob_count}/{len(simulator.ball_positions)}")

# Statistics
stats = results.get('statistics', {})
if stats:
    print(f"\nMatch Statistics:")
    print(f"  Home shots: {stats['home']['shots']}")
    print(f"  Away shots: {stats['away']['shots']}")
    print(f"  Home possession: {stats['home']['possession_percent']:.1f}%")
    print(f"  Away possession: {stats['away']['possession_percent']:.1f}%")

# Event breakdown
events = results.get('events', [])
event_types = {}
for event in events:
    event_type = event['event_type']
    event_types[event_type] = event_types.get(event_type, 0) + 1

print(f"\nEvent Breakdown ({len(events)} total):")
for event_type, count in sorted(event_types.items(), key=lambda x: -x[1]):
    print(f"  {event_type}: {count}")

print("\n" + "="*70)
