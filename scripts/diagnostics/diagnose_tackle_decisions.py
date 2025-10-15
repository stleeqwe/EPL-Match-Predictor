#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnose Tackle Decisions
Track what actions agents choose when opponent has ball nearby
"""

import sys
import numpy as np
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from simulation.game_simulator import GameSimulator, SimulationConfig
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
    # Defenders (4)
    for i, y in enumerate([-20, -7, 7, 20]):
        players.append(create_test_player_dict(
            f'{team_prefix}_df{i}',
            (x_offset - 30, y),
            'CB' if abs(y) < 15 else 'FB'
        ))
    # Midfielders (3)
    for i, y in enumerate([-10, 0, 10]):
        players.append(create_test_player_dict(
            f'{team_prefix}_mf{i}',
            (x_offset - 15, y),
            'CM'
        ))
    # Forwards (3)
    for i, y in enumerate([-15, 0, 15]):
        players.append(create_test_player_dict(
            f'{team_prefix}_fw{i}',
            (x_offset + 15, y),
            'ST' if y == 0 else 'WG'
        ))
    return players

# Monkey-patch SimpleAgent to track decisions
from agents.simple_agent import SimpleAgent

original_decide_without_ball = SimpleAgent._decide_without_ball

action_choices = Counter()
action_choices_near_ball = Counter()  # When within 5m of ball
action_choices_vs_opponent_with_ball = Counter()  # When opponent has ball

def tracked_decide_without_ball(self, player_state, game_context):
    # Call original
    action = original_decide_without_ball(self, player_state, game_context)

    # Track decision
    action_type_name = action.action_type.name if hasattr(action.action_type, 'name') else str(action.action_type)
    action_choices[action_type_name] += 1

    # Check distance to ball
    from physics.constants import distance_2d
    distance_to_ball = distance_2d(
        player_state.position[0], player_state.position[1],
        game_context.ball_position[0], game_context.ball_position[1]
    )

    if distance_to_ball < 5.0:
        action_choices_near_ball[action_type_name] += 1

    # Check if opponent has ball
    for opp in game_context.opponents:
        dist_to_opp = distance_2d(
            opp.position[0], opp.position[1],
            game_context.ball_position[0], game_context.ball_position[1]
        )
        if dist_to_opp < 1.5:  # Opponent has ball
            if distance_to_ball < 5.0:  # We're close to ball
                action_choices_vs_opponent_with_ball[action_type_name] += 1
            break

    return action

SimpleAgent._decide_without_ball = tracked_decide_without_ball

print("=" * 70)
print("TACKLE DECISION DIAGNOSTIC")
print("=" * 70)

# Create teams
home_players = create_test_formation('h', x_offset=0)
away_players = create_test_formation('a', x_offset=0)

# Mirror away team
for player in away_players:
    player['position'] = (-player['position'][0], player['position'][1])

print("\nRunning 2-minute simulation to track agent decisions...")

config = SimulationConfig(
    duration_seconds=120.0,  # 2 minutes
    dt=0.1,
    enable_agents=True,
    enable_position_behaviors=True,
    collect_statistics=True,
    verbose=False
)

simulator = GameSimulator(config)
results = simulator.simulate_match(home_players, away_players, 'Home', 'Away')

print("\n" + "=" * 70)
print("DECISION ANALYSIS")
print("=" * 70)

print("\n1. All actions chosen (when player doesn't have ball):")
for action_type, count in action_choices.most_common():
    print(f"  {action_type:20s}: {count:5d} times")

print("\n2. Actions chosen when within 5m of ball:")
if action_choices_near_ball:
    for action_type, count in action_choices_near_ball.most_common():
        print(f"  {action_type:20s}: {count:5d} times")
else:
    print("  No decisions within 5m of ball")

print("\n3. Actions chosen when opponent has ball (player within 5m):")
if action_choices_vs_opponent_with_ball:
    for action_type, count in action_choices_vs_opponent_with_ball.most_common():
        print(f"  {action_type:20s}: {count:5d} times")
else:
    print("  No decisions when opponent had ball nearby")

print("\n" + "=" * 70)
print("CRITICAL FINDINGS")
print("=" * 70)

# Check if TACKLE was ever chosen
tackle_count = action_choices.get('TACKLE', 0)
tackle_near_ball = action_choices_near_ball.get('TACKLE', 0)
tackle_vs_opponent = action_choices_vs_opponent_with_ball.get('TACKLE', 0)

print(f"\nTACKLE actions chosen:")
print(f"  Total: {tackle_count}")
print(f"  Near ball (<5m): {tackle_near_ball}")
print(f"  When opponent has ball: {tackle_vs_opponent}")

if tackle_count == 0:
    print("\n✗ CRITICAL ISSUE FOUND!")
    print("  → TACKLE action is NEVER chosen by agent")
    print("  → Agent implementation missing tackle decision logic")
    print("  → This explains why opponent can't win ball back")
    print("  → Fix: Add tackle action to _decide_without_ball()")
else:
    print(f"\n✓ TACKLE actions are being chosen ({tackle_count} times)")
    if tackle_vs_opponent == 0:
        print("  → But not when opponent has ball!")

print("\n" + "=" * 70)
