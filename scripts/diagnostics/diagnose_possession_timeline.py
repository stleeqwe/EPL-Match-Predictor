#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnose Possession Timeline
Track how possession balance changes over time
"""

import sys
import numpy as np
from pathlib import Path
from collections import defaultdict

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
print("POSSESSION TIMELINE DIAGNOSTIC")
print("Track possession changes over 30-minute match")
print("=" * 70)

# Create teams
home_players = create_test_formation('h', x_offset=0)
away_players = create_test_formation('a', x_offset=0)

# Mirror away team
for player in away_players:
    player['position'] = (-player['position'][0], player['position'][1])

print("\nRunning 30-minute simulation...")

config = SimulationConfig(
    duration_seconds=1800.0,  # 30 minutes
    dt=0.1,
    enable_agents=True,
    enable_position_behaviors=True,
    collect_statistics=True,
    verbose=False
)

simulator = GameSimulator(config)
results = simulator.simulate_match(home_players, away_players, 'Home', 'Away')

# Analyze possession changes by time interval
events = results['events']
possession_events = [e for e in events if e['event_type'] == 'possession_change']

print("\n" + "=" * 70)
print("TIMELINE ANALYSIS")
print("=" * 70)

# Track possession by 5-minute intervals
intervals = {
    '0-5min': {'home': 0, 'away': 0, 'changes': 0},
    '5-10min': {'home': 0, 'away': 0, 'changes': 0},
    '10-15min': {'home': 0, 'away': 0, 'changes': 0},
    '15-20min': {'home': 0, 'away': 0, 'changes': 0},
    '20-25min': {'home': 0, 'away': 0, 'changes': 0},
    '25-30min': {'home': 0, 'away': 0, 'changes': 0}
}

interval_keys = list(intervals.keys())

for i, event in enumerate(possession_events):
    time_min = event['time'] / 60.0

    # Determine interval
    if time_min < 5:
        interval = '0-5min'
    elif time_min < 10:
        interval = '5-10min'
    elif time_min < 15:
        interval = '10-15min'
    elif time_min < 20:
        interval = '15-20min'
    elif time_min < 25:
        interval = '20-25min'
    else:
        interval = '25-30min'

    # Track possession change
    intervals[interval]['changes'] += 1

    # Track possession duration (time to next change or end)
    start_time = event['time']
    if i + 1 < len(possession_events):
        end_time = possession_events[i + 1]['time']
    else:
        end_time = 1800.0  # Match end

    duration = end_time - start_time
    intervals[interval][event['team']] += duration

print("\nPossession by 5-minute intervals:")
print(f"{'Interval':<12} {'Home %':<10} {'Away %':<10} {'Changes':<10} {'Balance'}")
print("-" * 70)

for key in interval_keys:
    data = intervals[key]
    total = data['home'] + data['away']
    if total > 0:
        home_pct = (data['home'] / total) * 100
        away_pct = (data['away'] / total) * 100
    else:
        home_pct = away_pct = 0

    # Check balance
    if 30 <= home_pct <= 70 and 30 <= away_pct <= 70:
        balance = "✓ Balanced"
    else:
        balance = "✗ Imbalanced"

    print(f"{key:<12} {home_pct:>6.1f}%   {away_pct:>6.1f}%   {data['changes']:>7}    {balance}")

# Overall stats
stats = results.get('statistics', {})
print(f"\nOverall (30 minutes):")
print(f"  Home: {stats['home']['possession_percent']:.1f}%")
print(f"  Away: {stats['away']['possession_percent']:.1f}%")
print(f"  Total changes: {len(possession_events)}")

print("\n" + "=" * 70)
print("PATTERN ANALYSIS")
print("=" * 70)

# Check if imbalance grows over time
home_pcts = []
for key in interval_keys:
    data = intervals[key]
    total = data['home'] + data['away']
    if total > 0:
        home_pcts.append((data['home'] / total) * 100)
    else:
        home_pcts.append(0)

# Calculate trend
if len(home_pcts) >= 3:
    early_avg = np.mean(home_pcts[:2])  # First 10 min
    late_avg = np.mean(home_pcts[-2:])  # Last 10 min

    print(f"\nEarly game (0-10 min): Home {early_avg:.1f}%")
    print(f"Late game (20-30 min): Home {late_avg:.1f}%")
    print(f"Shift: {late_avg - early_avg:+.1f}%")

    if abs(late_avg - early_avg) > 20:
        print("\n✗ SIGNIFICANT DRIFT DETECTED!")
        print("  → Possession balance deteriorates over time")
        print("  → Positive feedback loop confirmed")

        if late_avg > early_avg:
            print("  → Home team accumulates advantage")
        else:
            print("  → Away team accumulates advantage")
    else:
        print("\n✓ Possession remains relatively stable")

print("\n" + "=" * 70)
