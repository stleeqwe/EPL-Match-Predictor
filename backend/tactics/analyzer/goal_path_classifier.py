"""
득점 경로 분류기

골 데이터를 분석하여 득점 경로 자동 분류
"""

from typing import Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class GoalData:
    """골 데이터 구조"""
    buildup_passes: int  # 빌드업 패스 수
    buildup_duration: float  # 빌드업 시간 (초)
    x_start: float  # 빌드업 시작 x좌표 (0-105m)
    y_start: float  # 빌드업 시작 y좌표 (0-68m)
    x_shot: float  # 슈팅 위치 x좌표
    y_shot: float  # 슈팅 위치 y좌표
    assist_type: Optional[str] = None  # 'cross', 'through_ball', 'cutback', etc.
    set_piece: bool = False  # 세트피스 여부
    situation: Optional[str] = None  # 'corner', 'freekick', 'penalty'


class GoalPathClassifier:
    """
    골 데이터 자동 분류기

    12가지 득점 경로 분류:
    - buildup_gradual (빌드업 점진적)
    - buildup_medium (중속 전개)
    - counter_fast (고속 역습)
    - counter_normal (일반 역습)
    - central_penetration (중앙 침투)
    - wide_penetration (측면 침투)
    - cutback (컷백)
    - cross_finish (크로스→마무리)
    - halfspace (하프스페이스)
    - corner (코너킥)
    - freekick (프리킥)
    - penalty (페널티킥)
    """

    # 필드 구역 정의 (68m 폭 기준)
    CENTRAL_ZONE = (20, 48)  # 중앙 (20-48m)
    HALFSPACE_LEFT = (14, 27)  # 왼쪽 하프스페이스
    HALFSPACE_RIGHT = (41, 54)  # 오른쪽 하프스페이스
    WIDE_LEFT = (0, 20)  # 왼쪽 측면
    WIDE_RIGHT = (48, 68)  # 오른쪽 측면

    def classify_goal(self, goal_data: GoalData) -> Tuple[str, float]:
        """
        골 데이터를 받아 득점 경로 분류

        Args:
            goal_data: GoalData 인스턴스

        Returns:
            (primary_category, confidence)
            - primary_category: 분류된 득점 경로
            - confidence: 분류 확신도 (0.0-1.0)

        Example:
            >>> classifier = GoalPathClassifier()
            >>> goal = GoalData(
            ...     buildup_passes=2,
            ...     buildup_duration=3.5,
            ...     x_start=45,
            ...     y_start=34,
            ...     x_shot=92,
            ...     y_shot=38,
            ...     assist_type='through_ball'
            ... )
            >>> category, confidence = classifier.classify_goal(goal)
            >>> print(f"{category} (확신도: {confidence:.2f})")
            counter_normal (확신도: 0.88)
        """
        # 1단계: 세트피스 판별
        if goal_data.set_piece:
            return self._classify_setpiece(goal_data)

        # 2단계: 역습 판별 (빠른 전개)
        if goal_data.buildup_duration < 5.0:
            return self._classify_counter(goal_data)

        # 3단계: 공간 기반 판별
        return self._classify_spatial(goal_data)

    def _classify_setpiece(self, data: GoalData) -> Tuple[str, float]:
        """세트피스 분류"""
        if data.situation == 'corner':
            return ('corner', 0.98)
        elif data.situation == 'freekick':
            return ('freekick', 0.98)
        elif data.situation == 'penalty':
            return ('penalty', 0.99)
        else:
            # 상황 정보 없으면 위치로 추정
            if data.x_start < 20:  # 자진영에서 시작
                return ('freekick', 0.85)
            else:
                return ('corner', 0.85)

    def _classify_counter(self, data: GoalData) -> Tuple[str, float]:
        """역습 분류"""
        if data.buildup_duration < 3.0:
            # 0-5초 고속 역습
            confidence = 0.95 if data.buildup_duration < 2.0 else 0.90
            return ('counter_fast', confidence)
        else:
            # 3-5초 일반 역습
            return ('counter_normal', 0.88)

    def _classify_spatial(self, data: GoalData) -> Tuple[str, float]:
        """공간 기반 분류 (점진적 빌드업)"""
        y_shot = data.y_shot

        # 컷백 판별 (박스 가장자리에서 중앙으로 패스)
        if data.assist_type == 'cutback':
            return ('cutback', 0.92)

        # 크로스 판별
        if data.assist_type == 'cross':
            return ('cross_finish', 0.90)

        # 슈팅 위치 기반 분류
        if self._is_in_zone(y_shot, self.CENTRAL_ZONE):
            # 중앙 구역
            if data.buildup_passes >= 5:
                return ('buildup_gradual', 0.88)
            elif data.buildup_passes >= 3:
                return ('buildup_medium', 0.85)
            else:
                return ('central_penetration', 0.85)

        elif self._is_in_zone(y_shot, self.HALFSPACE_LEFT) or self._is_in_zone(y_shot, self.HALFSPACE_RIGHT):
            # 하프스페이스
            return ('halfspace', 0.82)

        else:
            # 측면 구역
            if data.buildup_passes >= 5:
                return ('buildup_gradual', 0.85)
            else:
                return ('wide_penetration', 0.82)

    def _is_in_zone(self, y_coord: float, zone: Tuple[float, float]) -> bool:
        """좌표가 특정 구역에 속하는지 확인"""
        return zone[0] <= y_coord <= zone[1]

    def classify_batch(self, goals: list) -> Dict[str, int]:
        """
        다수의 골 데이터를 일괄 분류하고 통계 반환

        Args:
            goals: GoalData 리스트

        Returns:
            {득점_경로: 골_수}

        Example:
            >>> goals = [goal1, goal2, goal3, ...]
            >>> stats = classifier.classify_batch(goals)
            >>> print(stats)
            {
                'central_penetration': 45,
                'wide_penetration': 32,
                'counter_fast': 8,
                ...
            }
        """
        statistics = {}

        for goal in goals:
            category, _ = self.classify_goal(goal)

            if category not in statistics:
                statistics[category] = 0

            statistics[category] += 1

        return statistics

    def get_frequency_distribution(self, goals: list) -> Dict[str, float]:
        """
        득점 경로별 빈도 분포

        Args:
            goals: GoalData 리스트

        Returns:
            {득점_경로: 빈도} (합계 1.0)
        """
        stats = self.classify_batch(goals)
        total = sum(stats.values())

        if total == 0:
            return {}

        return {
            category: count / total
            for category, count in stats.items()
        }


