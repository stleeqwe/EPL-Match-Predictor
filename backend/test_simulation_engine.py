#!/usr/bin/env python3
"""
Simulation Engine Test Script
Tests the complete V2 pipeline with Gemini AI
"""

import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from ai.ai_factory import get_ai_client
from services.enriched_data_loader import EnrichedDomainDataLoader
from simulation.v2.simulation_pipeline import get_pipeline, PipelineConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_gemini_connection():
    """Test 1: Gemini API connectivity"""
    print("\n" + "="*70)
    print("TEST 1: Gemini API Connection")
    print("="*70)

    try:
        client = get_ai_client()
        model_info = client.get_model_info()
        print(f"✓ AI Client initialized: {model_info['provider']}")
        print(f"✓ Model: {model_info['model']}")

        # Health check
        is_healthy, error = client.health_check()
        if is_healthy:
            print("✓ Health check passed")
            return True
        else:
            print(f"✗ Health check failed: {error}")
            return False

    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False


def test_data_loading():
    """Test 2: Team data loading"""
    print("\n" + "="*70)
    print("TEST 2: Team Data Loading")
    print("="*70)

    try:
        loader = EnrichedDomainDataLoader()

        # Load Arsenal
        arsenal = loader.load_team_data("Arsenal")
        print(f"✓ Arsenal data loaded")
        print(f"  - Players: {len(arsenal.lineup)}")
        print(f"  - Formation: {arsenal.formation}")
        print(f"  - Has formation tactics: {arsenal.formation_tactics is not None}")
        print(f"  - Attack strength: {arsenal.derived_strengths.attack_strength:.1f}/100")
        print(f"  - Defense strength: {arsenal.derived_strengths.defense_strength:.1f}/100")

        # Load Liverpool
        liverpool = loader.load_team_data("Liverpool")
        print(f"✓ Liverpool data loaded")
        print(f"  - Players: {len(liverpool.lineup)}")
        print(f"  - Formation: {liverpool.formation}")
        print(f"  - Has formation tactics: {liverpool.formation_tactics is not None}")
        print(f"  - Attack strength: {liverpool.derived_strengths.attack_strength:.1f}/100")
        print(f"  - Defense strength: {liverpool.derived_strengths.defense_strength:.1f}/100")

        return True, arsenal, liverpool

    except Exception as e:
        print(f"✗ Data loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None


def test_simple_simulation(home_team_data, away_team_data):
    """Test 3: Simple V2 Pipeline simulation"""
    print("\n" + "="*70)
    print("TEST 3: V2 Pipeline Simulation (Quick Test)")
    print("="*70)

    try:
        # Use minimal config for quick test
        config = PipelineConfig(
            max_iterations=2,  # Reduced from 5
            initial_runs=10,   # Reduced from 100
            final_runs=50,     # Reduced from 3000
            convergence_threshold=0.75
        )

        pipeline = get_pipeline(config=config)

        match_context = {
            'venue': 'Emirates Stadium',
            'competition': 'Premier League',
            'importance': 'top_clash'
        }

        print(f"Running simulation: {home_team_data.name} vs {away_team_data.name}")
        print(f"Config: {config.max_iterations} iterations, {config.initial_runs} initial runs")

        start_time = datetime.now()

        success, result, error = pipeline.run_enriched(
            home_team=home_team_data,
            away_team=away_team_data,
            match_context=match_context
        )

        elapsed = (datetime.now() - start_time).total_seconds()

        if success:
            print(f"\n✓ Simulation completed in {elapsed:.1f}s")

            # Display results
            report = result['report']
            prediction = report['prediction']

            print(f"\n--- Results ---")
            print(f"Converged: {result['converged']}")
            print(f"Iterations: {result['iterations']}/{config.max_iterations}")
            print(f"Total simulations: {result['metadata']['total_simulations']}")

            print(f"\n--- Prediction ---")
            win_probs = prediction['win_probabilities']
            print(f"Home win: {win_probs['home']:.1%}")
            print(f"Draw:     {win_probs['draw']:.1%}")
            print(f"Away win: {win_probs['away']:.1%}")

            xg = prediction['expected_goals']
            print(f"\nExpected goals: {xg['home']:.2f} - {xg['away']:.2f}")

            print(f"\n--- Dominant Scenario ---")
            dominant = report['dominant_scenario']
            print(f"Name: {dominant['name']}")
            print(f"Probability: {dominant['probability']:.1%}")
            print(f"Reasoning: {dominant['reasoning'][:100]}...")

            return True
        else:
            print(f"\n✗ Simulation failed: {error}")
            return False

    except Exception as e:
        print(f"✗ Simulation error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("EPL MATCH PREDICTOR - SIMULATION ENGINE TEST")
    print("="*70)
    print(f"Timestamp: {datetime.now().isoformat()}")

    results = {}

    # Test 1: Gemini connection
    results['gemini'] = test_gemini_connection()
    if not results['gemini']:
        print("\n❌ Gemini connection failed. Aborting tests.")
        return

    # Test 2: Data loading
    data_success, home_team, away_team = test_data_loading()
    results['data_loading'] = data_success
    if not data_success:
        print("\n❌ Data loading failed. Aborting tests.")
        return

    # Test 3: Simple simulation
    results['simulation'] = test_simple_simulation(home_team, away_team)

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(results.values())
    if all_passed:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed.")

    return all_passed


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
