"""
Unit Tests for FormationShape Value Object
"""

import pytest
import sys
from pathlib import Path

# Add domain path
domain_path = Path(__file__).parent.parent.parent / "domain"
sys.path.insert(0, str(domain_path))

from value_objects.formation_shape import FormationShape


class TestFormationShapeCreation:
    """FormationShape 생성 테스트"""

    def test_create_valid_formation_shape(self):
        """유효한 포메이션 형태 생성"""
        shape = FormationShape(defenders=4, midfielders=3, forwards=3)
        assert shape.defenders == 4
        assert shape.midfielders == 3
        assert shape.forwards == 3

    def test_create_with_total_not_10_raises_error(self):
        """총 인원이 10명이 아닐 때 에러"""
        with pytest.raises(ValueError, match="Total field players must be 10"):
            FormationShape(defenders=5, midfielders=3, forwards=3)  # 11명

    def test_create_with_too_few_defenders_raises_error(self):
        """수비수가 너무 적을 때 에러"""
        with pytest.raises(ValueError, match="defenders must be between"):
            FormationShape(defenders=2, midfielders=5, forwards=3)

    def test_create_with_too_many_defenders_raises_error(self):
        """수비수가 너무 많을 때 에러"""
        with pytest.raises(ValueError, match="defenders must be between"):
            FormationShape(defenders=6, midfielders=2, forwards=2)

    def test_create_with_too_few_midfielders_raises_error(self):
        """미드필더가 너무 적을 때 에러"""
        with pytest.raises(ValueError, match="midfielders must be between"):
            FormationShape(defenders=4, midfielders=1, forwards=2)

    def test_create_with_too_many_midfielders_raises_error(self):
        """미드필더가 너무 많을 때 에러"""
        with pytest.raises(ValueError, match="midfielders must be between"):
            FormationShape(defenders=3, midfielders=6, forwards=1)

    def test_create_with_too_few_forwards_raises_error(self):
        """공격수가 너무 적을 때 에러"""
        with pytest.raises(ValueError, match="forwards must be between"):
            FormationShape(defenders=5, midfielders=5, forwards=0)

    def test_create_with_too_many_forwards_raises_error(self):
        """공격수가 너무 많을 때 에러"""
        with pytest.raises(ValueError, match="forwards must be between"):
            FormationShape(defenders=3, midfielders=3, forwards=4)

    def test_create_with_non_integer_raises_error(self):
        """정수가 아닌 값으로 생성 시 에러"""
        with pytest.raises(TypeError, match="must be int"):
            FormationShape(defenders=4.5, midfielders=3, forwards=3)


class TestFormationShapeFromString:
    """FormationShape.from_string() 테스트"""

    def test_from_string_basic_format(self):
        """기본 형식 (3개 파트)"""
        shape = FormationShape.from_string("4-3-3")
        assert shape.defenders == 4
        assert shape.midfielders == 3
        assert shape.forwards == 3

    def test_from_string_four_parts(self):
        """4개 파트 형식 (예: 4-2-3-1)"""
        shape = FormationShape.from_string("4-2-3-1")
        assert shape.defenders == 4
        assert shape.midfielders == 5  # 2 + 3
        assert shape.forwards == 1

    def test_from_string_five_parts_invalid(self):
        """5개 파트 형식 - 유효하지 않음 (미드필더 초과)"""
        # 3-4-1-1-1은 미드필더가 6명이 되어 MAX_MIDFIELDERS 5를 초과
        with pytest.raises(ValueError, match="Invalid formation shape"):
            FormationShape.from_string("3-4-1-1-1")

    def test_from_string_3_5_2(self):
        """3-5-2 포메이션"""
        shape = FormationShape.from_string("3-5-2")
        assert shape.defenders == 3
        assert shape.midfielders == 5
        assert shape.forwards == 2

    def test_from_string_5_3_2(self):
        """5-3-2 포메이션"""
        shape = FormationShape.from_string("5-3-2")
        assert shape.defenders == 5
        assert shape.midfielders == 3
        assert shape.forwards == 2

    def test_from_string_invalid_format_raises_error(self):
        """잘못된 형식 시 에러"""
        with pytest.raises(ValueError, match="Invalid formation shape"):
            FormationShape.from_string("4-3")  # 너무 짧음

    def test_from_string_with_letters_raises_error(self):
        """문자 포함 시 에러"""
        with pytest.raises(ValueError, match="Invalid formation shape"):
            FormationShape.from_string("4-three-3")


class TestFormationShapeStringConversion:
    """FormationShape 문자열 변환 테스트"""

    def test_to_string(self):
        """문자열로 변환"""
        shape = FormationShape(defenders=4, midfielders=4, forwards=2)
        assert shape.to_string() == "4-4-2"

    def test_str_representation(self):
        """__str__ 메서드"""
        shape = FormationShape(defenders=3, midfielders=5, forwards=2)
        assert str(shape) == "3-5-2"

    def test_repr_representation(self):
        """__repr__ 메서드"""
        shape = FormationShape(defenders=4, midfielders=3, forwards=3)
        repr_str = repr(shape)
        assert "FormationShape" in repr_str
        assert "defenders=4" in repr_str
        assert "midfielders=3" in repr_str
        assert "forwards=3" in repr_str


