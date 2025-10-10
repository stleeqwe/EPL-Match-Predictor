#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Phase 1: Dynamic Balance System
Target: 75% of matches with balanced possession (30-70%)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'backend'))

import numpy as np
from simulation.game_simulator import GameSimulator, SimulationConfig


def create_test_team(team_name, x_side):
    """Create a test team with moderate ratings"""
    players = []

    # GK
    players.append({
        'id': f'{team_name}_GK',
        'position': [x_side * 45, 0],
        'role': 'GK',
        'attributes': {
            'pace': 60, 'shooting': 40, 'passing': 60,
            'dribbling': 50, 'defending': 70, 'physical': 70,
            'reflexes': 80
        }
    })

    # Defenders (4)
    for i in range(4):
        y_pos = -20 + i * 13
        players.append({
            'id': f'{team_name}_DEF{i}',
            'position': [x_side * 30, y_pos],
            'role': 'CB',
            'attributes': {
                'pace': 65, 'shooting': 40, 'passing': 65,
                'dribbling': 55, 'defending': 75, 'physical': 75
            }
        })

    # Midfielders (4)
    for i in range(4):
        y_pos = -20 + i * 13
        players.append({
            'id': f'{team_name}_MID{i}',
            'position': [x_side * 10, y_pos],
            'role': 'CM',
            'attributes': {
                'pace': 70, 'shooting': 65, 'passing': 75,
                'dribbling': 70, 'defending': 65, 'physical': 65
            }
        })

    # Forwards (2)
    for i in range(2):
        y_pos = -8 + i * 16
        players.append({
            'id': f'{team_name}_FWD{i}',
            'position': [x_side * -15, y_pos],
            'role': 'ST',
            'attributes': {
                'pace': 80, 'shooting': 78, 'passing': 70,
                'dribbling': 75, 'defending': 40, 'physical': 65
            }
        })

    return players


def run_test_match(match_num):
    """Run a single test match"""
    print(f"\n{'='*70}")
    print(f"Match {match_num}")
    print(f"{'='*70}")

    # Create teams (equal strength)
    home_players = create_test_team('HOME', 1)
    away_players = create_test_team('AWAY', -1)

    # Configure for quick test (5 minutes = 300 seconds)
    config = SimulationConfig(
        duration_seconds=300.0,  # 5 minutes
        dt=0.1,
        enable_agents=True,
        enable_position_behaviors=True,
        collect_statistics=True,
        verbose=False
    )

    # Run simulation
    simulator = GameSimulator(config)
    results = simulator.simulate_match(home_players, away_players, 'Home', 'Away')

    # Extract possession from global context
    context_summary = simulator.global_context.get_summary()

    possession = {
        'home': context_summary['possession_home'],
        'away': context_summary['possession_away']
    }

    # Check if balanced (30-70% range)
    is_balanced = (30 <= possession['home'] <= 70 and 30 <= possession['away'] <= 70)

    print(f"\n📊 POSSESSION RESULTS:")
    print(f"  Home: {possession['home']:.1f}%")
    print(f"  Away: {possession['away']:.1f}%")
    print(f"  Balanced: {'✅ YES' if is_balanced else '❌ NO'}")
    print(f"  Balance metric: {context_summary['possession_balance']:.3f}")
    print(f"  Dominant team: {context_summary['dominant_team']}")
    print(f"  Possession changes: {context_summary['possession_changes']}")
    print(f"  Time in balance: {context_summary['time_in_balance']:.1f}s")

    return {
        'home_poss': possession['home'],
        'away_poss': possession['away'],
        'is_balanced': is_balanced,
        'balance_metric': context_summary['possession_balance'],
        'dominant_team': context_summary['dominant_team'],
        'possession_changes': context_summary['possession_changes'],
        'score': results['score'],
        'simulation_speed': results['performance']['simulation_speed']
    }


def main():
    """Run Phase 1 balance tests"""
    print("\n" + "="*70)
    print("PHASE 1 BALANCE TEST - Dynamic Balancer + Global Context")
    print("="*70)
    print("\nTarget: 75% of matches with balanced possession (30-70%)")
    print("Baseline (V11): 60% balanced")
    print("\nRunning 10 test matches (5 minutes each)...\n")

    results = []
    for i in range(1, 11):
        result = run_test_match(i)
        results.append(result)

    # Calculate statistics
    balanced_count = sum(1 for r in results if r['is_balanced'])
    balanced_pct = (balanced_count / len(results)) * 100

    avg_home_poss = np.mean([r['home_poss'] for r in results])
    avg_away_poss = np.mean([r['away_poss'] for r in results])

    std_dev = np.std([r['home_poss'] for r in results])

    avg_balance_metric = np.mean([abs(r['balance_metric']) for r in results])
    avg_poss_changes = np.mean([r['possession_changes'] for r in results])
    avg_sim_speed = np.mean([r['simulation_speed'] for r in results])

    # Print summary
    print("\n" + "="*70)
    print("PHASE 1 TEST RESULTS")
    print("="*70)

    print(f"\n📊 Balance Performance:")
    print(f"  Balanced matches: {balanced_count}/10 ({balanced_pct:.0f}%)")
    print(f"  Target: 75%")
    print(f"  Status: {'✅ PASSED' if balanced_pct >= 75 else '⚠️  CLOSE' if balanced_pct >= 65 else '❌ NEEDS WORK'}")

    print(f"\n📈 Possession Statistics:")
    print(f"  Average Home: {avg_home_poss:.1f}%")
    print(f"  Average Away: {avg_away_poss:.1f}%")
    print(f"  Standard deviation: σ = {std_dev:.1f}%")
    print(f"  Average balance metric: {avg_balance_metric:.3f}")
    print(f"  Average possession changes: {avg_poss_changes:.0f}")

    print(f"\n⚡ Performance:")
    print(f"  Average simulation speed: {avg_sim_speed:.1f}x real-time")
    print(f"  Target: >50x real-time")
    print(f"  Status: {'✅ PASSED' if avg_sim_speed >= 50 else '❌ TOO SLOW'}")

    print(f"\n📋 Individual Match Results:")
    print(f"  {'Match':<8} {'Home%':<8} {'Away%':<8} {'Balanced':<10} {'Score'}")
    print(f"  {'-'*60}")
    for i, r in enumerate(results, 1):
        balanced_str = '✅' if r['is_balanced'] else '❌'
        score_str = f"{r['score']['home']}-{r['score']['away']}"
        print(f"  {i:<8} {r['home_poss']:<8.1f} {r['away_poss']:<8.1f} {balanced_str:<10} {score_str}")

    # Final verdict
    print("\n" + "="*70)
    print("PHASE 1 VERDICT")
    print("="*70)

    if balanced_pct >= 75:
        print("✅ SUCCESS - Phase 1 target achieved!")
        print(f"   Balanced matches: {balanced_pct:.0f}% (target: 75%)")
        print("   Ready to proceed to Phase 2")
    elif balanced_pct >= 65:
        print("⚠️  CLOSE - Near target but needs minor tuning")
        print(f"   Balanced matches: {balanced_pct:.0f}% (target: 75%)")
        print("   Consider slight parameter adjustments")
    else:
        print("❌ NEEDS WORK - Below target")
        print(f"   Balanced matches: {balanced_pct:.0f}% (target: 75%)")
        print("   Phase 1 components may need debugging or tuning")

    print("\n" + "="*70 + "\n")


if __name__ == '__main__':
    main()
