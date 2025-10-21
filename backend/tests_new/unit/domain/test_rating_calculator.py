"""
Phase 2 Unit Tests - RatingCalculator Domain Service
Tests rating calculation logic
"""
import pytest
from backend.core.domain.services.rating_calculator import RatingCalculator
from backend.core.domain.value_objects.position import Position
from backend.core.domain.value_objects.rating_value import RatingValue


class TestRatingCalculator:
    """Test RatingCalculator domain service"""

    def test_calculate_weighted_average_striker(self):
        """Test weighted average calculation for striker"""
        position = Position.from_string("FW", "ST")

        ratings = {
            'finishing': 4.5,
            'shot_power': 4.0,
            'composure': 4.25,
            'off_ball_movement': 4.0,
            'hold_up_play': 3.5,
            'heading': 3.75,
            'acceleration': 4.0,
            'physicality_balance': 3.75,
            'jumping': 3.5
        }

        result = RatingCalculator.calculate_weighted_average(ratings, position)

        assert isinstance(result, RatingValue)
        assert 3.0 <= result.value <= 5.0
        # Result should be rounded to 0.25 step
        assert result.value % 0.25 == 0.0

    def test_calculate_weighted_average_goalkeeper(self):
        """Test weighted average calculation for goalkeeper"""
        position = Position.from_string("GK")

        ratings = {
            'reflexes': 4.5,
            'positioning': 4.25,
            'handling': 4.0,
            'one_on_one': 4.25,
            'aerial_control': 4.0,
            'buildup': 3.5,
            'leadership_communication': 4.0,
            'long_kick': 3.75
        }

        result = RatingCalculator.calculate_weighted_average(ratings, position)

        assert isinstance(result, RatingValue)
        assert result.value > 3.5  # Should be relatively high

    def test_get_required_attributes(self):
        """Test getting required attributes for position"""
        st_position = Position.from_string("FW", "ST")
        gk_position = Position.from_string("GK")

        st_attrs = RatingCalculator.get_required_attributes(st_position)
        gk_attrs = RatingCalculator.get_required_attributes(gk_position)

        assert len(st_attrs) == 9  # ST has 9 attributes
        assert len(gk_attrs) == 8  # GK has 8 attributes
        assert 'finishing' in st_attrs
        assert 'reflexes' in gk_attrs

    def test_validate_ratings_complete(self):
        """Test validation with complete ratings"""
        position = Position.from_string("FW", "ST")

        ratings = {
            'finishing': 4.5,
            'shot_power': 4.0,
            'composure': 4.25,
            'off_ball_movement': 4.0,
            'hold_up_play': 3.5,
            'heading': 3.75,
            'acceleration': 4.0,
            'physicality_balance': 3.75,
            'jumping': 3.5
        }

        is_valid, missing = RatingCalculator.validate_ratings(ratings, position)

        assert is_valid is True
        assert len(missing) == 0

    def test_validate_ratings_incomplete(self):
        """Test validation with missing attributes"""
        position = Position.from_string("FW", "ST")

        ratings = {
            'finishing': 4.5,
            'shot_power': 4.0,
            # Missing 7 other attributes
        }

        is_valid, missing = RatingCalculator.validate_ratings(ratings, position)

        assert is_valid is False
        assert len(missing) == 7

    def test_get_attribute_weight(self):
        """Test getting attribute weight"""
        position = Position.from_string("FW", "ST")

        finishing_weight = RatingCalculator.get_attribute_weight(position, "finishing")

        assert finishing_weight == 0.15  # ST finishing weight is 15%
        assert 0.0 < finishing_weight <= 1.0

    def test_get_top_attributes(self):
        """Test getting top weighted attributes"""
        position = Position.from_string("FW", "ST")

        ratings = {
            'finishing': 5.0,  # High rating on important attribute
            'shot_power': 2.0,
            'composure': 4.0,
            'off_ball_movement': 4.5,
            'hold_up_play': 3.0,
            'heading': 2.5,
            'acceleration': 3.5,
            'physicality_balance': 3.0,
            'jumping': 2.5
        }

        top = RatingCalculator.get_top_attributes(ratings, position, n=3)

        assert len(top) == 3
        # Should be sorted by weighted contribution
        assert top[0][2] >= top[1][2] >= top[2][2]

    def test_compare_players(self):
        """Test comparing two players"""
        position = Position.from_string("FW", "ST")

        player1_ratings = {
            'finishing': 5.0,
            'shot_power': 4.5,
            'composure': 4.0,
            'off_ball_movement': 4.0,
            'hold_up_play': 3.5,
            'heading': 3.5,
            'acceleration': 4.0,
            'physicality_balance': 4.0,
            'jumping': 3.5
        }

        player2_ratings = {
            'finishing': 4.0,
            'shot_power': 4.0,
            'composure': 4.5,
            'off_ball_movement': 4.5,
            'hold_up_play': 4.0,
            'heading': 4.0,
            'acceleration': 3.5,
            'physicality_balance': 3.5,
            'jumping': 4.0
        }

        comparison = RatingCalculator.compare_players(
            player1_ratings,
            player2_ratings,
            position
        )

        assert 'player1_overall' in comparison
        assert 'player2_overall' in comparison
        assert 'overall_difference' in comparison
        assert 'attribute_differences' in comparison

    def test_suggest_improvements(self):
        """Test improvement suggestions"""
        position = Position.from_string("FW", "ST")

        ratings = {
            'finishing': 3.0,
            'shot_power': 3.0,
            'composure': 3.5,
            'off_ball_movement': 3.5,
            'hold_up_play': 2.5,
            'heading': 2.5,
            'acceleration': 3.0,
            'physicality_balance': 3.0,
            'jumping': 2.5
        }

        suggestions = RatingCalculator.suggest_improvements(
            ratings,
            position,
            target_overall=4.0
        )

        assert 'current_overall' in suggestions
        assert 'target_overall' in suggestions
        assert 'gap' in suggestions
        assert 'top_improvement_areas' in suggestions
        assert len(suggestions['top_improvement_areas']) <= 5

    def test_weights_sum_to_one(self):
        """Test that position weights sum to approximately 1.0"""
        from backend.core.domain.value_objects.position import DetailedPosition

        for detailed_pos in DetailedPosition:
            weights = RatingCalculator.POSITION_WEIGHTS.get(detailed_pos)
            if weights:
                total = sum(weights.values())
                # Should sum to 1.0 (allow small floating point tolerance)
                assert abs(total - 1.0) < 0.01, f"{detailed_pos.value} weights sum to {total}, not 1.0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
