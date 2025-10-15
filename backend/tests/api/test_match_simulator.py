"""
Test script for MatchSimulator (Integrated)
Validates complete simulation pipeline: AI Analysis + Statistical Engine
"""

import sys
import logging
import json

from simulation.match_simulator import MatchSimulator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_quick_predict():
    """Test quick prediction API"""
    print("\n" + "="*80)
    print("TEST 1: Quick Prediction (Simple API)")
    print("="*80)

    simulator = MatchSimulator(num_simulations=1000, enable_ai_analysis=True)

    success, prediction, error = simulator.quick_predict(
        home_team_name="Manchester City",
        away_team_name="Luton Town",
        home_rating=90.0,
        away_rating=68.0
    )

    assert success, f"Simulation failed: {error}"

    print(f"\nManchester City vs Luton Town")
    print(f"Predicted Score: {prediction['prediction']['predicted_score']}")
    print(f"Expected Goals: Home {prediction['prediction']['expected_goals']['home']}, "
          f"Away {prediction['prediction']['expected_goals']['away']}")

    print(f"\nProbabilities:")
    probs = prediction['prediction']['probabilities']
    print(f"  Home Win: {probs['home_win']:.1%}")
    print(f"  Draw: {probs['draw']:.1%}")
    print(f"  Away Win: {probs['away_win']:.1%}")

    print(f"\nConfidence: {prediction['prediction']['confidence']}")

    if prediction['ai_analysis']:
        print(f"\nAI Key Factors:")
        for i, factor in enumerate(prediction['ai_analysis']['key_factors'], 1):
            print(f"  {i}. {factor}")

    assert probs['home_win'] > 0.6, "Man City should be strong favorites"

    print("\n✅ TEST PASSED: Quick prediction works correctly")


def test_full_simulation():
    """Test full simulation with detailed team data"""
    print("\n" + "="*80)
    print("TEST 2: Full Simulation (Detailed Team Data)")
    print("="*80)

    simulator = MatchSimulator(num_simulations=1000, enable_ai_analysis=True)

    # Detailed team data
    arsenal = {
        'name': 'Arsenal',
        'overall_rating': 85.0,
        'tactical_profile': {
            'attacking_efficiency': 86.0,
            'defensive_stability': 83.0,
            'tactical_organization': 85.0,
            'physicality_stamina': 84.0,
            'psychological_factors': 85.0
        },
        'recent_form': 'WWDWL',
        'key_players': ['Bukayo Saka', 'Martin Ødegaard', 'Gabriel Martinelli']
    }

    chelsea = {
        'name': 'Chelsea',
        'overall_rating': 82.0,
        'tactical_profile': {
            'attacking_efficiency': 81.0,
            'defensive_stability': 82.0,
            'tactical_organization': 83.0,
            'physicality_stamina': 82.0,
            'psychological_factors': 80.0
        },
        'recent_form': 'WDWWW',
        'key_players': ['Cole Palmer', 'Nicolas Jackson', 'Enzo Fernández']
    }

    success, prediction, error = simulator.simulate(
        home_team_name='Arsenal',
        away_team_name='Chelsea',
        home_team_data=arsenal,
        away_team_data=chelsea
    )

    assert success, f"Simulation failed: {error}"

    print(f"\n{arsenal['name']} vs {chelsea['name']}")
    print(f"Predicted Score: {prediction['prediction']['predicted_score']}")

    print(f"\nScore Distribution (Top 5):")
    for i, (score, prob) in enumerate(list(prediction['prediction']['score_distribution'].items())[:5], 1):
        print(f"  {i}. {score}: {prob:.1%}")

    print(f"\nMatch Events:")
    events = prediction['match_events']
    print(f"  Shots: Home {events['home_shots']}, Away {events['away_shots']}")
    print(f"  Possession: Home {events['home_possession']}%, Away {events['away_possession']}%")

    if prediction['ai_analysis']:
        print(f"\nAI Tactical Insight:")
        print(f"  {prediction['ai_analysis']['tactical_insight']}")

    print("\n✅ TEST PASSED: Full simulation completed")


