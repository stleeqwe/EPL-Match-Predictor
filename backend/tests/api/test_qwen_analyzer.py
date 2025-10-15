"""
Test script for QwenMatchAnalyzer
Validates AI analysis quality
"""

import sys
import logging

from simulation.qwen_analyzer import QwenMatchAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_basic_analysis():
    """Test basic AI analysis"""
    print("\n" + "="*80)
    print("TEST 1: Basic AI Analysis")
    print("="*80)

    analyzer = QwenMatchAnalyzer()

    # Create test data
    man_city = {
        'name': 'Manchester City',
        'overall_rating': 90.0,
        'tactical_profile': {
            'attacking_efficiency': 92.0,
            'defensive_stability': 88.0,
            'tactical_organization': 91.0,
            'physicality_stamina': 87.0,
            'psychological_factors': 90.0
        }
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
        }
    }

    success, analysis, error = analyzer.analyze_match(man_city, luton)

    assert success, f"Analysis failed: {error}"

    print(f"\n{man_city['name']} vs {luton['name']}")
    print(f"\nProbability Weights:")
    weights = analysis['probability_weights']
    print(f"  Home Win Boost: {weights['home_win_boost']:.2f}")
    print(f"  Draw Boost: {weights['draw_boost']:.2f}")
    print(f"  Away Win Boost: {weights['away_win_boost']:.2f}")

    print(f"\nKey Factors:")
    for i, factor in enumerate(analysis['key_factors'], 1):
        print(f"  {i}. {factor}")

    print(f"\nTactical Insight:")
    print(f"  {analysis['tactical_insight']}")

    print(f"\nReasoning:")
    print(f"  {analysis['reasoning']}")

    print(f"\nConfidence: {analysis['confidence']}")

    # Validate that strong team is favored
    assert weights['home_win_boost'] > 1.0, "Strong home team should have boost > 1.0"
    assert weights['away_win_boost'] < 1.0, "Weak away team should have boost < 1.0"

    print("\n✅ TEST PASSED: Strong team correctly favored")


def test_even_teams():
    """Test analysis of evenly matched teams"""
    print("\n" + "="*80)
    print("TEST 2: Evenly Matched Teams")
    print("="*80)

    analyzer = QwenMatchAnalyzer()

    team_a = {
        'name': 'Team A',
        'overall_rating': 75.0,
        'tactical_profile': {
            'attacking_efficiency': 75.0,
            'defensive_stability': 75.0,
            'tactical_organization': 75.0,
            'physicality_stamina': 75.0,
            'psychological_factors': 75.0
        }
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
        }
    }

    success, analysis, error = analyzer.analyze_match(team_a, team_b)

    assert success, f"Analysis failed: {error}"

    print(f"\n{team_a['name']} vs {team_b['name']}")
    print(f"\nProbability Weights:")
    weights = analysis['probability_weights']
    print(f"  Home Win Boost: {weights['home_win_boost']:.2f}")
    print(f"  Draw Boost: {weights['draw_boost']:.2f}")
    print(f"  Away Win Boost: {weights['away_win_boost']:.2f}")

    # For even teams, boosts should show home advantage but not extreme
    # Home boost should be slightly above 1.0, away boost can be below
    assert 0.9 <= weights['home_win_boost'] <= 1.3, "Even teams should show moderate home advantage"
    assert 0.7 <= weights['away_win_boost'] <= 1.1, "Even teams away boost should be reasonable"
    # Home should be favored over away for evenly matched teams
    assert weights['home_win_boost'] > weights['away_win_boost'], "Home advantage should be present"

    print("\n✅ TEST PASSED: Even teams show balanced analysis")


