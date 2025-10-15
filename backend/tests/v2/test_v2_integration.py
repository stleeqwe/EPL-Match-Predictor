"""
Integration test for Match Simulator v2.0

Tests the complete workflow:
1. AI parameter generation
2. Iterative refinement loop
3. Bias detection
4. Narrative alignment
5. Convergence
6. Final prediction
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from simulation.v2.match_simulator_v2 import get_match_simulator_v2


def test_v2_quick_prediction():
    """Test quick prediction with v2.0 simulator."""
    print("=" * 80)
    print("v2.0 Integration Test: Quick Prediction")
    print("=" * 80)

    simulator = get_match_simulator_v2()

    # Test case 1: Even teams
    print("\n### Test 1: Even Teams (75 vs 75) ###")
    success, prediction, error = simulator.quick_predict(
        home_team="Manchester United",
        away_team="Liverpool",
        home_rating=75.0,
        away_rating=75.0
    )

    if not success:
        print(f"❌ Test 1 FAILED: {error}")
        return False

    print_prediction_summary(prediction)

    # Test case 2: Strong vs Weak
    print("\n### Test 2: Strong vs Weak (90 vs 68) ###")
    success, prediction, error = simulator.quick_predict(
        home_team="Manchester City",
        away_team="Luton Town",
        home_rating=90.0,
        away_rating=68.0
    )

    if not success:
        print(f"❌ Test 2 FAILED: {error}")
        return False

    print_prediction_summary(prediction)

    # Test case 3: With user insight
    print("\n### Test 3: With User Insight ###")
    success, prediction, error = simulator.quick_predict(
        home_team="Arsenal",
        away_team="Chelsea",
        home_rating=85.0,
        away_rating=82.0,
        user_insight="Arsenal's key striker is injured, Chelsea's new manager has just been appointed"
    )

    if not success:
        print(f"❌ Test 3 FAILED: {error}")
        return False

    print_prediction_summary(prediction)

    print("\n" + "=" * 80)
    print("✅ All v2.0 integration tests PASSED")
    print("=" * 80)

    return True


def print_prediction_summary(prediction: dict):
    """Print a summary of the prediction."""
    match = prediction['match']
    pred = prediction['prediction']
    convergence = prediction['convergence_report']
    metadata = prediction['metadata']

    print(f"\n📊 {match['home_team']} vs {match['away_team']}")
    print("-" * 60)

    # Prediction
    print(f"Predicted Score: {pred['predicted_score']}")
    print(f"Expected Goals: {pred['expected_goals']['home']:.2f} - {pred['expected_goals']['away']:.2f}")
    print(f"Probabilities:")
    print(f"  Home Win: {pred['probabilities']['home_win']:.1%}")
    print(f"  Draw:     {pred['probabilities']['draw']:.1%}")
    print(f"  Away Win: {pred['probabilities']['away_win']:.1%}")
    print(f"Confidence: {pred['confidence']}")

    # Convergence
    print(f"\n🔄 Convergence Report:")
    print(f"  Iterations: {convergence['total_iterations']}")
    print(f"  Converged: {convergence['converged']}")
    print(f"  Final Bias Score: {convergence['final_bias_score']:.2f}")
    print(f"  Final Narrative Alignment: {convergence['final_narrative_alignment']:.2f}%")
    print(f"  Reason: {convergence['convergence_reason']}")

    # Metadata
    print(f"\n⚙️  Metadata:")
    print(f"  Total Simulations: {metadata['total_simulations']}")
    print(f"  Time Elapsed: {metadata['elapsed_seconds']:.2f}s")
    print(f"  Version: {metadata['version']}")


if __name__ == "__main__":
    try:
        success = test_v2_quick_prediction()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
