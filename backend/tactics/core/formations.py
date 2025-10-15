"""
포메이션 시스템

6가지 주요 포메이션 관리 및 로드:
- 4-3-3 (하이 프레싱)
- 4-2-3-1 (미드 블록)
- 4-4-2 (로우 블록)
- 3-5-2 (윙백 시스템)
- 4-1-4-1 (미드프레스 덫)
- 3-4-3 (전방 압박)
"""

import json
import os
from typing import Dict, List, Optional
from pathlib import Path


class FormationSystem:
    """포메이션 시스템 관리"""

    def __init__(self, data_path: Optional[str] = None):
        """
        Args:
            data_path: formations.json 파일 경로 (기본값: tactics/data/formations.json)
        """
        if data_path is None:
            # 현재 파일 기준 상대 경로
            current_dir = Path(__file__).parent.parent
            data_path = current_dir / 'data' / 'formations.json'

        self.data_path = data_path
        self.formations = self._load_formations()
        self.goal_categories = self.formations.get('goal_categories', {})
        self.metadata = self.formations.get('metadata', {})

    def _load_formations(self) -> Dict:
        """formations.json 로드"""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"formations.json not found at {self.data_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in formations.json: {e}")

    def get_formation(self, formation_name: str) -> Optional[Dict]:
        """
        특정 포메이션 데이터 가져오기

        Args:
            formation_name: 포메이션 이름 (예: "4-3-3", "4-2-3-1")

        Returns:
            포메이션 데이터 딕셔너리

        Example:
            >>> fs = FormationSystem()
            >>> formation_433 = fs.get_formation("4-3-3")
            >>> print(formation_433['name'])
            "4-3-3 High Press"
        """
        return self.formations['formations'].get(formation_name)

    def list_formations(self) -> List[str]:
        """사용 가능한 포메이션 목록"""
        return list(self.formations['formations'].keys())

    def get_blocking_rate(self, formation_name: str, goal_category: str) -> Optional[float]:
        """
        특정 포메이션의 특정 득점 경로 차단률

        Args:
            formation_name: 포메이션 이름
            goal_category: 득점 경로 (예: "central_penetration")

        Returns:
            차단률 (0-100)

        Example:
            >>> fs = FormationSystem()
            >>> rate = fs.get_blocking_rate("4-3-3", "central_penetration")
            >>> print(f"차단률: {rate}%")
            차단률: 85.0%
        """
        formation = self.get_formation(formation_name)
        if not formation:
            return None

        return formation['blocking_rates'].get(goal_category)

    def get_formation_rating(self, formation_name: str) -> Optional[int]:
        """
        포메이션의 종합 수비 지수

        Args:
            formation_name: 포메이션 이름

        Returns:
            수비 지수 (0-100)
        """
        formation = self.get_formation(formation_name)
        if not formation:
            return None

        return formation.get('overall_defensive_rating')

    def get_formation_strengths(self, formation_name: str) -> List[str]:
        """포메이션 강점 리스트"""
        formation = self.get_formation(formation_name)
        if not formation:
            return []

        return formation.get('strengths', [])

    def get_formation_weaknesses(self, formation_name: str) -> List[str]:
        """포메이션 약점 리스트"""
        formation = self.get_formation(formation_name)
        if not formation:
            return []

        return formation.get('weaknesses', [])

    def get_position_importance(self, formation_name: str) -> Dict[str, float]:
        """
        포메이션에서 각 포지션의 중요도 (가중치)

        Args:
            formation_name: 포메이션 이름

        Returns:
            {포지션: 가중치} 딕셔너리 (합계 1.0)

        Example:
            >>> fs = FormationSystem()
            >>> weights = fs.get_position_importance("4-3-3")
            >>> print(weights['DM'])
            0.30  # DM이 30% 중요도
        """
        formation = self.get_formation(formation_name)
        if not formation:
            return {}

        return formation.get('key_positions', {})

    def get_default_tactics(self, formation_name: str) -> Dict[str, any]:
        """
        포메이션의 기본 전술 파라미터

        Returns:
            {
                'pressing_intensity': int (1-10),
                'defensive_line': int (1-10),
                'tempo': int (1-10),
                ...
            }
        """
        formation = self.get_formation(formation_name)
        if not formation:
            return {}

        return formation.get('default_tactics', {})

    def compare_formations(self, formation_a: str, formation_b: str,
                          goal_category: str) -> Dict[str, any]:
        """
        두 포메이션의 특정 득점 경로 차단률 비교

        Args:
            formation_a: 첫 번째 포메이션
            formation_b: 두 번째 포메이션
            goal_category: 득점 경로

        Returns:
            {
                'formation_a': str,
                'formation_b': str,
                'goal_category': str,
                'blocking_rate_a': float,
                'blocking_rate_b': float,
                'difference': float,
                'better': str
            }
        """
        rate_a = self.get_blocking_rate(formation_a, goal_category)
        rate_b = self.get_blocking_rate(formation_b, goal_category)

        if rate_a is None or rate_b is None:
            return {}

        difference = rate_a - rate_b
        better = formation_a if difference > 0 else formation_b

        return {
            'formation_a': formation_a,
            'formation_b': formation_b,
            'goal_category': goal_category,
            'blocking_rate_a': rate_a,
            'blocking_rate_b': rate_b,
            'difference': abs(difference),
            'better': better
        }

    def get_best_formation_for_category(self, goal_category: str) -> Dict[str, any]:
        """
        특정 득점 경로 차단에 가장 효과적인 포메이션

        Args:
            goal_category: 득점 경로

        Returns:
            {
                'formation': str,
                'blocking_rate': float,
                'name': str
            }
        """
        best_formation = None
        best_rate = 0

        for formation_name in self.list_formations():
            rate = self.get_blocking_rate(formation_name, goal_category)
            if rate and rate > best_rate:
                best_rate = rate
                best_formation = formation_name

        if not best_formation:
            return {}

        formation_data = self.get_formation(best_formation)

        return {
            'formation': best_formation,
            'blocking_rate': best_rate,
            'name': formation_data['name'],
            'name_kr': formation_data['name_kr']
        }

    def get_formation_matrix(self) -> Dict[str, Dict[str, float]]:
        """
        전체 포메이션 × 득점 경로 매트릭스

        Returns:
            {
                '4-3-3': {
                    'central_penetration': 85.0,
                    'wide_penetration': 78.0,
                    ...
                },
                ...
            }
        """
        matrix = {}

        for formation_name in self.list_formations():
            formation = self.get_formation(formation_name)
            matrix[formation_name] = formation['blocking_rates']

        return matrix

    def get_goal_category_info(self, category: str) -> Optional[Dict]:
        """
        득점 경로 정보

        Args:
            category: 득점 경로 (예: "central_penetration")

        Returns:
            {
                'name': str (한글),
                'name_en': str (영문),
                'description': str,
                'epl_frequency': float (EPL 발생 빈도)
            }
        """
        return self.goal_categories.get(category)

    def list_goal_categories(self) -> List[str]:
        """득점 경로 목록"""
        return list(self.goal_categories.keys())


