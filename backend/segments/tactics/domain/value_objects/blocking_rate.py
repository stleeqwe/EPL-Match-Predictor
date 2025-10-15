"""
Blocking Rate Value Object

차단률을 표현하는 불변 값 객체
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class BlockingRate:
    """
    차단률 값 객체

    0-100 범위의 차단률을 표현합니다.
    불변 객체로, 생성 후 값을 변경할 수 없습니다.

    Attributes:
        value: 차단률 (0-100)
    """
    value: float

    def __post_init__(self):
        """값 검증"""
        if not isinstance(self.value, (int, float)):
            raise TypeError(f"BlockingRate value must be numeric, got {type(self.value)}")

        if not 0 <= self.value <= 100:
            raise ValueError(f"BlockingRate must be between 0 and 100, got {self.value}")

    def apply_coefficient(self, coefficient: float) -> 'BlockingRate':
        """
        계수를 적용한 새로운 차단률 반환

        Args:
            coefficient: 적용할 계수

        Returns:
            새로운 BlockingRate 객체

        Examples:
            >>> rate = BlockingRate(70.0)
            >>> adjusted = rate.apply_coefficient(1.2)
            >>> adjusted.value
            84.0
        """
        new_value = self.value * coefficient
        # 0-100 범위로 제한
        new_value = max(0.0, min(100.0, new_value))
        return BlockingRate(new_value)

    def increase_by(self, amount: float) -> 'BlockingRate':
        """
        차단률을 증가시킨 새로운 객체 반환

        Args:
            amount: 증가량

        Returns:
            새로운 BlockingRate 객체
        """
        new_value = min(100.0, self.value + amount)
        return BlockingRate(new_value)

    def decrease_by(self, amount: float) -> 'BlockingRate':
        """
        차단률을 감소시킨 새로운 객체 반환

        Args:
            amount: 감소량

        Returns:
            새로운 BlockingRate 객체
        """
        new_value = max(0.0, self.value - amount)
        return BlockingRate(new_value)

    def as_probability(self) -> float:
        """
        확률로 변환 (0-1 범위)

        Returns:
            확률 값 (0.0 ~ 1.0)
        """
        return self.value / 100.0

    def __float__(self) -> float:
        """float 타입으로 변환"""
        return self.value

    def __int__(self) -> int:
        """int 타입으로 변환"""
        return int(self.value)

    def __str__(self) -> str:
        """문자열 표현"""
        return f"{self.value:.1f}%"

    def __repr__(self) -> str:
        """개발자용 표현"""
        return f"BlockingRate({self.value})"

    # 비교 연산자
    def __lt__(self, other) -> bool:
        if isinstance(other, BlockingRate):
            return self.value < other.value
        return self.value < other

    def __le__(self, other) -> bool:
        if isinstance(other, BlockingRate):
            return self.value <= other.value
        return self.value <= other

    def __gt__(self, other) -> bool:
        if isinstance(other, BlockingRate):
            return self.value > other.value
        return self.value > other

    def __ge__(self, other) -> bool:
        if isinstance(other, BlockingRate):
            return self.value >= other.value
        return self.value >= other
