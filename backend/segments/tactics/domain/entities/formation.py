"""
Formation Entity

포메이션은 전술 시스템의 핵심 엔티티입니다.
팀의 선수 배치와 각 골 카테고리별 차단률을 정의합니다.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
import sys
from pathlib import Path

# Shared Kernel import - add backend to path to import shared module
backend_path = Path(__file__).parent.parent.parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import shared.types.identifiers as identifiers
from shared.domain.field_coordinates import FieldCoordinates
from shared.domain.position_type import PositionType

FormationId = identifiers.FormationId
PositionId = identifiers.PositionId


@dataclass
class Formation:
    """
    포메이션 엔티티

    Attributes:
        id: 포메이션 고유 식별자 (예: "4-3-3", "4-2-3-1")
        name: 표시용 이름
        blocking_rates: 골 카테고리별 기본 차단률 (0-100)
        player_positions: 포지션별 필드 좌표
        description: 포메이션 설명
    """
    id: FormationId
    name: str
    blocking_rates: Dict[str, float]
    player_positions: Dict[PositionType, FieldCoordinates] = field(default_factory=dict)
    description: Optional[str] = None

    # 표준 골 카테고리 (12가지)
    GOAL_CATEGORIES = [
        "central_penetration",
        "wide_penetration",
        "cutback",
        "cross",
        "throughball",
        "longball",
        "corner",
        "freekick",
        "counterattack",
        "setpiece",
        "individual",
        "error"
    ]

    def __post_init__(self):
        """엔티티 검증"""
        self._validate_blocking_rates()
        self._validate_player_positions()

    def _validate_blocking_rates(self):
        """차단률 검증"""
        # 모든 필수 카테고리가 있는지 확인
        missing_categories = set(self.GOAL_CATEGORIES) - set(self.blocking_rates.keys())
        if missing_categories:
            raise ValueError(f"Missing blocking rates for categories: {missing_categories}")

        # 각 차단률이 0-100 범위인지 확인
        for category, rate in self.blocking_rates.items():
            if not 0 <= rate <= 100:
                raise ValueError(
                    f"Blocking rate for '{category}' must be between 0 and 100, got {rate}"
                )

    def _validate_player_positions(self):
        """선수 포지션 검증"""
        # GK는 필수
        if self.player_positions and PositionType.GK not in self.player_positions:
            raise ValueError("Formation must have a goalkeeper position")

    def get_blocking_rate(self, category: str) -> float:
        """
        특정 골 카테고리의 차단률 조회

        Args:
            category: 골 카테고리

        Returns:
            차단률 (0-100)

        Raises:
            KeyError: 존재하지 않는 카테고리
        """
        if category not in self.blocking_rates:
            raise KeyError(f"Unknown goal category: {category}")
        return self.blocking_rates[category]

    def calculate_overall_defensive_rating(self) -> float:
        """
        전체 수비력 평가 점수 계산

        주요 수비 카테고리에 가중치를 적용하여 계산:
        - central_penetration: 30%
        - wide_penetration: 25%
        - throughball: 20%
        - cross: 15%
        - counterattack: 10%

        Returns:
            수비력 점수 (0-100)
        """
        weights = {
            "central_penetration": 0.30,
            "wide_penetration": 0.25,
            "throughball": 0.20,
            "cross": 0.15,
            "counterattack": 0.10,
        }

        total_score = 0.0
        for category, weight in weights.items():
            total_score += self.blocking_rates.get(category, 0) * weight

        return round(total_score, 2)

    def calculate_overall_attacking_vulnerability(self) -> float:
        """
        공격 취약성 평가 (역수비력)

        Returns:
            공격 취약성 점수 (0-100, 높을수록 취약)
        """
        defensive_rating = self.calculate_overall_defensive_rating()
        return round(100 - defensive_rating, 2)

    def get_position_coordinate(self, position: PositionType) -> Optional[FieldCoordinates]:
        """
        특정 포지션의 필드 좌표 조회

        Args:
            position: 포지션 타입

        Returns:
            필드 좌표 (없으면 None)
        """
        return self.player_positions.get(position)

    def is_defensive_formation(self) -> bool:
        """
        수비형 포메이션 여부 판단

        중앙 침투와 측면 침투 차단률이 모두 70% 이상이면 수비형으로 판단
        """
        central = self.blocking_rates.get("central_penetration", 0)
        wide = self.blocking_rates.get("wide_penetration", 0)
        return central >= 70 and wide >= 70

    def is_attacking_formation(self) -> bool:
        """
        공격형 포메이션 여부 판단

        중앙 침투와 측면 침투 차단률이 모두 60% 미만이면 공격형으로 판단
        """
        central = self.blocking_rates.get("central_penetration", 0)
        wide = self.blocking_rates.get("wide_penetration", 0)
        return central < 60 and wide < 60

    def is_balanced_formation(self) -> bool:
        """균형형 포메이션 여부"""
        return not self.is_defensive_formation() and not self.is_attacking_formation()

    def get_formation_style(self) -> str:
        """
        포메이션 스타일 판단

        Returns:
            "defensive", "attacking", "balanced" 중 하나
        """
        if self.is_defensive_formation():
            return "defensive"
        elif self.is_attacking_formation():
            return "attacking"
        else:
            return "balanced"

    def __eq__(self, other) -> bool:
        """엔티티 동등성 비교 (ID 기반)"""
        if not isinstance(other, Formation):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """엔티티 해싱 (ID 기반)"""
        return hash(self.id)

    def __repr__(self) -> str:
        """문자열 표현"""
        style = self.get_formation_style()
        rating = self.calculate_overall_defensive_rating()
        return f"Formation(id='{self.id}', name='{self.name}', style='{style}', defensive_rating={rating})"
