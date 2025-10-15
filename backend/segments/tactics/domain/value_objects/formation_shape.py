"""
Formation Shape Value Object

포메이션의 형태/구조를 표현하는 불변 값 객체
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class FormationShape:
    """
    포메이션 형태 값 객체

    수비수-미드필더-공격수의 배치를 표현합니다.
    예: 4-3-3, 4-2-3-1, 3-5-2 등

    Attributes:
        defenders: 수비수 수 (3-5)
        midfielders: 미드필더 수 (2-5)
        forwards: 공격수 수 (1-3)
    """
    defenders: int
    midfielders: int
    forwards: int

    # 유효 범위
    MIN_DEFENDERS = 3
    MAX_DEFENDERS = 5
    MIN_MIDFIELDERS = 2
    MAX_MIDFIELDERS = 5
    MIN_FORWARDS = 1
    MAX_FORWARDS = 3

    def __post_init__(self):
        """값 검증"""
        # 타입 검증
        if not isinstance(self.defenders, int):
            raise TypeError(f"defenders must be int, got {type(self.defenders)}")
        if not isinstance(self.midfielders, int):
            raise TypeError(f"midfielders must be int, got {type(self.midfielders)}")
        if not isinstance(self.forwards, int):
            raise TypeError(f"forwards must be int, got {type(self.forwards)}")

        # 범위 검증
        if not self.MIN_DEFENDERS <= self.defenders <= self.MAX_DEFENDERS:
            raise ValueError(
                f"defenders must be between {self.MIN_DEFENDERS} and {self.MAX_DEFENDERS}, "
                f"got {self.defenders}"
            )
        if not self.MIN_MIDFIELDERS <= self.midfielders <= self.MAX_MIDFIELDERS:
            raise ValueError(
                f"midfielders must be between {self.MIN_MIDFIELDERS} and {self.MAX_MIDFIELDERS}, "
                f"got {self.midfielders}"
            )
        if not self.MIN_FORWARDS <= self.forwards <= self.MAX_FORWARDS:
            raise ValueError(
                f"forwards must be between {self.MIN_FORWARDS} and {self.MAX_FORWARDS}, "
                f"got {self.forwards}"
            )

        # 총 필드 플레이어 수 검증 (GK 제외 10명)
        total = self.defenders + self.midfielders + self.forwards
        if total != 10:
            raise ValueError(
                f"Total field players must be 10 (excluding GK), got {total} "
                f"({self.defenders}+{self.midfielders}+{self.forwards})"
            )

    @classmethod
    def from_string(cls, shape_str: str) -> 'FormationShape':
        """
        문자열로부터 FormationShape 생성

        Args:
            shape_str: 포메이션 문자열 (예: "4-3-3", "4-2-3-1")

        Returns:
            FormationShape 객체

        Raises:
            ValueError: 잘못된 형식

        Examples:
            >>> FormationShape.from_string("4-3-3")
            FormationShape(defenders=4, midfielders=3, forwards=3)
            >>> FormationShape.from_string("4-2-3-1")
            FormationShape(defenders=4, midfielders=5, forwards=1)
        """
        parts = shape_str.split('-')

        if len(parts) < 3:
            raise ValueError(f"Invalid formation shape: {shape_str}")

        try:
            # 기본적으로 3개 파트 (수-미-공)
            if len(parts) == 3:
                defenders = int(parts[0])
                midfielders = int(parts[1])
                forwards = int(parts[2])
            # 4개 파트인 경우 (예: 4-2-3-1)
            elif len(parts) == 4:
                defenders = int(parts[0])
                midfielders = int(parts[1]) + int(parts[2])  # 미드필더 합산
                forwards = int(parts[3])
            # 5개 파트인 경우 (예: 3-4-1-2)
            elif len(parts) == 5:
                defenders = int(parts[0])
                midfielders = int(parts[1]) + int(parts[2]) + int(parts[3])
                forwards = int(parts[4])
            else:
                raise ValueError(f"Too many parts in formation shape: {shape_str}")

            return cls(defenders=defenders, midfielders=midfielders, forwards=forwards)

        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid formation shape: {shape_str}") from e

    def to_string(self) -> str:
        """
        표준 문자열 형식으로 변환

        Returns:
            "수-미-공" 형식 문자열
        """
        return f"{self.defenders}-{self.midfielders}-{self.forwards}"

    def is_defensive(self) -> bool:
        """
        수비형 포메이션 여부

        수비수가 4명 이상이고 공격수가 2명 이하면 수비형으로 판단
        """
        return self.defenders >= 4 and self.forwards <= 2

    def is_attacking(self) -> bool:
        """
        공격형 포메이션 여부

        공격수가 3명이고 수비수가 4명 이하면 공격형으로 판단
        """
        return self.forwards >= 3 and self.defenders <= 4

    def is_balanced(self) -> bool:
        """균형형 포메이션 여부"""
        return not self.is_defensive() and not self.is_attacking()

    def get_style(self) -> str:
        """
        포메이션 스타일 반환

        Returns:
            "defensive", "attacking", "balanced" 중 하나
        """
        if self.is_defensive():
            return "defensive"
        elif self.is_attacking():
            return "attacking"
        else:
            return "balanced"

    def defensive_strength(self) -> float:
        """
        수비 강도 점수

        수비수와 수비형 미드필더 비중으로 계산
        """
        return (self.defenders * 2 + self.midfielders) / 13 * 100

    def attacking_strength(self) -> float:
        """
        공격 강도 점수

        공격수와 공격형 미드필더 비중으로 계산
        """
        return (self.forwards * 2 + self.midfielders) / 13 * 100

    def as_tuple(self) -> Tuple[int, int, int]:
        """
        튜플로 변환

        Returns:
            (defenders, midfielders, forwards)
        """
        return (self.defenders, self.midfielders, self.forwards)

    def __str__(self) -> str:
        """문자열 표현"""
        return self.to_string()

    def __repr__(self) -> str:
        """개발자용 표현"""
        return (
            f"FormationShape(defenders={self.defenders}, "
            f"midfielders={self.midfielders}, forwards={self.forwards})"
        )

    # 일반적인 포메이션 프리셋
    @classmethod
    def FOUR_THREE_THREE(cls) -> 'FormationShape':
        """4-3-3 포메이션"""
        return cls(defenders=4, midfielders=3, forwards=3)

    @classmethod
    def FOUR_FOUR_TWO(cls) -> 'FormationShape':
        """4-4-2 포메이션"""
        return cls(defenders=4, midfielders=4, forwards=2)

    @classmethod
    def FOUR_TWO_THREE_ONE(cls) -> 'FormationShape':
        """4-2-3-1 포메이션 (미드필더 5명으로 계산)"""
        return cls(defenders=4, midfielders=5, forwards=1)

    @classmethod
    def THREE_FIVE_TWO(cls) -> 'FormationShape':
        """3-5-2 포메이션"""
        return cls(defenders=3, midfielders=5, forwards=2)

    @classmethod
    def FIVE_THREE_TWO(cls) -> 'FormationShape':
        """5-3-2 포메이션"""
        return cls(defenders=5, midfielders=3, forwards=2)

    @classmethod
    def FOUR_THREE_TWO_ONE(cls) -> 'FormationShape':
        """4-3-2-1 포메이션 (미드필더 5명으로 계산)"""
        return cls(defenders=4, midfielders=5, forwards=1)
