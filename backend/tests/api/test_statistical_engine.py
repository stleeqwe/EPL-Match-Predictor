"""
Test script for StatisticalMatchEngine
Validates simulation quality against EPL baseline statistics
"""

import sys
import logging
from simulation.statistical_engine import StatisticalMatchEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_basic_simulation():
    """Test basic simulation functionality"""
    print("\n" + "="*80)
    print("TEST 1: Basic Simulation Functionality")
    print("="*80)

    engine = StatisticalMatchEngine(num_simulations=1000)

    # Create test team data
    man_city = {
        'name': 'Manchester City',
        'overall_rating': 90.0,
        'tactical_profile': {
            'attacking_efficiency': 92.0,
            'defensive_stability': 88.0,
            'tactical_organization': 91.0,
            'physicality_stamina': 87.0,
            'psychological_factors': 90.0
        },
        'squad_quality': 90.0
    }

    luton = {
        'name': 'Luton Town',
        'overall_rating': 68.0,
        'tactical_profile': {
            'attacking_efficiency': 65.0,
            'defensive_stability': 67.0,
            'tactical_organization': 70.0,
            'physicality_stamina': 72.0,
            'psychological_factors': 68.0
        },
        'squad_quality': 68.0
    }

    result = engine.simulate_match(man_city, luton)

    print(f"\n{man_city['name']} vs {luton['name']}")
    print(f"Predicted Score: {result['predicted_score']}")
    print(f"Expected Goals: Home {result['expected_goals']['home']}, Away {result['expected_goals']['away']}")
    print(f"Probabilities:")
    print(f"  Home Win: {result['probabilities']['home_win']:.1%}")
    print(f"  Draw: {result['probabilities']['draw']:.1%}")
    print(f"  Away Win: {result['probabilities']['away_win']:.1%}")
    print(f"Confidence: {result['confidence']}")

    print("\nTop 5 Score Predictions:")
    for i, (score, prob) in enumerate(list(result['score_distribution'].items())[:5], 1):
        print(f"  {i}. {score}: {prob:.1%}")

    print("\nAverage Match Events:")
    events = result['events']
    print(f"  Shots: Home {events['home_shots']}, Away {events['away_shots']}")
    print(f"  Shots on Target: Home {events['home_shots_on_target']}, Away {events['away_shots_on_target']}")
    print(f"  Corners: Home {events['home_corners']}, Away {events['away_corners']}")
    print(f"  Possession: Home {events['home_possession']}%, Away {events['away_possession']}%")

    assert result['probabilities']['home_win'] > 0.6, "Man City should be favorites"
    print("\n✅ TEST PASSED: Strong team favored against weak team")


def test_evenly_matched():
    """Test evenly matched teams"""
    print("\n" + "="*80)
    print("TEST 2: Evenly Matched Teams")
    print("="*80)

    engine = StatisticalMatchEngine(num_simulations=1000)

    # Two evenly matched mid-table teams
    team_a = {
        'name': 'Team A',
        'overall_rating': 75.0,
        'tactical_profile': {
            'attacking_efficiency': 75.0,
            'defensive_stability': 75.0,
            'tactical_organization': 75.0,
            'physicality_stamina': 75.0,
            'psychological_factors': 75.0
        },
        'squad_quality': 75.0
    }

    team_b = {
        'name': 'Team B',
        'overall_rating': 75.0,
        'tactical_profile': {
            'attacking_efficiency': 75.0,
            'defensive_stability': 75.0,
            'tactical_organization': 75.0,
            'physicality_stamina': 75.0,
            'psychological_factors': 75.0
        },
        'squad_quality': 75.0
    }

    result = engine.simulate_match(team_a, team_b)

    print(f"\n{team_a['name']} vs {team_b['name']}")
    print(f"Probabilities:")
    print(f"  Home Win: {result['probabilities']['home_win']:.1%}")
    print(f"  Draw: {result['probabilities']['draw']:.1%}")
    print(f"  Away Win: {result['probabilities']['away_win']:.1%}")

    # For evenly matched teams at home, expect home advantage but not too strong
    assert 0.35 < result['probabilities']['home_win'] < 0.55, "Home win probability should show home advantage"
    assert result['probabilities']['draw'] > 0.20, "Draw should be likely for evenly matched teams"

    print("\n✅ TEST PASSED: Even teams show realistic probabilities with home advantage")


