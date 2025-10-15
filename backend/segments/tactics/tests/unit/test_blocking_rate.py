"""
Unit Tests for BlockingRate Value Object
"""

import pytest
import sys
from pathlib import Path

# Add domain path
domain_path = Path(__file__).parent.parent.parent / "domain"
sys.path.insert(0, str(domain_path))

from value_objects.blocking_rate import BlockingRate


class TestBlockingRateCreation:
    """BlockingRate 생성 테스트"""

    def test_create_valid_blocking_rate(self):
        """유효한 차단률 생성"""
        rate = BlockingRate(70.0)
        assert rate.value == 70.0

    def test_create_blocking_rate_with_integer(self):
        """정수로 차단률 생성"""
        rate = BlockingRate(75)
        assert rate.value == 75

    def test_create_blocking_rate_at_boundaries(self):
        """경계값 테스트"""
        min_rate = BlockingRate(0.0)
        max_rate = BlockingRate(100.0)
        assert min_rate.value == 0.0
        assert max_rate.value == 100.0

    def test_create_blocking_rate_with_negative_value_raises_error(self):
        """음수 차단률 생성 시 에러"""
        with pytest.raises(ValueError, match="must be between 0 and 100"):
            BlockingRate(-10.0)

    def test_create_blocking_rate_above_100_raises_error(self):
        """100 초과 차단률 생성 시 에러"""
        with pytest.raises(ValueError, match="must be between 0 and 100"):
            BlockingRate(150.0)

    def test_create_blocking_rate_with_non_numeric_raises_error(self):
        """비숫자 타입으로 생성 시 에러"""
        with pytest.raises(TypeError, match="must be numeric"):
            BlockingRate("70")


class TestBlockingRateOperations:
    """BlockingRate 연산 테스트"""

    def test_apply_coefficient(self):
        """계수 적용"""
        rate = BlockingRate(70.0)
        adjusted = rate.apply_coefficient(1.2)
        assert adjusted.value == 84.0

    def test_apply_coefficient_capped_at_100(self):
        """계수 적용 후 100으로 제한"""
        rate = BlockingRate(90.0)
        adjusted = rate.apply_coefficient(1.5)
        assert adjusted.value == 100.0

    def test_apply_coefficient_floored_at_0(self):
        """계수 적용 후 0으로 제한"""
        rate = BlockingRate(50.0)
        adjusted = rate.apply_coefficient(0.0)
        assert adjusted.value == 0.0

    def test_increase_by(self):
        """차단률 증가"""
        rate = BlockingRate(60.0)
        increased = rate.increase_by(15.0)
        assert increased.value == 75.0

    def test_increase_by_capped_at_100(self):
        """증가 후 100으로 제한"""
        rate = BlockingRate(95.0)
        increased = rate.increase_by(10.0)
        assert increased.value == 100.0

    def test_decrease_by(self):
        """차단률 감소"""
        rate = BlockingRate(80.0)
        decreased = rate.decrease_by(20.0)
        assert decreased.value == 60.0

    def test_decrease_by_floored_at_0(self):
        """감소 후 0으로 제한"""
        rate = BlockingRate(10.0)
        decreased = rate.decrease_by(20.0)
        assert decreased.value == 0.0


class TestBlockingRateConversions:
    """BlockingRate 변환 테스트"""

    def test_as_probability(self):
        """확률로 변환"""
        rate = BlockingRate(70.0)
        assert rate.as_probability() == 0.7

    def test_float_conversion(self):
        """float 타입으로 변환"""
        rate = BlockingRate(85.5)
        assert float(rate) == 85.5

    def test_int_conversion(self):
        """int 타입으로 변환"""
        rate = BlockingRate(75.8)
        assert int(rate) == 75

    def test_str_representation(self):
        """문자열 표현"""
        rate = BlockingRate(68.3)
        assert str(rate) == "68.3%"

    def test_repr_representation(self):
        """개발자용 표현"""
        rate = BlockingRate(72.0)
        assert repr(rate) == "BlockingRate(72.0)"


class TestBlockingRateComparison:
    """BlockingRate 비교 테스트"""

    def test_less_than(self):
        """작음 비교"""
        rate1 = BlockingRate(60.0)
        rate2 = BlockingRate(70.0)
        assert rate1 < rate2

    def test_less_than_with_number(self):
        """숫자와 작음 비교"""
        rate = BlockingRate(50.0)
        assert rate < 60.0

    def test_less_than_or_equal(self):
        """작거나 같음 비교"""
        rate1 = BlockingRate(70.0)
        rate2 = BlockingRate(70.0)
        assert rate1 <= rate2

    def test_greater_than(self):
        """큼 비교"""
        rate1 = BlockingRate(80.0)
        rate2 = BlockingRate(70.0)
        assert rate1 > rate2

    def test_greater_than_or_equal(self):
        """크거나 같음 비교"""
        rate1 = BlockingRate(75.0)
        rate2 = BlockingRate(75.0)
        assert rate1 >= rate2


class TestBlockingRateImmutability:
    """BlockingRate 불변성 테스트"""

    def test_blocking_rate_is_immutable(self):
        """값 변경 불가"""
        rate = BlockingRate(70.0)
        with pytest.raises(AttributeError):
            rate.value = 80.0

    def test_operations_return_new_instance(self):
        """연산은 새 인스턴스 반환"""
        rate = BlockingRate(70.0)
        adjusted = rate.apply_coefficient(1.2)
        assert rate.value == 70.0  # 원본 유지
        assert adjusted.value == 84.0  # 새 인스턴스
        assert rate is not adjusted
