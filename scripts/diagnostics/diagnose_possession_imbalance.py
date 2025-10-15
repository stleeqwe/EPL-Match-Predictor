#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnose Possession Imbalance
Why is possession 98.7% vs 1.2%?
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
print("POSSESSION IMBALANCE DIAGNOSTIC")
print("=" * 70)

# Create teams
print("\n1. Creating teams and checking formations...")
home_players = create_test_formation('h', x_offset=0)
away_players = create_test_formation('a', x_offset=0)

# Mirror away team
for player in away_players:
    player['position'] = (-player['position'][0], player['position'][1])

print("\nHome team positions:")
for player in home_players:
    print(f"  {player['id']:8s} ({player['role']:2s}): ({player['position'][0]:6.1f}, {player['position'][1]:6.1f})")

print("\nAway team positions (should be mirrored):")
for player in away_players:
    print(f"  {player['id']:8s} ({player['role']:2s}): ({player['position'][0]:6.1f}, {player['position'][1]:6.1f})")

# Ball starts at (0, 0)
print(f"\n2. Ball starting position: (0.0, 0.0, 0.11)")

# Find closest players to ball
print("\n3. Closest players to ball at kickoff:")
ball_pos = np.array([0.0, 0.0])

home_distances = []
for player in home_players:
    pos = np.array(player['position'])
    dist = np.linalg.norm(pos - ball_pos)
    home_distances.append((player['id'], player['role'], dist))

away_distances = []
for player in away_players:
    pos = np.array(player['position'])
    dist = np.linalg.norm(pos - ball_pos)
    away_distances.append((player['id'], player['role'], dist))

home_distances.sort(key=lambda x: x[2])
away_distances.sort(key=lambda x: x[2])

print("\nHome team (closest 3):")
for pid, role, dist in home_distances[:3]:
    print(f"  {pid:8s} ({role:2s}): {dist:6.1f}m from ball")

print("\nAway team (closest 3):")
for pid, role, dist in away_distances[:3]:
    print(f"  {pid:8s} ({role:2s}): {dist:6.1f}m from ball")

closest_home = home_distances[0][2]
closest_away = away_distances[0][2]
print(f"\nClosest player: {'HOME' if closest_home < closest_away else 'AWAY'} ({min(closest_home, closest_away):.1f}m)")

# Run short simulation to see possession evolution
print("\n4. Running 30-second simulation to observe possession evolution...")

config = SimulationConfig(
    duration_seconds=30.0,
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

print(f"\nResults after 30 seconds:")
print(f"  Home possession: {stats['home']['possession_percent']:.1f}%")
print(f"  Away possession: {stats['away']['possession_percent']:.1f}%")

# Count possession changes
possession_changes = [e for e in events if e['event_type'] == 'possession_change']
print(f"  Possession changes: {len(possession_changes)}")

# Show first 10 possession changes
if possession_changes:
    print(f"\n  First 10 possession changes:")
    for i, event in enumerate(possession_changes[:10]):
        print(f"    {event['time']:5.1f}s - {event['team'].upper()}")

print("\n" + "=" * 70)
print("DIAGNOSIS")
print("=" * 70)

# Analyze
print("\nPossible causes of imbalance:")

if stats['home']['possession_percent'] > 80 or stats['away']['possession_percent'] > 80:
    dominant_team = 'HOME' if stats['home']['possession_percent'] > 80 else 'AWAY'
    print(f"\n✗ {dominant_team} team dominates possession ({stats[dominant_team.lower()]['possession_percent']:.1f}%)")

    if closest_home < closest_away - 5:
        print(f"  → Home team starts 5m+ closer to ball")
        print(f"  → Recommendation: Randomize ball starting position")
    elif closest_away < closest_home - 5:
        print(f"  → Away team starts 5m+ closer to ball")
        print(f"  → Recommendation: Randomize ball starting position")
    else:
        print(f"  → Teams equally distant from ball start")
        print(f"  → Issue may be in ball chase/retention behavior")

    if len(possession_changes) < 10:
        print(f"  → Very few possession changes ({len(possession_changes)})")
        print(f"  → Dominant team retains ball too easily")
        print(f"  → Recommendation: Improve opponent pressing/tackling")
else:
    print("\n✓ Possession appears balanced in 30s test")
    print("  → Imbalance may develop over longer matches")
    print("  → Check for reset/restart issues")

print("\n" + "=" * 70)