def test_baseline_validation():
    """Test engine calibration against EPL baseline"""
    print("\n" + "="*80)
    print("TEST 3: EPL Baseline Validation (Quality Check)")
    print("="*80)

    engine = StatisticalMatchEngine(num_simulations=1000)

    # Run validation
    validation = engine.validate_against_baseline(num_validation_matches=100)

    print("\nValidation Results:")
    print(f"  Validation Matches: {validation['validation_matches']}")
    print(f"  Quality Score: {validation['quality_score']}/100")
    print(f"  Status: {validation['status']}")

    print("\nGoals Comparison:")
    metrics = validation['metrics']
    print(f"  Simulated Avg: {metrics['avg_total_goals']} goals/match")
    print(f"  EPL Baseline: {metrics['baseline_goals']} goals/match")
    print(f"  Deviation: {metrics['goals_deviation']:.2f}")

    print("\nOutcome Probabilities Comparison:")
    print(f"  Home Win: Simulated {metrics['avg_home_win_prob']:.1%} vs Baseline {metrics['baseline_home_win']:.1%}")
    print(f"  Draw: Simulated {metrics['avg_draw_prob']:.1%} vs Baseline {metrics['baseline_draw']:.1%}")
    print(f"  Away Win: Simulated {metrics['avg_away_win_prob']:.1%} vs Baseline {metrics['baseline_away_win']:.1%}")

    assert validation['status'] == 'PASS', f"Quality score too low: {validation['quality_score']}"
    print("\n✅ TEST PASSED: Engine calibrated to EPL statistics")


def test_ai_weights():
    """Test AI weight integration"""
    print("\n" + "="*80)
    print("TEST 4: AI Weight Integration")
    print("="*80)

    engine = StatisticalMatchEngine(num_simulations=1000)

    team_a = {
        'name': 'Team A',
        'overall_rating': 75.0,
        'tactical_profile': {
            'attacking_efficiency': 75.0,
            'defensive_stability': 75.0,
            'tactical_organization': 75.0,
            'physicality_stamina': 75.0,
            'psychological_factors': 75.0
        },
        'squad_quality': 75.0
    }

    team_b = {
        'name': 'Team B',
        'overall_rating': 75.0,
        'tactical_profile': {
            'attacking_efficiency': 75.0,
            'defensive_stability': 75.0,
            'tactical_organization': 75.0,
            'physicality_stamina': 75.0,
            'psychological_factors': 75.0
        },
        'squad_quality': 75.0
    }

    # Simulate without AI weights
    result_no_ai = engine.simulate_match(team_a, team_b)

    # Simulate with AI boosting home win
    ai_weights = {
        'home_win_boost': 1.5,  # Boost home win probability
        'draw_boost': 0.8,
        'away_win_boost': 0.6
    }
    result_with_ai = engine.simulate_match(team_a, team_b, ai_weights=ai_weights)

    print("\nWithout AI Weights:")
    print(f"  Home Win: {result_no_ai['probabilities']['home_win']:.1%}")
    print(f"  Draw: {result_no_ai['probabilities']['draw']:.1%}")
    print(f"  Away Win: {result_no_ai['probabilities']['away_win']:.1%}")

    print("\nWith AI Weights (boosting home win):")
    print(f"  Home Win: {result_with_ai['probabilities']['home_win']:.1%}")
    print(f"  Draw: {result_with_ai['probabilities']['draw']:.1%}")
    print(f"  Away Win: {result_with_ai['probabilities']['away_win']:.1%}")

    assert result_with_ai['probabilities']['home_win'] > result_no_ai['probabilities']['home_win'], \
        "AI weights should boost home win probability"

    print("\n✅ TEST PASSED: AI weights correctly adjust probabilities")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("STATISTICAL MATCH ENGINE - QUALITY VALIDATION SUITE")
    print("Phase 1 MVP - Result Quality Focus")
    print("="*80)

    try:
        test_basic_simulation()
        test_evenly_matched()
        test_baseline_validation()
        test_ai_weights()

        print("\n" + "="*80)
        print("ALL TESTS PASSED ✅")
        print("="*80)
        print("\nStatisticalMatchEngine is ready for integration!")
        print("Quality Focus: EPL-calibrated statistics with realistic outcomes")
        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