# 사용 예시
if __name__ == "__main__":
    # 포메이션 시스템 초기화
    fs = FormationSystem()

    # 포메이션 목록
    print("=== 사용 가능한 포메이션 ===")
    for formation in fs.list_formations():
        rating = fs.get_formation_rating(formation)
        print(f"{formation}: 수비 지수 {rating}")

    print("\n=== 4-3-3 포메이션 상세 ===")
    formation_433 = fs.get_formation("4-3-3")
    print(f"이름: {formation_433['name_kr']}")
    print(f"철학: {formation_433['philosophy']}")
    print(f"수비 지수: {formation_433['overall_defensive_rating']}")

    print("\n강점:")
    for strength in formation_433['strengths']:
        print(f"  - {strength}")

    print("\n약점:")
    for weakness in formation_433['weaknesses']:
        print(f"  - {weakness}")

    print("\n=== 중앙 침투 차단 최적 포메이션 ===")
    best = fs.get_best_formation_for_category("central_penetration")
    print(f"{best['name_kr']}: {best['blocking_rate']}%")

    print("\n=== 4-3-3 vs 4-2-3-1 비교 (중앙 침투) ===")
    comparison = fs.compare_formations("4-3-3", "4-2-3-1", "central_penetration")
    print(f"4-3-3: {comparison['blocking_rate_a']}%")
    print(f"4-2-3-1: {comparison['blocking_rate_b']}%")
    print(f"우위: {comparison['better']} (+{comparison['difference']}%p)")
