#!/usr/bin/env python3
"""
Real AI Scenario Generation Test
"""

import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from services.enriched_data_loader import EnrichedDomainDataLoader
from simulation.v3.models.model_ensemble import ModelEnsemble
from simulation.v3.scenario.math_based_generator import MathBasedScenarioGenerator

# Load data
loader = EnrichedDomainDataLoader()
arsenal = loader.load_team_data('Arsenal')
liverpool = loader.load_team_data('Liverpool')

# Run ensemble
print('\n' + '='*80)
print('Running Ensemble...')
print('='*80)

ensemble = ModelEnsemble()
ensemble_result = ensemble.calculate(arsenal, liverpool)

print(f'\nEnsemble: Home {ensemble_result.ensemble_probabilities["home_win"]:.1%}, '
      f'Draw {ensemble_result.ensemble_probabilities["draw"]:.1%}, '
      f'Away {ensemble_result.ensemble_probabilities["away_win"]:.1%}')

# Generate scenarios (REAL AI CALL)
print('\n' + '='*80)
print('Calling Gemini AI to generate scenarios...')
print('='*80)

generator = MathBasedScenarioGenerator()
try:
    result = generator.generate(arsenal, liverpool, ensemble_result)

    print(f'\n✓ AI Response received!')
    print(f'\nReasoning: {result.reasoning}')
    print(f'\nScenario count: {result.scenario_count}')
    print(f'\nScenarios:')
    for i, scenario in enumerate(result.scenarios, 1):
        print(f'\n  {i}. {scenario.id}: {scenario.name}')
        print(f'     Probability: {scenario.expected_probability:.1%}')
        print(f'     Reasoning: {scenario.reasoning[:100]}...')
        print(f'     Events: {len(scenario.events)}')

        # Show first 2 events
        for j, event in enumerate(scenario.events[:2], 1):
            print(f'       Event {j}: {event.type.value} by {event.actor} ({event.minute_range[0]}-{event.minute_range[1]} min)')

    print('\n' + '='*80)
    print('✓ AI Scenario Generation Test PASSED')
    print('='*80)
    print()

except Exception as e:
    print(f'\n✗ AI call failed: {e}')
    import traceback
    traceback.print_exc()
