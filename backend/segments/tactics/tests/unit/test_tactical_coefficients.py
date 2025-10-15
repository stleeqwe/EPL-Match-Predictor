"""
Unit Tests for TacticalCoefficients Value Object
"""

import pytest
import sys
from pathlib import Path

# Add domain path
domain_path = Path(__file__).parent.parent.parent / "domain"
sys.path.insert(0, str(domain_path))

from value_objects.tactical_coefficients import TacticalCoefficients


class TestTacticalCoefficientsCreation:
    """TacticalCoefficients 생성 테스트"""

    def test_create_default_coefficients(self):
        """기본 계수 생성"""
        coef = TacticalCoefficients()
        assert coef.team_ability == 1.0
        assert coef.fatigue == 1.0
        assert coef.psychology == 1.0
        assert coef.weather == 1.0
        assert coef.situation == 1.0

    def test_create_custom_coefficients(self):
        """커스텀 계수 생성"""
        coef = TacticalCoefficients(
            team_ability=1.2,
            fatigue=0.8,
            psychology=1.1,
            weather=0.95,
            situation=0.9
        )
        assert coef.team_ability == 1.2
        assert coef.fatigue == 0.8
        assert coef.psychology == 1.1
        assert coef.weather == 0.95
        assert coef.situation == 0.9

    def test_create_with_team_ability_out_of_range_raises_error(self):
        """팀 능력 계수 범위 초과 시 에러"""
        with pytest.raises(ValueError, match="team_ability must be between"):
            TacticalCoefficients(team_ability=2.0)

        with pytest.raises(ValueError, match="team_ability must be between"):
            TacticalCoefficients(team_ability=0.3)

    def test_create_with_fatigue_out_of_range_raises_error(self):
        """피로도 계수 범위 초과 시 에러"""
        with pytest.raises(ValueError, match="fatigue must be between"):
            TacticalCoefficients(fatigue=1.5)

        with pytest.raises(ValueError, match="fatigue must be between"):
            TacticalCoefficients(fatigue=0.3)

    def test_create_with_psychology_out_of_range_raises_error(self):
        """심리 계수 범위 초과 시 에러"""
        with pytest.raises(ValueError, match="psychology must be between"):
            TacticalCoefficients(psychology=1.5)

        with pytest.raises(ValueError, match="psychology must be between"):
            TacticalCoefficients(psychology=0.5)

    def test_create_with_non_numeric_raises_error(self):
        """비숫자 타입으로 생성 시 에러"""
        with pytest.raises(TypeError, match="must be numeric"):
            TacticalCoefficients(team_ability="1.2")


class TestTacticalCoefficientsCombined:
    """TacticalCoefficients combined() 메서드 테스트"""

    def test_combined_with_default_values(self):
        """기본값의 통합 계수"""
        coef = TacticalCoefficients()
        assert coef.combined() == 1.0

    def test_combined_with_custom_values(self):
        """커스텀 값의 통합 계수"""
        coef = TacticalCoefficients(
            team_ability=1.2,
            fatigue=0.9,
            psychology=1.1,
            weather=0.95,
            situation=1.0
        )
        expected = 1.2 * 0.9 * 1.1 * 0.95 * 1.0
        assert abs(coef.combined() - expected) < 0.0001

    def test_combined_rounds_to_4_decimals(self):
        """통합 계수는 소수점 4자리까지"""
        coef = TacticalCoefficients(
            team_ability=1.234567,
            fatigue=0.987654
        )
        result = coef.combined()
        assert len(str(result).split('.')[-1]) <= 4


class TestTacticalCoefficientsImmutability:
    """TacticalCoefficients 불변성 테스트"""

    def test_coefficients_are_immutable(self):
        """계수 값 변경 불가"""
        coef = TacticalCoefficients(team_ability=1.2)
        with pytest.raises(AttributeError):
            coef.team_ability = 1.3

    def test_with_methods_return_new_instance(self):
        """with 메서드는 새 인스턴스 반환"""
        original = TacticalCoefficients(team_ability=1.0)
        modified = original.with_team_ability(1.2)

        assert original.team_ability == 1.0  # 원본 유지
        assert modified.team_ability == 1.2  # 새 인스턴스
        assert original is not modified


