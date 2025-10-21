#!/usr/bin/env python3
"""
Pipeline V3 Full E2E Test (3000 runs per scenario)

프로덕션 환경과 동일한 설정으로 전체 테스트:
- Phase 1: Ensemble
- Phase 2: AI Scenarios (2-5 dynamic)
- Phase 3: Validation (3000 runs per scenario)
- Phase 4: Final Report

Expected execution time: 5-10 minutes
"""

import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

import logging
import time

# Set logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

from services.enriched_data_loader import EnrichedDomainDataLoader
from simulation.v3.pipeline.simulation_pipeline_v3 import SimulationPipelineV3, PipelineConfig

print("\n" + "="*80)
print("PIPELINE V3 FULL E2E TEST")
print("="*80)
print("\nThis is a FULL production-level test:")
print("- Mathematical Models: Poisson-Rating, Zone Dominance, Key Player")
print("- AI Scenarios: 2-5 scenarios (NO Templates)")
print("- Validation: 3000 runs per scenario")
print("- Expected time: 5-10 minutes")
print("\nPress Ctrl+C to cancel, or wait 5 seconds to start...")
print()

time.sleep(5)

# Load data
print("\n" + "="*80)
print("Loading team data...")
print("="*80)

loader = EnrichedDomainDataLoader()
arsenal = loader.load_team_data("Arsenal")
liverpool = loader.load_team_data("Liverpool")

print(f"\n✓ Loaded {arsenal.name}: Attack {arsenal.derived_strengths.attack_strength:.1f}, Defense {arsenal.derived_strengths.defense_strength:.1f}")
print(f"✓ Loaded {liverpool.name}: Attack {liverpool.derived_strengths.attack_strength:.1f}, Defense {liverpool.derived_strengths.defense_strength:.1f}")

# Configure pipeline (3000 runs - PRODUCTION SETTING)
config = PipelineConfig(
    validation_runs=3000,  # Full production runs
    log_level="INFO"
)

# Create pipeline
pipeline = SimulationPipelineV3(config=config)

print("\n" + "="*80)
print("STARTING FULL E2E TEST")
print("="*80)
print(f"\nMatch: {arsenal.name} vs {liverpool.name}")
print(f"Validation runs per scenario: {config.validation_runs}")
print()

# Run pipeline
start_time = time.time()

try:
    result = pipeline.run(arsenal, liverpool)

    elapsed = time.time() - start_time

    print("\n" + "="*80)
    print("E2E TEST RESULTS")
    print("="*80)

    print(f"\nExecution time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")

    print(f"\n[Phase 1] Ensemble Probabilities:")
    print(f"  Home: {result.ensemble_result.ensemble_probabilities['home_win']:.1%}")
    print(f"  Draw: {result.ensemble_result.ensemble_probabilities['draw']:.1%}")
    print(f"  Away: {result.ensemble_result.ensemble_probabilities['away_win']:.1%}")

    print(f"\n[Phase 2] AI Generated Scenarios: {result.generated_scenarios.scenario_count}")
    for scenario in result.generated_scenarios.scenarios:
        print(f"  - {scenario.id}: {scenario.name}")
        print(f"    Expected probability: {scenario.expected_probability:.1%}, Events: {len(scenario.events)}")

    print(f"\n[Phase 3] Validation Results:")
    print(f"  Total scenarios: {result.validation_result.total_scenarios}")
    print(f"  Total runs: {result.validation_result.total_runs}")

    for sc_result in result.validation_result.scenario_results:
        print(f"\n  {sc_result.scenario_id}:")
        print(f"    Expected prob: {sc_result.initial_probability:.1%}")
        print(f"    Converged: Home {sc_result.convergence_probability['home_win']:.1%}, "
              f"Draw {sc_result.convergence_probability['draw']:.1%}, "
              f"Away {sc_result.convergence_probability['away_win']:.1%}")
        print(f"    Avg score: {sc_result.avg_score['home']:.2f}-{sc_result.avg_score['away']:.2f}")
        print(f"    Outcomes: Home {sc_result.outcome_distribution.get('home_win', 0)}, "
              f"Draw {sc_result.outcome_distribution.get('draw', 0)}, "
              f"Away {sc_result.outcome_distribution.get('away_win', 0)}")

    print(f"\n[Final] Converged Probabilities:")
    print(f"  Home win: {result.final_probabilities['home_win']:.1%}")
    print(f"  Draw:     {result.final_probabilities['draw']:.1%}")
    print(f"  Away win: {result.final_probabilities['away_win']:.1%}")

    # Performance metrics
    print(f"\n[Performance Metrics]")
    print(f"  Total simulations: {result.validation_result.total_runs}")
    print(f"  Average time per simulation: {elapsed / result.validation_result.total_runs * 1000:.1f}ms")
    print(f"  Simulations per second: {result.validation_result.total_runs / elapsed:.1f}")

    print("\n" + "="*80)
    print("✓ PIPELINE V3 FULL E2E TEST PASSED")
    print("="*80)
    print()

except KeyboardInterrupt:
    print("\n\n✗ Test cancelled by user")
except Exception as e:
    print(f"\n✗ Pipeline failed: {e}")
    import traceback
    traceback.print_exc()
