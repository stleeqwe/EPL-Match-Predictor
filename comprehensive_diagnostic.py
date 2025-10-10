#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Diagnostic
Test all hypotheses simultaneously
"""

import sys
import numpy as np
from pathlib import Path
from collections import Counter, defaultdict

sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from simulation.game_simulator import GameSimulator, SimulationConfig
from agents.actions import ActionType

# Track all decisions and outcomes
all_actions = defaultdict(lambda: Counter())
tackle_attempts = {'home': 0, 'away': 0}
tackle_successes = {'home': 0, 'away': 0}
possession_holder_timeline = []  # [(time, team)]
pass_attempts = {'home': 0, 'away': 0}
pass_completions = {'home': 0, 'away': 0}

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

# Monkey-patch to track actions
from agents.simple_agent import SimpleAgent
original_decide = SimpleAgent.decide_action

def tracked_decide(self, player_state, game_context):
    action = original_decide(self, player_state, game_context)

    team = player_state.team_id
    action_name = action.action_type.name if hasattr(action.action_type, 'name') else str(action.action_type)
    all_actions[team][action_name] += 1

    if action_name == 'TACKLE':
        tackle_attempts[team] += 1

    return action

SimpleAgent.decide_action = tracked_decide

# Monkey-patch to track tackle outcomes
from simulation.action_executor import ActionExecutor
original_execute_tackle = ActionExecutor._execute_tackle

def tracked_tackle(self, action, player_state, player_attributes, ball_state):
    result = original_execute_tackle(self, action, player_state, player_attributes, ball_state)

    # Check if tackle succeeded (ball kicked)
    if result[1] and result[1].ball_kicked:
        # Infer team from player position (rough heuristic)
        team = 'home' if player_state.position[0] > 0 else 'away'
        tackle_successes[team] += 1

    return result

ActionExecutor._execute_tackle = tracked_tackle

# Track pass outcomes
original_execute_pass = ActionExecutor._execute_pass

def tracked_pass(self, action, player_state, player_attributes, ball_state):
    result = original_execute_pass(self, action, player_state, player_attributes, ball_state)

    team = 'home' if player_state.position[0] > 0 else 'away'
    pass_attempts[team] += 1

    # If pass executed, assume success (simplified)
    if result[1] and result[1].ball_kicked:
        pass_completions[team] += 1

    return result

ActionExecutor._execute_pass = tracked_pass

print("=" * 70)
print("COMPREHENSIVE DIAGNOSTIC")
print("Testing all hypotheses simultaneously")
print("=" * 70)

print("\nHYPOTHESIS 1: Directional Bias")
print("Testing if Home vs Away position creates systematic advantage")

# Test 1: Normal configuration
print("\n  Test 1A: Home at positive X, Away at negative X")
home_players = create_test_formation('h', x_offset=0)
away_players = create_test_formation('a', x_offset=0)
for player in away_players:
    player['position'] = (-player['position'][0], player['position'][1])

config = SimulationConfig(duration_seconds=300.0, dt=0.1, enable_agents=True,
                          enable_position_behaviors=True, collect_statistics=True, verbose=False)

simulator = GameSimulator(config)
result1 = simulator.simulate_match(home_players, away_players, 'Home', 'Away')
stats1 = result1.get('statistics', {})

print(f"    Home (x>0): {stats1['home']['possession_percent']:.1f}%")
print(f"    Away (x<0): {stats1['away']['possession_percent']:.1f}%")

# Test 2: Swapped configuration (swap TEAM LABELS, not positions)
print("\n  Test 1B: SWAPPED - Home at negative X, Away at positive X")
home_players2 = create_test_formation('h', x_offset=0)
away_players2 = create_test_formation('a', x_offset=0)
# Mirror away team to negative x (same as Test 1A)
for player in away_players2:
    player['position'] = (-player['position'][0], player['position'][1])

# V9 FIX: Swap team labels so Home is now at negative x, Away at positive x
# This properly tests if x-position creates bias
simulator2 = GameSimulator(config)
result2 = simulator2.simulate_match(away_players2, home_players2, 'HomeSwap', 'AwaySwap')
stats2 = result2.get('statistics', {})

print(f"    Home (x<0): {stats2['home']['possession_percent']:.1f}%")
print(f"    Away (x>0): {stats2['away']['possession_percent']:.1f}%")

# Analysis
print("\n  Analysis:")
if abs(stats1['home']['possession_percent'] - stats2['away']['possession_percent']) < 10:
    print("    ✓ No directional bias detected")
    print("    → Position (x>0 vs x<0) doesn't create systematic advantage")
else:
    print("    ✗ DIRECTIONAL BIAS DETECTED!")
    print(f"    → x>0 position: {(stats1['home']['possession_percent'] + stats2['away']['possession_percent'])/2:.1f}% avg")
    print(f"    → x<0 position: {(stats1['away']['possession_percent'] + stats2['home']['possession_percent'])/2:.1f}% avg")

print("\n" + "=" * 70)
print("HYPOTHESIS 2: Decision Cooldown Impact")
print("Checking how often actions are being chosen")

print(f"\n  Action frequency (from Test 1A):")
for team in ['home', 'away']:
    print(f"\n  {team.upper()}:")
    total = sum(all_actions[team].values())
    for action, count in all_actions[team].most_common(5):
        pct = count / total * 100 if total > 0 else 0
        print(f"    {action:15s}: {count:5d} ({pct:5.1f}%)")

print("\n" + "=" * 70)
print("HYPOTHESIS 3: Tackle Effectiveness")

print(f"\n  Tackle attempts:")
print(f"    Home: {tackle_attempts['home']}")
print(f"    Away: {tackle_attempts['away']}")

print(f"\n  Tackle successes:")
print(f"    Home: {tackle_successes['home']}")
print(f"    Away: {tackle_successes['away']}")

for team in ['home', 'away']:
    if tackle_attempts[team] > 0:
        success_rate = tackle_successes[team] / tackle_attempts[team] * 100
        print(f"\n  {team.upper()} tackle success rate: {success_rate:.1f}%")
    else:
        print(f"\n  {team.upper()}: No tackles attempted")

print("\n" + "=" * 70)
print("HYPOTHESIS 4: Pass Completion Rate")

for team in ['home', 'away']:
    if pass_attempts[team] > 0:
        completion = pass_completions[team] / pass_attempts[team] * 100
        print(f"\n  {team.upper()}:")
        print(f"    Attempts: {pass_attempts[team]}")
        print(f"    Completions: {pass_completions[team]}")
        print(f"    Success rate: {completion:.1f}%")

        if completion > 95:
            print(f"    ⚠️  TOO HIGH! (Target: 65-92%)")
        elif completion < 65:
            print(f"    ⚠️  TOO LOW! (Target: 65-92%)")
        else:
            print(f"    ✓ Within EPL range")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

print("\nIssues found:")
issues = []

# Check directional bias
if abs(stats1['home']['possession_percent'] - stats2['away']['possession_percent']) >= 10:
    issues.append("✗ Directional bias (x-position matters)")

# Check tackle frequency
total_tackles = tackle_attempts['home'] + tackle_attempts['away']
if total_tackles < 10:
    issues.append("✗ Tackles too infrequent (<10 per 5 min)")

# Check pass completion
for team in ['home', 'away']:
    if pass_attempts[team] > 0:
        completion = pass_completions[team] / pass_attempts[team] * 100
        if completion > 95:
            issues.append(f"✗ {team.upper()} pass completion too high ({completion:.0f}%)")

if not issues:
    print("  ✓ No major issues detected in this test")
else:
    for issue in issues:
        print(f"  {issue}")

print("\n" + "=" * 70)
