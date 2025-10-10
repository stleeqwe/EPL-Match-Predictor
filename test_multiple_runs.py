#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Multiple Runs
Run 5 matches and check possession balance consistency
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
print("MULTIPLE RUNS TEST (V8 - Randomized Resets)")
print("=" * 70)

results_list = []

for run in range(5):
    print(f"\n{'='*70}")
    print(f"RUN {run + 1}/5")
    print(f"{'='*70}")

    # Create teams
    home_players = create_test_formation('h', x_offset=0)
    away_players = create_test_formation('a', x_offset=0)

    # Mirror away team
    for player in away_players:
        player['position'] = (-player['position'][0], player['position'][1])

    config = SimulationConfig(
        duration_seconds=300.0,  # 5 minutes
        dt=0.1,
        enable_agents=True,
        enable_position_behaviors=True,
        collect_statistics=True,
        verbose=False
    )

    simulator = GameSimulator(config)
    results = simulator.simulate_match(home_players, away_players, f'Home{run+1}', f'Away{run+1}')

    stats = results.get('statistics', {})
    home_poss = stats['home']['possession_percent']
    away_poss = stats['away']['possession_percent']

    results_list.append({
        'home': home_poss,
        'away': away_poss,
        'balanced': (30 <= home_poss <= 70 and 30 <= away_poss <= 70)
    })

    print(f"  Home: {home_poss:.1f}%")
    print(f"  Away: {away_poss:.1f}%")
    print(f"  {'✓ Balanced' if results_list[-1]['balanced'] else '✗ Imbalanced'}")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

import numpy as np

home_possessions = [r['home'] for r in results_list]
away_possessions = [r['away'] for r in results_list]
balanced_count = sum(1 for r in results_list if r['balanced'])

print(f"\nHome possession: {np.mean(home_possessions):.1f}% ± {np.std(home_possessions):.1f}%")
print(f"Away possession: {np.mean(away_possessions):.1f}% ± {np.std(away_possessions):.1f}%")
print(f"\nBalanced matches: {balanced_count}/5 ({balanced_count/5*100:.0f}%)")

if balanced_count >= 4:
    print("\n✓ V8 FIX SUCCESSFUL!")
    print("  → 80%+ of matches are balanced")
elif balanced_count >= 3:
    print("\n⚠️ PARTIAL SUCCESS")
    print(f"  → {balanced_count}/5 matches balanced")
    print("  → May need additional tuning")
else:
    print("\n✗ V8 FIX INSUFFICIENT")
    print(f"  → Only {balanced_count}/5 matches balanced")
    print("  → Need different approach")

print("\n" + "=" * 70)
