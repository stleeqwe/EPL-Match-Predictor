#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnose Home vs Away Team Bias
Why does Away team dominate regardless of position?
"""

import sys
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
print("HOME vs AWAY BIAS DIAGNOSTIC")
print("=" * 70)

# Create identical teams
team_a = create_test_formation('a', x_offset=0)
team_b = create_test_formation('b', x_offset=0)

# Mirror team_b to negative x
for player in team_b:
    player['position'] = (-player['position'][0], player['position'][1])

config = SimulationConfig(
    duration_seconds=300.0,  # 5 minutes
    dt=0.1,
    enable_agents=True,
    enable_position_behaviors=True,
    collect_statistics=True,
    verbose=False
)

print("\nTest 1: Team A as Home, Team B as Away")
print("-" * 70)
simulator1 = GameSimulator(config)
result1 = simulator1.simulate_match(team_a, team_b, 'TeamA', 'TeamB')
stats1 = result1.get('statistics', {})

print(f"  Home (Team A): {stats1['home']['possession_percent']:.1f}%")
print(f"  Away (Team B): {stats1['away']['possession_percent']:.1f}%")

# Test 2: SWAP TEAM ROLES (same positions, different labels)
print("\nTest 2: Team B as Home, Team A as Away (SWAPPED ROLES)")
print("-" * 70)
simulator2 = GameSimulator(config)
result2 = simulator2.simulate_match(team_b, team_a, 'TeamB', 'TeamA')
stats2 = result2.get('statistics', {})

print(f"  Home (Team B): {stats2['home']['possession_percent']:.1f}%")
print(f"  Away (Team A): {stats2['away']['possession_percent']:.1f}%")

# Analysis
print("\n" + "=" * 70)
print("ANALYSIS")
print("=" * 70)

team_a_as_home = stats1['home']['possession_percent']
team_a_as_away = stats2['away']['possession_percent']
team_b_as_home = stats2['home']['possession_percent']
team_b_as_away = stats1['away']['possession_percent']

print(f"\nTeam A performance:")
print(f"  As Home: {team_a_as_home:.1f}%")
print(f"  As Away: {team_a_as_away:.1f}%")
print(f"  Difference: {abs(team_a_as_home - team_a_as_away):.1f}%")

print(f"\nTeam B performance:")
print(f"  As Home: {team_b_as_home:.1f}%")
print(f"  As Away: {team_b_as_away:.1f}%")
print(f"  Difference: {abs(team_b_as_home - team_b_as_away):.1f}%")

avg_home_poss = (team_a_as_home + team_b_as_home) / 2
avg_away_poss = (team_a_as_away + team_b_as_away) / 2

print(f"\nAverage possession by role:")
print(f"  Home team: {avg_home_poss:.1f}%")
print(f"  Away team: {avg_away_poss:.1f}%")

if abs(avg_home_poss - avg_away_poss) > 20:
    if avg_home_poss > avg_away_poss:
        print(f"\n✗ HOME TEAM BIAS DETECTED!")
        print(f"  → Home teams average {avg_home_poss:.1f}% vs Away {avg_away_poss:.1f}%")
    else:
        print(f"\n✗ AWAY TEAM BIAS DETECTED!")
        print(f"  → Away teams average {avg_away_poss:.1f}% vs Home {avg_home_poss:.1f}%")
else:
    print(f"\n✓ No systematic Home/Away bias")
    print(f"  → Both roles perform similarly")

print("\n" + "=" * 70)
