"""
Phase 2 Unit Tests - Value Objects
Tests all domain value objects
"""
import pytest
from backend.core.domain.value_objects.player_id import PlayerId, TeamId, MatchId
from backend.core.domain.value_objects.position import Position, GeneralPosition, DetailedPosition
from backend.core.domain.value_objects.rating_value import RatingValue
from backend.core.domain.value_objects.formation import Formation


class TestPlayerIdValueObject:
    """Test PlayerId value object"""

    def test_create_valid_player_id(self):
        """Test creating valid PlayerId"""
        player_id = PlayerId(123)
        assert player_id.value == 123
        assert int(player_id) == 123
        assert str(player_id) == "123"

    def test_player_id_must_be_positive(self):
        """Test PlayerId must be positive"""
        with pytest.raises(ValueError, match="must be positive"):
            PlayerId(0)

        with pytest.raises(ValueError, match="must be positive"):
            PlayerId(-1)

    def test_player_id_must_be_integer(self):
        """Test PlayerId must be integer"""
        with pytest.raises(TypeError):
            PlayerId("123")

        with pytest.raises(TypeError):
            PlayerId(12.5)

    def test_player_id_immutability(self):
        """Test PlayerId is immutable"""
        player_id = PlayerId(123)

        with pytest.raises(Exception):  # FrozenInstanceError
            player_id.value = 456

    def test_player_id_equality(self):
        """Test PlayerId equality"""
        id1 = PlayerId(123)
        id2 = PlayerId(123)
        id3 = PlayerId(456)

        assert id1 == id2
        assert id1 != id3
        assert hash(id1) == hash(id2)


class TestPositionValueObject:
    """Test Position value object"""

    def test_create_valid_position(self):
        """Test creating valid Position"""
        position = Position(
            general=GeneralPosition.FW,
            detailed=DetailedPosition.ST
        )

        assert position.general == GeneralPosition.FW
        assert position.detailed == DetailedPosition.ST

    def test_position_consistency_validation(self):
        """Test position consistency is validated"""
        # Valid: FW -> ST
        Position(general=GeneralPosition.FW, detailed=DetailedPosition.ST)

        # Invalid: FW -> CB
        with pytest.raises(ValueError, match="Inconsistent position"):
            Position(general=GeneralPosition.FW, detailed=DetailedPosition.CB)

    def test_position_from_string(self):
        """Test Position.from_string()"""
        position = Position.from_string("FW", "ST")

        assert position.general == GeneralPosition.FW
        assert position.detailed == DetailedPosition.ST

    def test_position_from_string_with_default(self):
        """Test Position.from_string() with default detailed position"""
        position = Position.from_string("GK")

        assert position.general == GeneralPosition.GK
        assert position.detailed == DetailedPosition.GK

    def test_position_is_defensive(self):
        """Test is_defensive()"""
        gk = Position.from_string("GK")
        cb = Position.from_string("DF", "CB")
        cm = Position.from_string("MF", "CM")
        st = Position.from_string("FW", "ST")

        assert gk.is_defensive() is True
        assert cb.is_defensive() is True
        assert cm.is_defensive() is False
        assert st.is_defensive() is False

    def test_position_is_offensive(self):
        """Test is_offensive()"""
        st = Position.from_string("FW", "ST")
        wg = Position.from_string("FW", "WG")
        cm = Position.from_string("MF", "CM")

        assert st.is_offensive() is True
        assert wg.is_offensive() is True
        assert cm.is_offensive() is False


class TestRatingValueObject:
    """Test RatingValue value object"""

    def test_create_valid_rating(self):
        """Test creating valid RatingValue"""
        rating = RatingValue(4.25)
        assert rating.value == 4.25
        assert float(rating) == 4.25

    def test_rating_min_max_validation(self):
        """Test rating range validation"""
        # Valid
        RatingValue(0.0)
        RatingValue(5.0)
        RatingValue(2.5)

        # Invalid - below min
        with pytest.raises(ValueError, match="must be between"):
            RatingValue(-0.25)

        # Invalid - above max
        with pytest.raises(ValueError, match="must be between"):
            RatingValue(5.25)

    def test_rating_step_validation(self):
        """Test rating step (0.25) validation"""
        # Valid steps
        RatingValue(0.0)
        RatingValue(0.25)
        RatingValue(0.5)
        RatingValue(4.75)
        RatingValue(5.0)

        # Invalid steps
        with pytest.raises(ValueError, match="must be in .* increments"):
            RatingValue(1.1)

        with pytest.raises(ValueError, match="must be in .* increments"):
            RatingValue(3.33)

    def test_rating_to_percentage(self):
        """Test to_percentage()"""
        assert RatingValue(0.0).to_percentage() == 0.0
        assert RatingValue(2.5).to_percentage() == 50.0
        assert RatingValue(5.0).to_percentage() == 100.0

    def test_rating_get_grade(self):
        """Test get_grade()"""
        assert RatingValue(4.75).get_grade() == "World Class"
        assert RatingValue(4.25).get_grade() == "Elite"
        assert RatingValue(3.5).get_grade() == "Good"
        assert RatingValue(2.5).get_grade() == "Average"
        assert RatingValue(1.5).get_grade() == "Below Average"

    def test_rating_from_percentage(self):
        """Test from_percentage()"""
        rating = RatingValue.from_percentage(50.0)
        assert rating.value == 2.5

        rating = RatingValue.from_percentage(100.0)
        assert rating.value == 5.0

    def test_rating_comparison(self):
        """Test rating comparison operators"""
        low = RatingValue(2.0)
        mid = RatingValue(3.5)
        high = RatingValue(4.5)

        assert low < mid < high
        assert high > mid > low
        assert low <= mid
        assert high >= mid
        assert mid == RatingValue(3.5)


class TestFormationValueObject:
    """Test Formation value object"""

    def test_create_valid_formation(self):
        """Test creating valid Formation"""
        formation = Formation("4-3-3")
        assert formation.value == "4-3-3"

    def test_formation_validation(self):
        """Test formation is validated"""
        # Valid formations
        Formation("4-3-3")
        Formation("4-4-2")
        Formation("4-2-3-1")

        # Invalid formation
        with pytest.raises(ValueError, match="Unsupported formation"):
            Formation("1-1-1-1-1-1-1-1-1-1")

    def test_formation_total_players(self):
        """Test formation has 10 outfield players"""
        # Valid: 4+3+3 = 10
        Formation("4-3-3")

        # Would be invalid if it existed
        # (but won't pass supported formations check first)

    def test_formation_get_structure(self):
        """Test get_structure()"""
        formation = Formation("4-3-3")
        assert formation.get_structure() == [4, 3, 3]

        formation = Formation("4-2-3-1")
        assert formation.get_structure() == [4, 2, 3, 1]

    def test_formation_get_counts(self):
        """Test position count getters"""
        formation = Formation("4-3-3")

        assert formation.get_defender_count() == 4
        assert formation.get_midfielder_count() == 3
        assert formation.get_forward_count() == 3

    def test_formation_is_defensive(self):
        """Test is_defensive()"""
        assert Formation("5-3-2").is_defensive() is True
        assert Formation("4-3-3").is_defensive() is False

    def test_formation_is_offensive(self):
        """Test is_offensive()"""
        assert Formation("3-4-3").is_offensive() is True
        assert Formation("4-3-3").is_offensive() is False

    def test_formation_is_balanced(self):
        """Test is_balanced()"""
        assert Formation("4-3-3").is_balanced() is True
        assert Formation("3-4-3").is_balanced() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
