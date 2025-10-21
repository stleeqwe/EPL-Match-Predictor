#!/usr/bin/env python3
"""
Inspect AI Scenario Generation Process
실제 시나리오 생성 과정을 상세히 보여주는 스크립트
"""

import os
import sys
import logging
import json
from dotenv import load_dotenv

# Load environment
load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from services.enriched_data_loader import EnrichedDomainDataLoader
from simulation.v2.ai_scenario_generator_enriched import EnrichedAIScenarioGenerator

# Setup detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    print("\n" + "="*80)
    print("AI SCENARIO GENERATION PROCESS INSPECTION")
    print("="*80)

    # Step 1: Load team data
    print("\n[STEP 1] Loading Team Data...")
    loader = EnrichedDomainDataLoader()
    arsenal = loader.load_team_data("Arsenal")
    liverpool = loader.load_team_data("Liverpool")
    print(f"✓ Arsenal loaded: {len(arsenal.lineup)} players")
    print(f"✓ Liverpool loaded: {len(liverpool.lineup)} players")

    # Step 2: Create generator
    print("\n[STEP 2] Initializing AI Scenario Generator...")
    generator = EnrichedAIScenarioGenerator()
    print(f"✓ Generator initialized with {generator.ai_client.get_model_info()['provider']}")

    # Step 3: Build prompts (inspect)
    print("\n[STEP 3] Building AI Prompts...")
    system_prompt = generator._build_enriched_system_prompt_for_scenarios()
    user_prompt = generator._build_enriched_scenario_generation_prompt(
        home_team=arsenal,
        away_team=liverpool,
        match_context={
            'venue': 'Emirates Stadium',
            'competition': 'Premier League',
            'importance': 'top_clash'
        }
    )

    print("\n" + "-"*80)
    print("SYSTEM PROMPT (First 1000 chars):")
    print("-"*80)
    print(system_prompt[:1000])
    print("...\n")

    print("-"*80)
    print("USER PROMPT (First 2000 chars):")
    print("-"*80)
    print(user_prompt[:2000])
    print("...\n")

    # Step 4: Generate scenarios
    print("\n[STEP 4] Generating Scenarios with AI...")
    print("This may take 10-30 seconds...")

    success, scenarios, error = generator.generate_scenarios_enriched(
        home_team=arsenal,
        away_team=liverpool,
        match_context={
            'venue': 'Emirates Stadium',
            'competition': 'Premier League',
            'importance': 'top_clash'
        }
    )

    if not success:
        print(f"\n❌ Generation failed: {error}")
        return

    print(f"\n✓ Successfully generated {len(scenarios)} scenarios")

    # Step 5: Display scenarios
    print("\n" + "="*80)
    print("GENERATED SCENARIOS")
    print("="*80)

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{'='*80}")
        print(f"SCENARIO {i}: {scenario.name}")
        print(f"{'='*80}")
        print(f"ID: {scenario.id}")
        print(f"Expected Probability: {scenario.expected_probability:.1%}")
        print(f"\nReasoning:")
        print(f"  {scenario.reasoning}")

        print(f"\nEvents ({len(scenario.events)}):")
        for j, event in enumerate(scenario.events, 1):
            print(f"  {j}. [{event.minute_range[0]}-{event.minute_range[1]}min] "
                  f"{event.type.value} ({event.team})")
            print(f"     Actor: {event.actor or 'N/A'}")
            print(f"     Boost: {event.probability_boost}x")
            print(f"     Reason: {event.reason}")

        if scenario.parameter_adjustments:
            print(f"\nParameter Adjustments:")
            for param, value in scenario.parameter_adjustments.items():
                print(f"  - {param}: {value}")

    # Step 6: Summary statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)

    total_prob = sum(s.expected_probability for s in scenarios)
    total_events = sum(len(s.events) for s in scenarios)

    print(f"Total Scenarios: {len(scenarios)}")
    print(f"Total Probability: {total_prob:.2f} (target: 1.0)")
    print(f"Total Events: {total_events}")
    print(f"Avg Events per Scenario: {total_events / len(scenarios):.1f}")

    # Event type distribution
    event_types = {}
    for scenario in scenarios:
        for event in scenario.events:
            event_types[event.type.value] = event_types.get(event.type.value, 0) + 1

    print(f"\nEvent Type Distribution:")
    for event_type, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  {event_type}: {count}")

    # Step 7: Export JSON
    print("\n[STEP 7] Exporting scenarios to JSON...")
    export_data = {
        "match": f"{arsenal.name} vs {liverpool.name}",
        "scenarios": [s.to_dict() for s in scenarios],
        "metadata": {
            "total_scenarios": len(scenarios),
            "total_probability": total_prob,
            "total_events": total_events
        }
    }

    output_file = "generated_scenarios.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    print(f"✓ Exported to {output_file}")

    print("\n" + "="*80)
    print("INSPECTION COMPLETE")
    print("="*80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Inspection interrupted")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
