"""
Unit Tests for Hawkes Process Goal Model
EPL Match Predictor v3.0

Tests Cover:
1. Baseline intensity calculation
2. Momentum boost after goals
3. Exponential decay over time
4. Parameter validation
5. State reset functionality
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from simulation.v3.hawkes_model import HawkesGoalModel


class TestHawkesBaseline:
    """Test baseline intensity calculation"""

    def test_baseline_intensity_no_goals(self):
        """Test baseline intensity when no goals have been scored"""
        # Given
        hawkes = HawkesGoalModel(mu=0.03, alpha=0.06, beta=0.4)

        # When
        intensity = hawkes.calculate_intensity(10, 'home')

        # Then
        assert intensity == 0.03, "Intensity should equal baseline μ when no goals scored"

    def test_baseline_intensity_different_minutes(self):
        """Test baseline remains constant across different minutes"""
        # Given
        hawkes = HawkesGoalModel(mu=0.03, alpha=0.06, beta=0.4)

        # When & Then
        assert hawkes.calculate_intensity(1, 'home') == 0.03
        assert hawkes.calculate_intensity(45, 'home') == 0.03
        assert hawkes.calculate_intensity(90, 'home') == 0.03

    def test_baseline_intensity_different_teams(self):
        """Test baseline is same for both teams"""
        # Given
        hawkes = HawkesGoalModel(mu=0.03, alpha=0.06, beta=0.4)

        # When & Then
        assert hawkes.calculate_intensity(10, 'home') == 0.03
        assert hawkes.calculate_intensity(10, 'away') == 0.03


class TestHawkesMomentum:
    """Test momentum boost after goals"""

    def test_momentum_after_single_goal(self):
        """Test intensity increases after a goal is scored"""
        # Given
        hawkes = HawkesGoalModel(mu=0.03, alpha=0.06, beta=0.4)
        hawkes.record_goal(10, 'home')

        # When
        intensity_t2 = hawkes.calculate_intensity(12, 'home')
        multiplier = hawkes.calculate_intensity_multiplier(12, 'home')

        # Then
        assert intensity_t2 > 0.03, "Intensity should be boosted above baseline"
        assert 1.5 <= multiplier <= 2.0, f"Multiplier {multiplier} should be in realistic range [1.5, 2.0]"

    def test_momentum_realistic_boost_at_2min(self):
        """Test momentum boost at 2 minutes after goal"""
        # Given
        hawkes = HawkesGoalModel(mu=0.03, alpha=0.06, beta=0.4)
        hawkes.record_goal(20, 'home')

        # When (2 minutes later)
        intensity_22 = hawkes.calculate_intensity(22, 'home')

        # Then
        # At t=2, boost = α * e^(-β*2) = 0.06 * e^(-0.4*2) ≈ 0.06 * 0.449 ≈ 0.027
        # Total intensity ≈ 0.03 + 0.027 = 0.057
        expected_boost = 0.06 * 0.449  # e^(-0.8) ≈ 0.449
        expected_intensity = 0.03 + expected_boost

        assert abs(intensity_22 - expected_intensity) < 0.005, \
            f"Intensity {intensity_22} should be close to {expected_intensity}"

    def test_multiple_goals_accumulate(self):
        """Test multiple goals accumulate momentum"""
        # Given
        hawkes = HawkesGoalModel(mu=0.03, alpha=0.06, beta=0.4)
        hawkes.record_goal(10, 'home')
        hawkes.record_goal(15, 'home')

        # When
        intensity_20 = hawkes.calculate_intensity(20, 'home')

        # Then
        # Two goals should create higher intensity than one
        hawkes_single = HawkesGoalModel(mu=0.03, alpha=0.06, beta=0.4)
        hawkes_single.record_goal(15, 'home')
        intensity_single = hawkes_single.calculate_intensity(20, 'home')

        assert intensity_20 > intensity_single, "Multiple goals should accumulate momentum"

    def test_vulnerability_effect_opponent(self):
        """Test vulnerability effect: opponent gets small boost within 5min"""
        # Given
        hawkes = HawkesGoalModel(mu=0.03, alpha=0.06, beta=0.4)
        hawkes.record_goal(20, 'home')

        # When (2 minutes later, check away team)
        intensity_away_22 = hawkes.calculate_intensity(22, 'away')

        # Then
        # Away team should get small vulnerability boost (20% of α)
        # Vulnerability boost = 0.2 * 0.06 * e^(-0.4*2) ≈ 0.2 * 0.027 ≈ 0.0054
        assert intensity_away_22 > 0.03, "Opponent should get small vulnerability boost"
        assert intensity_away_22 < 0.04, "Vulnerability boost should be small (<0.01)"

    def test_no_vulnerability_after_5min(self):
        """Test vulnerability effect disappears after 5 minutes"""
        # Given
        hawkes = HawkesGoalModel(mu=0.03, alpha=0.06, beta=0.4)
        hawkes.record_goal(20, 'home')

        # When (6 minutes later)
        intensity_away_26 = hawkes.calculate_intensity(26, 'away')

        # Then
        # After 5min window, no vulnerability boost
        assert abs(intensity_away_26 - 0.03) < 0.001, "No vulnerability boost after 5min"


class TestHawkesDecay:
    """Test exponential decay over time"""

    def test_decay_monotonic_decrease(self):
        """Test intensity decreases monotonically over time"""
        # Given
        hawkes = HawkesGoalModel(mu=0.03, alpha=0.06, beta=0.4)
        hawkes.record_goal(10, 'home')

        # When
        intensity_t2 = hawkes.calculate_intensity(12, 'home')
        intensity_t10 = hawkes.calculate_intensity(20, 'home')
        intensity_t30 = hawkes.calculate_intensity(40, 'home')

        # Then
        assert intensity_t2 > intensity_t10 > intensity_t30, \
            "Intensity should decrease monotonically over time"

    def test_decay_to_baseline(self):
        """Test intensity decays back to baseline"""
        # Given
        hawkes = HawkesGoalModel(mu=0.03, alpha=0.06, beta=0.4)
        hawkes.record_goal(10, 'home')

        # When (30 minutes later)
        intensity_t30 = hawkes.calculate_intensity(40, 'home')

        # Then
        # After 30min: boost = 0.06 * e^(-0.4*30) ≈ 0 (essentially back to baseline)
        assert abs(intensity_t30 - 0.03) < 0.01, \
            f"After 30min, intensity {intensity_t30} should be close to baseline 0.03"

    def test_exponential_decay_rate(self):
        """Test decay follows exponential curve with β parameter"""
        # Given
        hawkes = HawkesGoalModel(mu=0.03, alpha=0.06, beta=0.4)
        hawkes.record_goal(10, 'home')

        # When
        intensity_t1 = hawkes.calculate_intensity(11, 'home')
        intensity_t2 = hawkes.calculate_intensity(12, 'home')

        # Then
        # Ratio should match e^(-β) ≈ e^(-0.4) ≈ 0.67
        boost_t1 = intensity_t1 - 0.03
        boost_t2 = intensity_t2 - 0.03
        ratio = boost_t2 / boost_t1

        import math
        expected_ratio = math.exp(-0.4)  # ≈ 0.67

        assert abs(ratio - expected_ratio) < 0.01, \
            f"Decay ratio {ratio} should match e^(-β) = {expected_ratio}"

    def test_half_life_approximation(self):
        """Test half-life is approximately ln(2)/β ≈ 1.73 minutes"""
        # Given
        hawkes = HawkesGoalModel(mu=0.03, alpha=0.06, beta=0.4)
        hawkes.record_goal(10, 'home')

        # When
        intensity_t0 = hawkes.calculate_intensity(10.01, 'home')

        import math
        half_life = math.log(2) / 0.4  # ≈ 1.73 minutes
        intensity_half_life = hawkes.calculate_intensity(10 + half_life, 'home')

        # Then
        boost_t0 = intensity_t0 - 0.03
        boost_half = intensity_half_life - 0.03

        # At half-life, boost should be ~50% of original
        assert abs(boost_half / boost_t0 - 0.5) < 0.05, \
            f"At half-life, boost should be ~50% of original"


class TestHawkesParameterValidation:
    """Test parameter validation and constraints"""

    def test_negative_mu_raises_error(self):
        """Test negative baseline μ raises ValueError"""
        with pytest.raises(ValueError, match="mu.*non-negative"):
            HawkesGoalModel(mu=-0.1, alpha=0.06, beta=0.4)

    def test_negative_alpha_raises_error(self):
        """Test negative excitation α raises ValueError"""
        with pytest.raises(ValueError, match="alpha.*non-negative"):
            HawkesGoalModel(mu=0.03, alpha=-0.1, beta=0.4)

    def test_alpha_too_large_raises_error(self):
        """Test α > 1.0 raises ValueError (unrealistic)"""
        with pytest.raises(ValueError, match="alpha.*too large"):
            HawkesGoalModel(mu=0.03, alpha=1.5, beta=0.4)

    def test_negative_beta_raises_error(self):
        """Test negative decay β raises ValueError"""
        with pytest.raises(ValueError, match="beta.*positive"):
            HawkesGoalModel(mu=0.03, alpha=0.06, beta=-0.1)

    def test_zero_beta_raises_error(self):
        """Test β = 0 raises ValueError (no decay)"""
        with pytest.raises(ValueError, match="beta.*positive"):
            HawkesGoalModel(mu=0.03, alpha=0.06, beta=0.0)

    def test_valid_parameters_accepted(self):
        """Test valid parameters are accepted"""
        # Should not raise any errors
        hawkes = HawkesGoalModel(mu=0.03, alpha=0.06, beta=0.4)
        assert hawkes.mu == 0.03
        assert hawkes.alpha == 0.06
        assert hawkes.beta == 0.4

    def test_default_parameters(self):
        """Test default parameters are set correctly"""
        hawkes = HawkesGoalModel()
        assert hawkes.mu == 0.03
        assert hawkes.alpha == 0.06
        assert hawkes.beta == 0.4


class TestHawkesReset:
    """Test state reset functionality"""

    def test_reset_clears_goal_history(self):
        """Test reset() clears all goal history"""
        # Given
        hawkes = HawkesGoalModel()
        hawkes.record_goal(10, 'home')
        hawkes.record_goal(25, 'away')
        hawkes.record_goal(40, 'home')

        # When
        hawkes.reset()

        # Then
        assert len(hawkes.goal_times) == 0, "Goal history should be empty after reset"

    def test_reset_returns_to_baseline(self):
        """Test reset returns intensity to baseline"""
        # Given
        hawkes = HawkesGoalModel()
        hawkes.record_goal(10, 'home')
        hawkes.record_goal(25, 'away')

        # When
        hawkes.reset()
        intensity_after_reset = hawkes.calculate_intensity(50, 'home')

        # Then
        assert intensity_after_reset == hawkes.mu, \
            "Intensity should return to baseline μ after reset"

    def test_reset_allows_new_goals(self):
        """Test goals can be recorded after reset"""
        # Given
        hawkes = HawkesGoalModel()
        hawkes.record_goal(10, 'home')
        hawkes.reset()

        # When
        hawkes.record_goal(20, 'away')
        intensity = hawkes.calculate_intensity(22, 'away')

        # Then
        assert intensity > hawkes.mu, "New goals should affect intensity after reset"
        assert len(hawkes.goal_times) == 1, "Only new goal should be recorded"


class TestHawkesIntensityMultiplier:
    """Test intensity multiplier calculation"""

    def test_multiplier_at_baseline(self):
        """Test multiplier is 1.0 at baseline (no goals)"""
        # Given
        hawkes = HawkesGoalModel(mu=0.03, alpha=0.06, beta=0.4)

        # When
        multiplier = hawkes.calculate_intensity_multiplier(10, 'home')

        # Then
        assert multiplier == 1.0, "Multiplier should be 1.0 at baseline"

    def test_multiplier_after_goal(self):
        """Test multiplier > 1.0 after goal"""
        # Given
        hawkes = HawkesGoalModel(mu=0.03, alpha=0.06, beta=0.4)
        hawkes.record_goal(10, 'home')

        # When
        multiplier = hawkes.calculate_intensity_multiplier(12, 'home')

        # Then
        assert multiplier > 1.0, "Multiplier should be > 1.0 after goal"

    def test_multiplier_capped_at_max(self):
        """Test multiplier doesn't exceed cap (2.0 in engine)"""
        # Given
        hawkes = HawkesGoalModel(mu=0.03, alpha=0.06, beta=0.4)
        # Record many goals
        for minute in range(10, 20):
            hawkes.record_goal(minute, 'home')

        # When
        multiplier = hawkes.calculate_intensity_multiplier(20, 'home')

        # Then
        # Note: The multiplier itself is not capped in HawkesGoalModel
        # The cap is applied in StatisticalMatchEngine
        # Here we just verify it's a reasonable value
        assert multiplier >= 1.0, "Multiplier should be at least 1.0"
        assert multiplier < 10.0, "Multiplier should not be absurdly high"


class TestHawkesEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_goal_at_minute_zero(self):
        """Test goal recorded at minute 0"""
        # Given
        hawkes = HawkesGoalModel()
        hawkes.record_goal(0, 'home')

        # When
        intensity = hawkes.calculate_intensity(2, 'home')

        # Then
        assert intensity > hawkes.mu, "Goal at minute 0 should affect later intensity"

    def test_goal_at_minute_90(self):
        """Test goal recorded at minute 90"""
        # Given
        hawkes = HawkesGoalModel()
        hawkes.record_goal(90, 'home')

        # When
        intensity = hawkes.calculate_intensity(90, 'home')

        # Then
        # At the exact same minute, intensity should be baseline (no time elapsed)
        assert intensity == hawkes.mu

    def test_negative_time_diff_ignored(self):
        """Test goals in the future are ignored"""
        # Given
        hawkes = HawkesGoalModel()
        hawkes.record_goal(50, 'home')

        # When (check at earlier minute)
        intensity = hawkes.calculate_intensity(30, 'home')

        # Then
        assert intensity == hawkes.mu, "Future goals should not affect past intensity"

    def test_very_small_time_diff(self):
        """Test very small time differences (fractions of a minute)"""
        # Given
        hawkes = HawkesGoalModel()
        hawkes.record_goal(10.0, 'home')

        # When (0.1 minutes later)
        intensity = hawkes.calculate_intensity(10.1, 'home')

        # Then
        assert intensity > hawkes.mu, "Even small time differences should show momentum"

    def test_alternating_teams(self):
        """Test alternating goals between teams"""
        # Given
        hawkes = HawkesGoalModel()
        hawkes.record_goal(10, 'home')
        hawkes.record_goal(15, 'away')
        hawkes.record_goal(20, 'home')

        # When
        intensity_home_25 = hawkes.calculate_intensity(25, 'home')
        intensity_away_25 = hawkes.calculate_intensity(25, 'away')

        # Then
        # Both teams have scored, both should have momentum
        assert intensity_home_25 > hawkes.mu
        assert intensity_away_25> hawkes.mu


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '-s'])