# 사용 예시
if __name__ == "__main__":
    classifier = GoalPathClassifier()

    # 예시 골 데이터
    print("=== 골 분류 예시 ===\n")

    # 1. 고속 역습골
    goal1 = GoalData(
        buildup_passes=2,
        buildup_duration=2.5,
        x_start=42,
        y_start=34,
        x_shot=94,
        y_shot=38,
        assist_type='through_ball'
    )
    category1, conf1 = classifier.classify_goal(goal1)
    print(f"1. 고속 역습: {category1} (확신도: {conf1:.2f})")

    # 2. 중앙 침투골
    goal2 = GoalData(
        buildup_passes=3,
        buildup_duration=6.0,
        x_start=55,
        y_start=30,
        x_shot=88,
        y_shot=35,
        assist_type='through_ball'
    )
    category2, conf2 = classifier.classify_goal(goal2)
    print(f"2. 중앙 침투: {category2} (확신도: {conf2:.2f})")

    # 3. 컷백골
    goal3 = GoalData(
        buildup_passes=4,
        buildup_duration=8.0,
        x_start=50,
        y_start=12,
        x_shot=85,
        y_shot=34,
        assist_type='cutback'
    )
    category3, conf3 = classifier.classify_goal(goal3)
    print(f"3. 컷백: {category3} (확신도: {conf3:.2f})")

    # 4. 크로스→마무리
    goal4 = GoalData(
        buildup_passes=5,
        buildup_duration=10.0,
        x_start=45,
        y_start=8,
        x_shot=90,
        y_shot=32,
        assist_type='cross'
    )
    category4, conf4 = classifier.classify_goal(goal4)
    print(f"4. 크로스: {category4} (확신도: {conf4:.2f})")

    # 5. 코너킥
    goal5 = GoalData(
        buildup_passes=1,
        buildup_duration=5.0,
        x_start=105,
        y_start=0,
        x_shot=88,
        y_shot=30,
        set_piece=True,
        situation='corner'
    )
    category5, conf5 = classifier.classify_goal(goal5)
    print(f"5. 코너킥: {category5} (확신도: {conf5:.2f})")

    # 6. 점진적 빌드업
    goal6 = GoalData(
        buildup_passes=8,
        buildup_duration=15.0,
        x_start=25,
        y_start=34,
        x_shot=92,
        y_shot=36,
        assist_type='through_ball'
    )
    category6, conf6 = classifier.classify_goal(goal6)
    print(f"6. 점진적 빌드업: {category6} (확신도: {conf6:.2f})")

    # 일괄 분류 예시
    print("\n=== 일괄 분류 통계 ===")
    all_goals = [goal1, goal2, goal3, goal4, goal5, goal6]
    stats = classifier.classify_batch(all_goals)
    print("득점 경로별 골 수:")
    for category, count in stats.items():
        print(f"  {category}: {count}골")

    freq_dist = classifier.get_frequency_distribution(all_goals)
    print("\n빈도 분포:")
    for category, freq in freq_dist.items():
        print(f"  {category}: {freq*100:.1f}%")