class TestFormationShapeStyle:
    """FormationShape 스타일 판단 테스트"""

    def test_is_defensive_4_4_2(self):
        """4-4-2는 수비형"""
        shape = FormationShape(defenders=4, midfielders=4, forwards=2)
        assert shape.is_defensive() is True
        assert shape.is_attacking() is False
        assert shape.is_balanced() is False

    def test_is_defensive_5_3_2(self):
        """5-3-2는 수비형"""
        shape = FormationShape(defenders=5, midfielders=3, forwards=2)
        assert shape.is_defensive() is True

    def test_is_attacking_4_3_3(self):
        """4-3-3은 공격형"""
        shape = FormationShape(defenders=4, midfielders=3, forwards=3)
        assert shape.is_attacking() is True
        assert shape.is_defensive() is False
        assert shape.is_balanced() is False

    def test_is_attacking_3_4_3(self):
        """3-4-3은 공격형"""
        shape = FormationShape(defenders=3, midfielders=4, forwards=3)
        assert shape.is_attacking() is True

    def test_is_balanced_3_5_2(self):
        """3-5-2는 균형형"""
        shape = FormationShape(defenders=3, midfielders=5, forwards=2)
        assert shape.is_balanced() is True
        assert shape.is_defensive() is False
        assert shape.is_attacking() is False

    def test_get_style_defensive(self):
        """수비형 스타일 반환"""
        shape = FormationShape(defenders=5, midfielders=4, forwards=1)
        assert shape.get_style() == "defensive"

    def test_get_style_attacking(self):
        """공격형 스타일 반환"""
        shape = FormationShape(defenders=3, midfielders=4, forwards=3)
        assert shape.get_style() == "attacking"

    def test_get_style_balanced(self):
        """균형형 스타일 반환"""
        shape = FormationShape(defenders=3, midfielders=5, forwards=2)
        assert shape.get_style() == "balanced"


class TestFormationShapeStrength:
    """FormationShape 강도 계산 테스트"""

    def test_defensive_strength(self):
        """수비 강도 계산"""
        shape = FormationShape(defenders=4, midfielders=3, forwards=3)
        strength = shape.defensive_strength()
        assert isinstance(strength, float)
        assert 0 <= strength <= 100

    def test_defensive_strength_5_3_2_higher_than_4_3_3(self):
        """5-3-2가 4-3-3보다 수비 강도 높음"""
        shape_532 = FormationShape(defenders=5, midfielders=3, forwards=2)
        shape_433 = FormationShape(defenders=4, midfielders=3, forwards=3)
        assert shape_532.defensive_strength() > shape_433.defensive_strength()

    def test_attacking_strength(self):
        """공격 강도 계산"""
        shape = FormationShape(defenders=4, midfielders=3, forwards=3)
        strength = shape.attacking_strength()
        assert isinstance(strength, float)
        assert 0 <= strength <= 100

    def test_attacking_strength_4_3_3_higher_than_5_3_2(self):
        """4-3-3이 5-3-2보다 공격 강도 높음"""
        shape_433 = FormationShape(defenders=4, midfielders=3, forwards=3)
        shape_532 = FormationShape(defenders=5, midfielders=3, forwards=2)
        assert shape_433.attacking_strength() > shape_532.attacking_strength()


class TestFormationShapeUtilities:
    """FormationShape 유틸리티 메서드 테스트"""

    def test_as_tuple(self):
        """튜플로 변환"""
        shape = FormationShape(defenders=4, midfielders=4, forwards=2)
        assert shape.as_tuple() == (4, 4, 2)


class TestFormationShapePresets:
    """FormationShape 프리셋 테스트"""

    def test_four_three_three_preset(self):
        """4-3-3 프리셋"""
        shape = FormationShape.FOUR_THREE_THREE()
        assert shape.defenders == 4
        assert shape.midfielders == 3
        assert shape.forwards == 3

    def test_four_four_two_preset(self):
        """4-4-2 프리셋"""
        shape = FormationShape.FOUR_FOUR_TWO()
        assert shape.defenders == 4
        assert shape.midfielders == 4
        assert shape.forwards == 2

    def test_four_two_three_one_preset(self):
        """4-2-3-1 프리셋"""
        shape = FormationShape.FOUR_TWO_THREE_ONE()
        assert shape.defenders == 4
        assert shape.midfielders == 5  # 2 + 3
        assert shape.forwards == 1

    def test_three_five_two_preset(self):
        """3-5-2 프리셋"""
        shape = FormationShape.THREE_FIVE_TWO()
        assert shape.defenders == 3
        assert shape.midfielders == 5
        assert shape.forwards == 2

    def test_five_three_two_preset(self):
        """5-3-2 프리셋"""
        shape = FormationShape.FIVE_THREE_TWO()
        assert shape.defenders == 5
        assert shape.midfielders == 3
        assert shape.forwards == 2

    def test_four_three_two_one_preset(self):
        """4-3-2-1 프리셋"""
        shape = FormationShape.FOUR_THREE_TWO_ONE()
        assert shape.defenders == 4
        assert shape.midfielders == 5  # 3 + 2
        assert shape.forwards == 1


class TestFormationShapeImmutability:
    """FormationShape 불변성 테스트"""

    def test_formation_shape_is_immutable(self):
        """값 변경 불가"""
        shape = FormationShape(defenders=4, midfielders=3, forwards=3)
        with pytest.raises(AttributeError):
            shape.defenders = 5