def test_user_insight_integration():
    """Test simulation with user insights"""
    print("\n" + "="*80)
    print("TEST 3: User Insight Integration (MVP Priority)")
    print("="*80)

    simulator = MatchSimulator(num_simulations=1000, enable_ai_analysis=True)

    liverpool = {
        'name': 'Liverpool',
        'overall_rating': 87.0,
        'tactical_profile': {
            'attacking_efficiency': 88.0,
            'defensive_stability': 85.0,
            'tactical_organization': 86.0,
            'physicality_stamina': 87.0,
            'psychological_factors': 86.0
        }
    }

    man_united = {
        'name': 'Manchester United',
        'overall_rating': 80.0,
        'tactical_profile': {
            'attacking_efficiency': 79.0,
            'defensive_stability': 78.0,
            'tactical_organization': 81.0,
            'physicality_stamina': 80.0,
            'psychological_factors': 79.0
        }
    }

    user_insight = """
    Liverpool's key striker is injured and will miss this match.
    Manchester United has a new manager bounce effect after recent appointment.
    Historical head-to-head heavily favors Liverpool at Anfield.
    """

    success, prediction, error = simulator.simulate(
        home_team_name='Liverpool',
        away_team_name='Manchester United',
        home_team_data=liverpool,
        away_team_data=man_united,
        user_insight=user_insight
    )

    assert success, f"Simulation failed: {error}"

    print(f"\n{liverpool['name']} vs {man_united['name']}")
    print(f"\nUser Insight:")
    print(user_insight)

    print(f"\nPrediction:")
    print(f"  Score: {prediction['prediction']['predicted_score']}")
    probs = prediction['prediction']['probabilities']
    print(f"  Home Win: {probs['home_win']:.1%}")
    print(f"  Draw: {probs['draw']:.1%}")
    print(f"  Away Win: {probs['away_win']:.1%}")

    if prediction['ai_analysis']:
        print(f"\nAI Reasoning (incorporating user insight):")
        print(f"  {prediction['ai_analysis']['reasoning']}")

    assert prediction['user_insight'] == user_insight, "User insight should be included"

    print("\n✅ TEST PASSED: User insights integrated into prediction")


def test_without_ai():
    """Test simulation without AI analysis (statistical only)"""
    print("\n" + "="*80)
    print("TEST 4: Statistical-Only Simulation (No AI)")
    print("="*80)

    # Disable AI analysis
    simulator = MatchSimulator(num_simulations=1000, enable_ai_analysis=False)

    success, prediction, error = simulator.quick_predict(
        home_team_name="Team A",
        away_team_name="Team B",
        home_rating=75.0,
        away_rating=75.0
    )

    assert success, f"Simulation failed: {error}"

    print(f"\nTeam A vs Team B (No AI)")
    print(f"Predicted Score: {prediction['prediction']['predicted_score']}")
    print(f"Probabilities: Home {prediction['prediction']['probabilities']['home_win']:.1%}, "
          f"Draw {prediction['prediction']['probabilities']['draw']:.1%}, "
          f"Away {prediction['prediction']['probabilities']['away_win']:.1%}")

    assert prediction['ai_analysis'] is None, "AI analysis should be None when disabled"
    assert prediction['metadata']['ai_enabled'] is False, "AI should be disabled in metadata"

    print("\n✅ TEST PASSED: Statistical-only mode works correctly")


def test_comprehensive_output():
    """Test and display comprehensive prediction output"""
    print("\n" + "="*80)
    print("TEST 5: Comprehensive Output Validation")
    print("="*80)

    simulator = MatchSimulator(num_simulations=1000, enable_ai_analysis=True)

    success, prediction, error = simulator.quick_predict(
        home_team_name="Manchester City",
        away_team_name="Arsenal",
        home_rating=90.0,
        away_rating=85.0
    )

    assert success, f"Simulation failed: {error}"

    # Validate all required fields
    assert 'match' in prediction
    assert 'prediction' in prediction
    assert 'match_events' in prediction
    assert 'metadata' in prediction

    assert 'probabilities' in prediction['prediction']
    assert 'predicted_score' in prediction['prediction']
    assert 'expected_goals' in prediction['prediction']
    assert 'confidence' in prediction['prediction']

    print("\nComprehensive Prediction Output:")
    print("="*80)
    print(json.dumps(prediction, indent=2, default=str))

    print("\n✅ TEST PASSED: All required fields present")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("MATCH SIMULATOR - INTEGRATED SYSTEM TEST")
    print("Phase 1 MVP - AI + Statistical Engine")
    print("="*80)

    try:
        test_quick_predict()
        test_full_simulation()
        test_user_insight_integration()
        test_without_ai()
        test_comprehensive_output()

        print("\n" + "="*80)
        print("ALL TESTS PASSED ✅")
        print("="*80)
        print("\nMatchSimulator is ready for API integration!")
        print("Quality Focus: AI-guided statistical simulation")
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
