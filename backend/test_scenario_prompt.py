#!/usr/bin/env python3
"""
AI Scenario Generator Prompt 테스트

실제 AI 호출 없이 prompt만 출력
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
arsenal = loader.load_team_data("Arsenal")
liverpool = loader.load_team_data("Liverpool")

# Run ensemble
print("\n" + "="*80)
print("Running Ensemble...")
print("="*80)

ensemble = ModelEnsemble()
ensemble_result = ensemble.calculate(arsenal, liverpool)

print(f"\nEnsemble Probabilities:")
print(f"  Home: {ensemble_result.ensemble_probabilities['home_win']:.1%}")
print(f"  Draw: {ensemble_result.ensemble_probabilities['draw']:.1%}")
print(f"  Away: {ensemble_result.ensemble_probabilities['away_win']:.1%}")

# Generate prompt (without AI call)
print("\n" + "="*80)
print("Generating AI Prompt...")
print("="*80)

generator = MathBasedScenarioGenerator()

# Build prompts
system_prompt = generator._build_system_prompt()
user_prompt = generator._build_user_prompt(arsenal, liverpool, ensemble_result)

print("\n" + "="*80)
print("SYSTEM PROMPT")
print("="*80)
print(system_prompt)

print("\n" + "="*80)
print("USER PROMPT")
print("="*80)
print(user_prompt)

print("\n" + "="*80)
print("Prompt Stats")
print("="*80)
print(f"System prompt: {len(system_prompt)} chars")
print(f"User prompt: {len(user_prompt)} chars")
print(f"Total: {len(system_prompt) + len(user_prompt)} chars")
print()