class TestTacticalCoefficientsWithMethods:
    """TacticalCoefficients with_* 메서드 테스트"""

    def test_with_team_ability(self):
        """팀 능력 계수 변경"""
        coef = TacticalCoefficients()
        new_coef = coef.with_team_ability(1.3)
        assert new_coef.team_ability == 1.3
        assert new_coef.fatigue == 1.0

    def test_with_fatigue(self):
        """피로도 계수 변경"""
        coef = TacticalCoefficients()
        new_coef = coef.with_fatigue(0.8)
        assert new_coef.fatigue == 0.8
        assert new_coef.team_ability == 1.0

    def test_with_psychology(self):
        """심리 계수 변경"""
        coef = TacticalCoefficients()
        new_coef = coef.with_psychology(1.1)
        assert new_coef.psychology == 1.1

    def test_with_weather(self):
        """날씨 계수 변경"""
        coef = TacticalCoefficients()
        new_coef = coef.with_weather(0.95)
        assert new_coef.weather == 0.95

    def test_with_situation(self):
        """상황 계수 변경"""
        coef = TacticalCoefficients()
        new_coef = coef.with_situation(0.9)
        assert new_coef.situation == 0.9

    def test_chaining_with_methods(self):
        """with 메서드 체이닝"""
        coef = TacticalCoefficients()
        new_coef = (coef
                    .with_team_ability(1.2)
                    .with_fatigue(0.9)
                    .with_psychology(1.1))

        assert new_coef.team_ability == 1.2
        assert new_coef.fatigue == 0.9
        assert new_coef.psychology == 1.1


class TestTacticalCoefficientsPresets:
    """TacticalCoefficients 프리셋 테스트"""

    def test_default_preset(self):
        """기본 프리셋"""
        coef = TacticalCoefficients.default()
        assert coef.team_ability == 1.0
        assert coef.fatigue == 1.0
        assert coef.psychology == 1.0
        assert coef.weather == 1.0
        assert coef.situation == 1.0

    def test_for_strong_team_preset(self):
        """강팀 프리셋"""
        coef = TacticalCoefficients.for_strong_team()
        assert coef.team_ability == 1.3
        assert coef.psychology == 1.1

    def test_for_strong_team_with_custom_ability(self):
        """강팀 프리셋 커스텀 능력"""
        coef = TacticalCoefficients.for_strong_team(ability_rating=1.4)
        assert coef.team_ability == 1.4

    def test_for_strong_team_caps_at_max(self):
        """강팀 프리셋 최대값 제한"""
        coef = TacticalCoefficients.for_strong_team(ability_rating=2.0)
        assert coef.team_ability == 1.5  # capped at max

    def test_for_weak_team_preset(self):
        """약팀 프리셋"""
        coef = TacticalCoefficients.for_weak_team()
        assert coef.team_ability == 0.7
        assert coef.psychology == 0.9

    def test_for_weak_team_with_custom_ability(self):
        """약팀 프리셋 커스텀 능력"""
        coef = TacticalCoefficients.for_weak_team(ability_rating=0.6)
        assert coef.team_ability == 0.6

    def test_for_tired_team_preset(self):
        """피로한 팀 프리셋"""
        coef = TacticalCoefficients.for_tired_team()
        assert coef.fatigue == 0.7
        assert coef.psychology == 0.9

    def test_for_tired_team_with_custom_fatigue(self):
        """피로한 팀 프리셋 커스텀 피로도"""
        coef = TacticalCoefficients.for_tired_team(fatigue_level=0.6)
        assert coef.fatigue == 0.6


class TestTacticalCoefficientsStringRepresentation:
    """TacticalCoefficients 문자열 표현 테스트"""

    def test_str_representation(self):
        """문자열 표현"""
        coef = TacticalCoefficients(team_ability=1.2, fatigue=0.9)
        str_repr = str(coef)
        assert "TacticalCoefficients" in str_repr
        assert "combined" in str_repr
        assert "ability=1.20" in str_repr
        assert "fatigue=0.90" in str_repr

    def test_repr_representation(self):
        """개발자용 표현"""
        coef = TacticalCoefficients(team_ability=1.2)
        repr_str = repr(coef)
        assert "TacticalCoefficients(" in repr_str
        assert "team_ability=1.2" in repr_str