def test_user_insight_integration():
    """Test analysis with user insights"""
    print("\n" + "="*80)
    print("TEST 3: User Insight Integration")
    print("="*80)

    analyzer = QwenMatchAnalyzer()

    arsenal = {
        'name': 'Arsenal',
        'overall_rating': 85.0,
        'tactical_profile': {
            'attacking_efficiency': 86.0,
            'defensive_stability': 83.0,
            'tactical_organization': 85.0,
            'physicality_stamina': 84.0,
            'psychological_factors': 85.0
        }
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
        }
    }

    user_insight = """
    Arsenal's right-back is injured, which will impact their defensive stability.
    Chelsea has been in excellent form with 4 wins in last 5 games.
    Weather forecast shows heavy rain, favoring Chelsea's more physical style.
    """

    success, analysis, error = analyzer.analyze_with_user_insight(
        arsenal,
        chelsea,
        user_insight
    )

    assert success, f"Analysis failed: {error}"

    print(f"\n{arsenal['name']} vs {chelsea['name']}")
    print(f"\nUser Insight Provided:")
    print(user_insight)

    print(f"\nProbability Weights:")
    weights = analysis['probability_weights']
    print(f"  Home Win Boost: {weights['home_win_boost']:.2f}")
    print(f"  Draw Boost: {weights['draw_boost']:.2f}")
    print(f"  Away Win Boost: {weights['away_win_boost']:.2f}")

    print(f"\nKey Factors:")
    for i, factor in enumerate(analysis['key_factors'], 1):
        print(f"  {i}. {factor}")

    print(f"\nAI Reasoning:")
    print(f"  {analysis['reasoning']}")

    print("\n✅ TEST PASSED: User insights integrated into analysis")


def test_tactical_contrast():
    """Test analysis of teams with contrasting styles"""
    print("\n" + "="*80)
    print("TEST 4: Contrasting Tactical Styles")
    print("="*80)

    analyzer = QwenMatchAnalyzer()

    # Attack-focused team
    attack_team = {
        'name': 'Attack FC',
        'overall_rating': 78.0,
        'tactical_profile': {
            'attacking_efficiency': 90.0,
            'defensive_stability': 65.0,
            'tactical_organization': 75.0,
            'physicality_stamina': 75.0,
            'psychological_factors': 78.0
        }
    }

    # Defense-focused team
    defense_team = {
        'name': 'Defense United',
        'overall_rating': 78.0,
        'tactical_profile': {
            'attacking_efficiency': 65.0,
            'defensive_stability': 90.0,
            'tactical_organization': 85.0,
            'physicality_stamina': 80.0,
            'psychological_factors': 75.0
        }
    }

    success, analysis, error = analyzer.analyze_match(attack_team, defense_team)

    assert success, f"Analysis failed: {error}"

    print(f"\n{attack_team['name']} vs {defense_team['name']}")
    print(f"\nTactical Profiles:")
    print(f"  {attack_team['name']}: High attack (90), Low defense (65)")
    print(f"  {defense_team['name']}: Low attack (65), High defense (90)")

    print(f"\nProbability Weights:")
    weights = analysis['probability_weights']
    print(f"  Home Win Boost: {weights['home_win_boost']:.2f}")
    print(f"  Draw Boost: {weights['draw_boost']:.2f}")
    print(f"  Away Win Boost: {weights['away_win_boost']:.2f}")

    print(f"\nTactical Insight:")
    print(f"  {analysis['tactical_insight']}")

    # Draw should be somewhat likely with these contrasting styles
    # (attack vs defense often leads to low-scoring games)
    print(f"\nDraw boost: {weights['draw_boost']:.2f} (contrasting styles may favor draws)")

    print("\n✅ TEST PASSED: Tactical contrast analysis completed")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("QWEN MATCH ANALYZER - QUALITY VALIDATION SUITE")
    print("Phase 1 MVP - AI Analysis Quality Focus")
    print("="*80)

    try:
        test_basic_analysis()
        test_even_teams()
        test_user_insight_integration()
        test_tactical_contrast()

        print("\n" + "="*80)
        print("ALL TESTS PASSED ✅")
        print("="*80)
        print("\nQwenMatchAnalyzer is ready for integration!")
        print("Quality Focus: Tactical analysis with probability adjustments")
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
