#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Full 90-Minute Match Simulation
Tests complete match with V6 coordination fixes
"""

import sys
import time
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'backend'))

from simulation.game_simulator import GameSimulator, SimulationConfig

# =============================================================================
# TEST FORMATION
# =============================================================================

def create_test_player_dict(player_id='p1', position=(0, 0), role='CM'):
    """Create test player dictionary"""
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
    """Create test 11-player formation (4-3-3)"""
    players = []

    # GK
    players.append(create_test_player_dict(
        f'{team_prefix}_gk',
        (x_offset - 40, 0),
        'GK'
    ))

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


# =============================================================================
# FULL MATCH SIMULATION
# =============================================================================

def run_full_match():
    """Run complete 90-minute match"""
    print("=" * 70)
    print("FULL 90-MINUTE MATCH SIMULATION")
    print("Testing V6 Player Coordination Fixes")
    print("=" * 70)

    # Create full teams
    print("\nCreating teams...")
    home_players = create_test_formation('h', x_offset=0)
    away_players = create_test_formation('a', x_offset=0)

    # Mirror away team
    for player in away_players:
        player['position'] = (-player['position'][0], player['position'][1])

    print(f"  Home: 11 players (4-3-3 formation)")
    print(f"  Away: 11 players (4-3-3 formation)")

    # Configure 90-minute simulation
    config = SimulationConfig(
        duration_seconds=5400.0,  # 90 minutes
        dt=0.1,
        enable_agents=True,
        enable_position_behaviors=True,
        collect_statistics=True,
        verbose=True  # Show goals
    )

    print(f"\nConfiguration:")
    print(f"  Duration: {config.duration_seconds/60:.0f} minutes")
    print(f"  Time step: {config.dt}s")
    print(f"  Total ticks: {int(config.duration_seconds / config.dt):,}")

    # Run simulation
    print("\nStarting simulation...")
    simulator = GameSimulator(config)

    wall_start = time.time()
    results = simulator.simulate_match(
        home_players, away_players,
        'Home Team', 'Away Team'
    )
    wall_elapsed = time.time() - wall_start

    # Extract results
    score = results['score']
    stats = results.get('statistics', {})
    validation = results.get('validation', {})
    performance = results['performance']
    events = results['events']

    # Print detailed results
    print("\n" + "=" * 70)
    print("MATCH RESULTS")
    print("=" * 70)

    print(f"\n📊 Final Score: {score['home']} - {score['away']}")
    print(f"⏱️  Match Duration: {results['duration']/60:.1f} minutes")
    print(f"🚀 Simulation Speed: {performance['simulation_speed']:.1f}x real-time")
    print(f"⏰ Wall Clock Time: {wall_elapsed:.1f}s ({wall_elapsed/60:.1f} min)")

    # Performance metrics
    print(f"\n🔧 Performance Metrics:")
    print(f"  Total ticks: {performance['ticks']:,}")
    print(f"  Avg tick time: {performance['avg_tick_time']:.3f}ms")
    print(f"  90min simulation time: {wall_elapsed:.1f}s")

    # Statistics
    if stats:
        print(f"\n📈 Match Statistics:")
        print(f"\n  Home Team:")
        print(f"    Shots: {stats['home']['shots']}")
        print(f"    Goals: {score['home']}")
        print(f"    Possession: {stats['home']['possession_percent']:.1f}%")

        print(f"\n  Away Team:")
        print(f"    Shots: {stats['away']['shots']}")
        print(f"    Goals: {score['away']}")
        print(f"    Possession: {stats['away']['possession_percent']:.1f}%")

        print(f"\n  Total:")
        total_possession = stats['home']['possession_percent'] + stats['away']['possession_percent']
        print(f"    Total shots: {stats['home']['shots'] + stats['away']['shots']}")
        print(f"    Total possession: {total_possession:.1f}%")
        print(f"    Total events: {len(events)}")

    # Event breakdown
    print(f"\n🎯 Event Breakdown:")
    event_types = {}
    for event in events:
        event_type = event['event_type']
        event_types[event_type] = event_types.get(event_type, 0) + 1

    for event_type, count in sorted(event_types.items(), key=lambda x: -x[1]):
        print(f"  {event_type}: {count}")

    # Realism validation
    if validation:
        print(f"\n✅ EPL Realism Validation:")

        # Define EPL targets
        epl_targets = {
            'total_shots': (10, 50, 'Total shots in range'),
            'goals': (0, 8, 'Total goals realistic'),
            'possession': (80, 105, 'Possession totals near 100%')
        }

        total_shots = stats['home']['shots'] + stats['away']['shots']
        total_goals = score['home'] + score['away']
        total_possession = stats['home']['possession_percent'] + stats['away']['possession_percent']

        results_check = {
            'total_shots': total_shots,
            'goals': total_goals,
            'possession': total_possession
        }

        all_pass = True
        for key, (min_val, max_val, desc) in epl_targets.items():
            value = results_check[key]
            passed = min_val <= value <= max_val
            status = '✓' if passed else '✗'
            print(f"  {status} {desc}: {value:.1f} (target: {min_val}-{max_val})")
            if not passed:
                all_pass = False

        print(f"\n  Overall: {'✓ REALISTIC' if all_pass else '⚠️  NEEDS TUNING'}")

    # Success/failure assessment
    print("\n" + "=" * 70)
    print("ASSESSMENT")
    print("=" * 70)

    # Check for critical issues
    issues = []
    warnings = []

    # 1. Ball should stay active (possession near 100%)
    if total_possession < 80:
        issues.append(f"Low possession total ({total_possession:.1f}%) - ball may be stuck")
    elif total_possession < 90:
        warnings.append(f"Possession total slightly low ({total_possession:.1f}%)")

    # 2. Performance should be good (>1x real-time)
    if performance['simulation_speed'] < 1.0:
        issues.append(f"Simulation slower than real-time ({performance['simulation_speed']:.1f}x)")
    elif performance['simulation_speed'] < 10.0:
        warnings.append(f"Simulation speed moderate ({performance['simulation_speed']:.1f}x)")

    # 3. Should have reasonable events
    if len(events) < 50:
        issues.append(f"Very few events ({len(events)}) - system may be stuck")

    # 4. Shot balance
    if total_shots > 1000:
        warnings.append(f"Very high shot count ({total_shots}) - may need tuning")
    elif total_shots < 5:
        warnings.append(f"Very low shot count ({total_shots}) - may need tuning")

    # Print assessment
    if issues:
        print("\n❌ CRITICAL ISSUES FOUND:")
        for issue in issues:
            print(f"  - {issue}")

    if warnings:
        print("\n⚠️  WARNINGS (tuning needed):")
        for warning in warnings:
            print(f"  - {warning}")

    if not issues and not warnings:
        print("\n✅ ALL SYSTEMS WORKING CORRECTLY!")
        print("  No critical issues detected")
        print("  Statistics within acceptable ranges")

    if not issues:
        if warnings:
            print("\n✓ SIMULATION SUCCESSFUL (with tuning recommendations)")
        else:
            print("\n✓ SIMULATION SUCCESSFUL")
        return True
    else:
        print("\n✗ SIMULATION FAILED (critical issues detected)")
        return False


if __name__ == "__main__":
    print("\n")
    success = run_full_match()
    print("\n")
    sys.exit(0 if success else 1)
