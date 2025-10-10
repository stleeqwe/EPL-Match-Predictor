#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test 5-Minute Match with V7 Tackle Fix
Verify possession balance improvement
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
print("5-MINUTE POSSESSION BALANCE TEST (V7 - With Tackle Fix)")
print("=" * 70)

# Create teams
home_players = create_test_formation('h', x_offset=0)
away_players = create_test_formation('a', x_offset=0)

# Mirror away team
for player in away_players:
    player['position'] = (-player['position'][0], player['position'][1])

print("\nRunning 5-minute simulation with V7 tackle fix...")

config = SimulationConfig(
    duration_seconds=300.0,  # 5 minutes
    dt=0.1,
    enable_agents=True,
    enable_position_behaviors=True,
    collect_statistics=True,
    verbose=False
)

simulator = GameSimulator(config)
results = simulator.simulate_match(home_players, away_players, 'Home', 'Away')

stats = results.get('statistics', {})
events = results['events']

print("\n" + "=" * 70)
print("RESULTS")
print("=" * 70)

home_poss = stats['home']['possession_percent']
away_poss = stats['away']['possession_percent']
total_poss = home_poss + away_poss

print(f"\nPossession:")
print(f"  Home: {home_poss:.1f}%")
print(f"  Away: {away_poss:.1f}%")
print(f"  Total: {total_poss:.1f}%")

print(f"\nShots:")
print(f"  Home: {stats['home']['shots']}")
print(f"  Away: {stats['away']['shots']}")
print(f"  Total: {stats['home']['shots'] + stats['away']['shots']}")

possession_changes = [e for e in events if e['event_type'] == 'possession_change']
print(f"\nPossession changes: {len(possession_changes)} ({len(possession_changes)/5:.1f}/min)")

# Analyze balance
print("\n" + "=" * 70)
print("BALANCE ANALYSIS")
print("=" * 70)

balanced = (30 <= home_poss <= 70 and 30 <= away_poss <= 70)

if balanced:
    print("\n✓ Possession is BALANCED!")
    print(f"  → Home: {home_poss:.1f}% (30-70% range)")
    print(f"  → Away: {away_poss:.1f}% (30-70% range)")
    print(f"  → V7 tackle fix SUCCESSFUL!")
else:
    print("\n✗ Possession still imbalanced")
    print(f"  → Home: {home_poss:.1f}%")
    print(f"  → Away: {away_poss:.1f}%")

    if home_poss > 70:
        print(f"  → Home dominates (+{home_poss-70:.1f}% over threshold)")
    elif away_poss > 70:
        print(f"  → Away dominates (+{away_poss-70:.1f}% over threshold)")

print("\n" + "=" * 70)
