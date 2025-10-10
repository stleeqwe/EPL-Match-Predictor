#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnose Goal Reset Behavior
Track what happens after goals are scored
"""

import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from simulation.game_simulator import GameSimulator, SimulationConfig

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

print("=" * 70)
print("GOAL RESET DIAGNOSTIC")
print("=" * 70)

# Create teams
home_players = create_test_formation('h', x_offset=0)
away_players = create_test_formation('a', x_offset=0)

# Mirror away team
for player in away_players:
    player['position'] = (-player['position'][0], player['position'][1])

print("\nRunning 10-minute simulation to capture goals...")

config = SimulationConfig(
    duration_seconds=600.0,  # 10 minutes
    dt=0.1,
    enable_agents=True,
    enable_position_behaviors=True,
    collect_statistics=True,
    verbose=False
)

simulator = GameSimulator(config)
results = simulator.simulate_match(home_players, away_players, 'Home', 'Away')

# Analyze events around goals
events = results['events']
goals = [e for e in events if e['event_type'] == 'goal']
possession_changes = [e for e in events if e['event_type'] == 'possession_change']

print("\n" + "=" * 70)
print("GOAL ANALYSIS")
print("=" * 70)

print(f"\nTotal goals: {len(goals)}")

for i, goal in enumerate(goals):
    print(f"\nGoal {i+1}:")
    print(f"  Time: {goal['time']/60:.1f} min")
    print(f"  Scored by: {goal['team'].upper()}")

    # Find possession changes within 10 seconds after goal
    goal_time = goal['time']
    after_goal = [e for e in possession_changes
                  if goal_time < e['time'] <= goal_time + 10.0]

    if after_goal:
        print(f"  Possession changes in next 10s: {len(after_goal)}")
        first_possession = after_goal[0]
        print(f"  First possession after reset: {first_possession['team'].upper()} "
              f"(at {(first_possession['time'] - goal_time):.1f}s after goal)")
    else:
        print(f"  No possession changes in next 10s")
        # Check next possession change whenever it happens
        later_changes = [e for e in possession_changes if e['time'] > goal_time]
        if later_changes:
            next_change = later_changes[0]
            print(f"  Next possession change: {next_change['team'].upper()} "
                  f"(at {(next_change['time'] - goal_time):.1f}s after goal)")

print("\n" + "=" * 70)
print("PATTERN ANALYSIS")
print("=" * 70)

# Count who gets ball after goals
scoring_team_keeps = 0
conceding_team_gets = 0

for goal in goals:
    goal_time = goal['time']
    scoring_team = goal['team']

    # Find next possession change
    later_changes = [e for e in possession_changes if e['time'] > goal_time]
    if later_changes:
        next_possession = later_changes[0]
        if next_possession['team'] == scoring_team:
            scoring_team_keeps += 1
        else:
            conceding_team_gets += 1

if len(goals) > 0:
    print(f"\nAfter goals ({len(goals)} total):")
    print(f"  Scoring team keeps ball: {scoring_team_keeps} times")
    print(f"  Conceding team gets ball: {conceding_team_gets} times")

    if scoring_team_keeps > conceding_team_gets:
        print("\n✗ PROBLEM FOUND!")
        print("  → Scoring team keeps winning possession after goals")
        print("  → This creates positive feedback loop (rich get richer)")
        print("  → Fix: Ensure conceding team gets kickoff after goal")
    elif conceding_team_gets > scoring_team_keeps:
        print("\n✓ Normal pattern")
        print("  → Conceding team gets kickoff (standard rule)")
    else:
        print("\n⚠️ Mixed pattern")

print("\n" + "=" * 70)
