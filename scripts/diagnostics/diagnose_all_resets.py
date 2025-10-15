#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnose All Ball Reset Events
Track all ball resets and who wins possession after
"""

import sys
import numpy as np
from pathlib import Path
from collections import Counter

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
print("ALL BALL RESETS DIAGNOSTIC")
print("=" * 70)

# Create teams
home_players = create_test_formation('h', x_offset=0)
away_players = create_test_formation('a', x_offset=0)

# Mirror away team
for player in away_players:
    player['position'] = (-player['position'][0], player['position'][1])

print("\nTeam positioning:")
print(f"  Home forwards: x = +15 (distance to center: 15m)")
print(f"  Away forwards: x = -15 (distance to center: 15m)")
print(f"  Ball reset position: (0, 0)")
print(f"  → Both teams equidistant from reset ✓")

print("\nRunning 10-minute simulation...")

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

# Analyze reset events
events = results['events']

reset_events = [e for e in events if e['event_type'] in
                ['goal', 'throw_in', 'goal_kick', 'corner']]
possession_changes = [e for e in events if e['event_type'] == 'possession_change']

print("\n" + "=" * 70)
print("RESET EVENT ANALYSIS")
print("=" * 70)

event_counts = Counter(e['event_type'] for e in reset_events)
print(f"\nReset events by type:")
for event_type, count in event_counts.most_common():
    print(f"  {event_type:<15}: {count:>5}")

print(f"\nTotal resets: {len(reset_events)}")
print(f"Total possession changes: {len(possession_changes)}")

# Track who wins ball after each reset type
reset_analysis = {
    'goal': {'home': 0, 'away': 0, 'none': 0},
    'throw_in': {'home': 0, 'away': 0, 'none': 0},
    'goal_kick': {'home': 0, 'away': 0, 'none': 0},
    'corner': {'home': 0, 'away': 0, 'none': 0}
}

for reset_event in reset_events:
    reset_time = reset_event['time']
    reset_type = reset_event['event_type']

    # Find next possession change within 15 seconds
    next_possessions = [e for e in possession_changes
                       if reset_time < e['time'] <= reset_time + 15.0]

    if next_possessions:
        first_team = next_possessions[0]['team']
        reset_analysis[reset_type][first_team] += 1
    else:
        reset_analysis[reset_type]['none'] += 1

print("\n" + "=" * 70)
print("WHO WINS BALL AFTER RESETS")
print("=" * 70)

for event_type in ['goal', 'throw_in', 'goal_kick', 'corner']:
    data = reset_analysis[event_type]
    total = data['home'] + data['away'] + data['none']

    if total > 0:
        print(f"\n{event_type.upper()} ({total} events):")
        print(f"  Home wins ball: {data['home']} ({data['home']/total*100:.1f}%)")
        print(f"  Away wins ball: {data['away']} ({data['away']/total*100:.1f}%)")
        print(f"  No winner (15s): {data['none']} ({data['none']/total*100:.1f}%)")

        # Check balance
        if data['home'] > data['away'] * 1.5:
            print(f"  ✗ HOME heavily favored")
        elif data['away'] > data['home'] * 1.5:
            print(f"  ✗ AWAY heavily favored")
        elif data['home'] > 0 or data['away'] > 0:
            print(f"  ✓ Relatively balanced")

print("\n" + "=" * 70)
print("OVERALL PATTERN")
print("=" * 70)

total_home = sum(data['home'] for data in reset_analysis.values())
total_away = sum(data['away'] for data in reset_analysis.values())
total_resets = total_home + total_away

if total_resets > 0:
    print(f"\nAll resets combined:")
    print(f"  Home wins: {total_home} ({total_home/total_resets*100:.1f}%)")
    print(f"  Away wins: {total_away} ({total_away/total_resets*100:.1f}%)")

    if abs(total_home - total_away) / total_resets > 0.2:  # >20% difference
        print(f"\n✗ CRITICAL IMBALANCE FOUND!")
        if total_home > total_away:
            print(f"  → HOME wins {total_home - total_away} more resets than AWAY")
            print(f"  → This creates positive feedback loop")
        else:
            print(f"  → AWAY wins {total_away - total_home} more resets than HOME")
            print(f"  → This creates positive feedback loop")
    else:
        print(f"\n✓ Reset ball wins are balanced")

print("\n" + "=" * 70)
