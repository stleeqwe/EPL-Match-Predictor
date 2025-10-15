"""
Formation Repository Interface

포메이션 저장소에 대한 도메인 계약 정의
구현은 Infrastructure Layer에서 제공
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import sys
from pathlib import Path

# Shared Kernel import - add backend to path
backend_path = Path(__file__).parent.parent.parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

import shared.types.identifiers as identifiers
FormationId = identifiers.FormationId

# Domain Entity import
from ..entities.formation import Formation


class IFormationRepository(ABC):
    """
    포메이션 저장소 인터페이스

    도메인 레이어에서 정의하는 포트(Port)
    실제 구현은 Infrastructure 레이어에서 제공하는 어댑터(Adapter)
    """

    @abstractmethod
    def find_by_id(self, formation_id: FormationId) -> Optional[Formation]:
        """
        ID로 포메이션 조회

        Args:
            formation_id: 포메이션 ID

        Returns:
            Formation 객체 (없으면 None)
        """
        pass

    @abstractmethod
    def find_all(self) -> List[Formation]:
        """
        모든 포메이션 조회

        Returns:
            Formation 객체 리스트
        """
        pass

    @abstractmethod
    def save(self, formation: Formation) -> None:
        """
        포메이션 저장

        Args:
            formation: 저장할 Formation 객체

        Raises:
            RepositoryError: 저장 실패 시
        """
        pass

    @abstractmethod
    def delete(self, formation_id: FormationId) -> bool:
        """
        포메이션 삭제

        Args:
            formation_id: 삭제할 포메이션 ID

        Returns:
            삭제 성공 여부
        """
        pass

    @abstractmethod
    def exists(self, formation_id: FormationId) -> bool:
        """
        포메이션 존재 여부 확인

        Args:
            formation_id: 확인할 포메이션 ID

        Returns:
            존재 여부
        """
        pass

    @abstractmethod
    def find_by_style(self, style: str) -> List[Formation]:
        """
        스타일로 포메이션 검색

        Args:
            style: 포메이션 스타일 ("defensive", "attacking", "balanced")

        Returns:
            해당 스타일의 Formation 객체 리스트
        """
        pass

    @abstractmethod
    def find_by_defensive_rating_range(
        self, min_rating: float, max_rating: float
    ) -> List[Formation]:
        """
        수비력 범위로 포메이션 검색

        Args:
            min_rating: 최소 수비력 점수
            max_rating: 최대 수비력 점수

        Returns:
            해당 범위의 Formation 객체 리스트
        """
        pass


class ITacticalStyleRepository(ABC):
    """
    전술 스타일 저장소 인터페이스

    향후 확장을 위한 인터페이스
    """

    @abstractmethod
    def find_by_team_id(self, team_id: str) -> Optional[dict]:
        """
        팀 ID로 전술 스타일 조회

        Args:
            team_id: 팀 ID

        Returns:
            전술 스타일 정보 (없으면 None)
        """
        pass

    @abstractmethod
    def save_team_style(self, team_id: str, style_data: dict) -> None:
        """
        팀 전술 스타일 저장

        Args:
            team_id: 팀 ID
            style_data: 전술 스타일 데이터
        """
        pass
