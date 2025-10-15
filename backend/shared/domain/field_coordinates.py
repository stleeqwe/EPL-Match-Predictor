"""
Field Coordinates - Shared Value Object

모든 세그먼트에서 사용하는 필드 좌표 표준
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class FieldCoordinates:
    """
    필드 좌표 (표준 105m × 68m 필드 기준)

    좌표계:
    - X축: -52.5 ~ +52.5 (길이 105m)
    - Y축: -34.0 ~ +34.0 (폭 68m)
    - 원점: 필드 중앙

    불변 객체 (immutable)
    """
    x: float
    y: float

    def __post_init__(self):
        """좌표 유효성 검증"""
        if not (-52.5 <= self.x <= 52.5):
            raise ValueError(
                f"X coordinate must be between -52.5 and 52.5, got {self.x}"
            )
        if not (-34.0 <= self.y <= 34.0):
            raise ValueError(
                f"Y coordinate must be between -34.0 and 34.0, got {self.y}"
            )

    def distance_to(self, other: 'FieldCoordinates') -> float:
        """다른 좌표까지의 거리 (미터)"""
        import math
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)

    def is_in_defensive_half(self, attacking_direction: str = 'right') -> bool:
        """수비 진영에 있는지 확인"""
        if attacking_direction == 'right':
            return self.x < 0
        else:
            return self.x > 0

    def is_in_penalty_box(self, defending_goal: str = 'left') -> bool:
        """페널티 박스 안에 있는지 확인"""
        if defending_goal == 'left':
            # 왼쪽 골 기준 페널티 박스
            return -52.5 <= self.x <= -35.5 and -20.16 <= self.y <= 20.16
        else:
            # 오른쪽 골 기준 페널티 박스
            return 35.5 <= self.x <= 52.5 and -20.16 <= self.y <= 20.16

    def __str__(self) -> str:
        return f"({self.x:.1f}, {self.y:.1f})"
