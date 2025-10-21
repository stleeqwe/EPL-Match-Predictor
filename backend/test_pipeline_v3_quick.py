#!/usr/bin/env python3
"""
Pipeline V3 Quick Test (100 runs)

빠른 통합 테스트:
- Phase 1: Ensemble
- Phase 2: AI Scenarios
- Phase 3: Validation (100 runs)
"""

import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

import logging

# Set logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

from services.enriched_data_loader import EnrichedDomainDataLoader
from simulation.v3.pipeline.simulation_pipeline_v3 import SimulationPipelineV3, PipelineConfig

# Load data
print("\n" + "="*80)
print("Loading team data...")
print("="*80)

loader = EnrichedDomainDataLoader()
arsenal = loader.load_team_data("Arsenal")
liverpool = loader.load_team_data("Liverpool")

print(f"\n✓ Loaded {arsenal.name}: Attack {arsenal.derived_strengths.attack_strength:.1f}, Defense {arsenal.derived_strengths.defense_strength:.1f}")
print(f"✓ Loaded {liverpool.name}: Attack {liverpool.derived_strengths.attack_strength:.1f}, Defense {liverpool.derived_strengths.defense_strength:.1f}")

# Configure pipeline (100 runs for quick test)
config = PipelineConfig(
    validation_runs=100,  # Quick test
    log_level="INFO"
)

# Create pipeline
pipeline = SimulationPipelineV3(config=config)

print("\n" + "="*80)
print("PIPELINE V3 QUICK TEST (100 runs)")
print("="*80)
print(f"\nMatch: {arsenal.name} vs {liverpool.name}")
print(f"Validation runs per scenario: {config.validation_runs}")
print()

# Run pipeline
try:
    result = pipeline.run(arsenal, liverpool)

    print("\n" + "="*80)
    print("TEST RESULTS")
    print("="*80)

    print(f"\nExecution time: {result.execution_time:.1f}s")

    print(f"\n[Phase 1] Ensemble Probabilities:")
    print(f"  Home: {result.ensemble_result.ensemble_probabilities['home_win']:.1%}")
    print(f"  Draw: {result.ensemble_result.ensemble_probabilities['draw']:.1%}")
    print(f"  Away: {result.ensemble_result.ensemble_probabilities['away_win']:.1%}")

    print(f"\n[Phase 2] AI Generated Scenarios: {result.generated_scenarios.scenario_count}")
    for scenario in result.generated_scenarios.scenarios:
        print(f"  - {scenario.id}: {scenario.name}")
        print(f"    Probability: {scenario.expected_probability:.1%}, Events: {len(scenario.events)}")

    print(f"\n[Phase 3] Validation Results:")
    print(f"  Total runs: {result.validation_result.total_runs}")
    for sc_result in result.validation_result.scenario_results:
        print(f"\n  {sc_result.scenario_id}:")
        print(f"    Initial prob: {sc_result.initial_probability:.1%}")
        print(f"    Convergence: Home {sc_result.convergence_probability['home_win']:.1%}, "
              f"Draw {sc_result.convergence_probability['draw']:.1%}, "
              f"Away {sc_result.convergence_probability['away_win']:.1%}")
        print(f"    Avg score: {sc_result.avg_score['home']:.2f}-{sc_result.avg_score['away']:.2f}")

    print(f"\n[Final] Converged Probabilities:")
    print(f"  Home win: {result.final_probabilities['home_win']:.1%}")
    print(f"  Draw:     {result.final_probabilities['draw']:.1%}")
    print(f"  Away win: {result.final_probabilities['away_win']:.1%}")

    print("\n" + "="*80)
    print("✓ PIPELINE V3 QUICK TEST PASSED")
    print("="*80)
    print()

except Exception as e:
    print(f"\n✗ Pipeline failed: {e}")
    import traceback
    traceback.print_exc()
