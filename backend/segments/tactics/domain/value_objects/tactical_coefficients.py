"""
Tactical Coefficients Value Object

전술 계산에 사용되는 계수들을 표현하는 불변 값 객체
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TacticalCoefficients:
    """
    전술 계수 값 객체

    경기 상황에 따라 전술 효과에 영향을 주는 다양한 계수들을 표현합니다.

    Attributes:
        team_ability: 팀 능력 계수 (0.5 ~ 1.5, 기본 1.0)
        fatigue: 피로도 계수 (0.5 ~ 1.0, 기본 1.0)
        psychology: 심리 상태 계수 (0.8 ~ 1.2, 기본 1.0)
        weather: 날씨 영향 계수 (0.9 ~ 1.0, 기본 1.0)
        situation: 상황 계수 (0.8 ~ 1.2, 기본 1.0)
    """
    team_ability: float = 1.0
    fatigue: float = 1.0
    psychology: float = 1.0
    weather: float = 1.0
    situation: float = 1.0

    # 계수별 유효 범위
    TEAM_ABILITY_RANGE = (0.5, 1.5)
    FATIGUE_RANGE = (0.5, 1.0)
    PSYCHOLOGY_RANGE = (0.8, 1.2)
    WEATHER_RANGE = (0.9, 1.0)
    SITUATION_RANGE = (0.8, 1.2)

    def __post_init__(self):
        """값 검증"""
        self._validate_coefficient("team_ability", self.team_ability, self.TEAM_ABILITY_RANGE)
        self._validate_coefficient("fatigue", self.fatigue, self.FATIGUE_RANGE)
        self._validate_coefficient("psychology", self.psychology, self.PSYCHOLOGY_RANGE)
        self._validate_coefficient("weather", self.weather, self.WEATHER_RANGE)
        self._validate_coefficient("situation", self.situation, self.SITUATION_RANGE)

    def _validate_coefficient(self, name: str, value: float, valid_range: tuple):
        """계수 값 검증"""
        if not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be numeric, got {type(value)}")

        min_val, max_val = valid_range
        if not min_val <= value <= max_val:
            raise ValueError(
                f"{name} must be between {min_val} and {max_val}, got {value}"
            )

    def combined(self) -> float:
        """
        모든 계수를 곱한 통합 계수 계산

        Returns:
            통합 계수 (모든 계수의 곱)

        Examples:
            >>> coef = TacticalCoefficients(
            ...     team_ability=1.2,
            ...     fatigue=0.9,
            ...     psychology=1.1,
            ...     weather=0.95,
            ...     situation=1.0
            ... )
            >>> coef.combined()
            1.1286
        """
        return round(
            self.team_ability * self.fatigue * self.psychology * self.weather * self.situation,
            4
        )

    def with_team_ability(self, team_ability: float) -> 'TacticalCoefficients':
        """
        팀 능력 계수를 변경한 새로운 객체 반환

        Args:
            team_ability: 새로운 팀 능력 계수

        Returns:
            새로운 TacticalCoefficients 객체
        """
        return TacticalCoefficients(
            team_ability=team_ability,
            fatigue=self.fatigue,
            psychology=self.psychology,
            weather=self.weather,
            situation=self.situation,
        )

    def with_fatigue(self, fatigue: float) -> 'TacticalCoefficients':
        """
        피로도 계수를 변경한 새로운 객체 반환

        Args:
            fatigue: 새로운 피로도 계수

        Returns:
            새로운 TacticalCoefficients 객체
        """
        return TacticalCoefficients(
            team_ability=self.team_ability,
            fatigue=fatigue,
            psychology=self.psychology,
            weather=self.weather,
            situation=self.situation,
        )

    def with_psychology(self, psychology: float) -> 'TacticalCoefficients':
        """
        심리 상태 계수를 변경한 새로운 객체 반환

        Args:
            psychology: 새로운 심리 상태 계수

        Returns:
            새로운 TacticalCoefficients 객체
        """
        return TacticalCoefficients(
            team_ability=self.team_ability,
            fatigue=self.fatigue,
            psychology=psychology,
            weather=self.weather,
            situation=self.situation,
        )

    def with_weather(self, weather: float) -> 'TacticalCoefficients':
        """
        날씨 계수를 변경한 새로운 객체 반환

        Args:
            weather: 새로운 날씨 계수

        Returns:
            새로운 TacticalCoefficients 객체
        """
        return TacticalCoefficients(
            team_ability=self.team_ability,
            fatigue=self.fatigue,
            psychology=self.psychology,
            weather=weather,
            situation=self.situation,
        )

    def with_situation(self, situation: float) -> 'TacticalCoefficients':
        """
        상황 계수를 변경한 새로운 객체 반환

        Args:
            situation: 새로운 상황 계수

        Returns:
            새로운 TacticalCoefficients 객체
        """
        return TacticalCoefficients(
            team_ability=self.team_ability,
            fatigue=self.fatigue,
            psychology=self.psychology,
            weather=self.weather,
            situation=situation,
        )

    @classmethod
    def default(cls) -> 'TacticalCoefficients':
        """
        기본 계수 반환 (모든 계수 1.0)

        Returns:
            기본 TacticalCoefficients 객체
        """
        return cls()

    @classmethod
    def for_strong_team(cls, ability_rating: float = 1.3) -> 'TacticalCoefficients':
        """
        강팀용 계수 프리셋

        Args:
            ability_rating: 팀 능력 평가 (1.0 ~ 1.5)

        Returns:
            강팀용 TacticalCoefficients 객체
        """
        return cls(
            team_ability=min(1.5, max(1.0, ability_rating)),
            fatigue=1.0,
            psychology=1.1,
            weather=1.0,
            situation=1.0,
        )

    @classmethod
    def for_weak_team(cls, ability_rating: float = 0.7) -> 'TacticalCoefficients':
        """
        약팀용 계수 프리셋

        Args:
            ability_rating: 팀 능력 평가 (0.5 ~ 1.0)

        Returns:
            약팀용 TacticalCoefficients 객체
        """
        return cls(
            team_ability=min(1.0, max(0.5, ability_rating)),
            fatigue=1.0,
            psychology=0.9,
            weather=1.0,
            situation=1.0,
        )

    @classmethod
    def for_tired_team(cls, fatigue_level: float = 0.7) -> 'TacticalCoefficients':
        """
        피로한 팀용 계수 프리셋

        Args:
            fatigue_level: 피로도 (0.5 ~ 1.0, 낮을수록 피로함)

        Returns:
            피로한 팀용 TacticalCoefficients 객체
        """
        return cls(
            team_ability=1.0,
            fatigue=min(1.0, max(0.5, fatigue_level)),
            psychology=0.9,
            weather=1.0,
            situation=1.0,
        )

    def __str__(self) -> str:
        """문자열 표현"""
        return (
            f"TacticalCoefficients(combined={self.combined():.3f}, "
            f"ability={self.team_ability:.2f}, "
            f"fatigue={self.fatigue:.2f}, "
            f"psychology={self.psychology:.2f})"
        )

    def __repr__(self) -> str:
        """개발자용 표현"""
        return (
            f"TacticalCoefficients("
            f"team_ability={self.team_ability}, "
            f"fatigue={self.fatigue}, "
            f"psychology={self.psychology}, "
            f"weather={self.weather}, "
            f"situation={self.situation})"
        )
