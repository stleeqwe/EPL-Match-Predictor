"""
효과성 계산기

포메이션별 차단률 계산 및 전술 효과성 분석
"""

from typing import Dict, List, Optional, Tuple
import sys
from pathlib import Path

# tactics 모듈 import를 위한 경로 추가
current_dir = Path(__file__).parent.parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from core.formations import FormationSystem


class EffectivenessCalculator:
    """
    전술 효과성 계산기

    기능:
    1. 포메이션별 득점 경로 차단률 계산
    2. 선수 능력 계수 적용
    3. 상황별 보정 계수 적용
    4. 최종 차단률 예측
    """

    def __init__(self):
        """초기화"""
        self.formation_system = FormationSystem()

    def calculate_blocking_rate(
        self,
        formation: str,
        goal_category: str,
        team_ability_coef: float = 1.0,
        fatigue_coef: float = 1.0,
        psychology_coef: float = 1.0,
        weather_coef: float = 1.0,
        situation_coef: float = 1.0
    ) -> Dict[str, any]:
        """
        최종 차단률 계산

        공식:
        실제 차단률 = 기본 차단률 × 선수 능력 계수 × 피로도 계수
                      × 심리 계수 × 기상 계수 × 상황 계수

        Args:
            formation: 포메이션 이름 (예: "4-3-3")
            goal_category: 득점 경로 (예: "central_penetration")
            team_ability_coef: 팀 능력 계수 (0.80-1.20, 기본 1.0)
            fatigue_coef: 피로도 계수 (0.80-1.00, 기본 1.0)
            psychology_coef: 심리 계수 (0.88-1.05, 기본 1.0)
            weather_coef: 기상 계수 (0.90-1.00, 기본 1.0)
            situation_coef: 상황 계수 (0.85-1.05, 기본 1.0)

        Returns:
            {
                'predicted_blocking_rate': float (0-100),
                'base_rate': float,
                'combined_coefficient': float,
                'components': dict
            }

        Example:
            >>> calculator = EffectivenessCalculator()
            >>> result = calculator.calculate_blocking_rate(
            ...     formation="4-3-3",
            ...     goal_category="central_penetration",
            ...     team_ability_coef=1.12,  # 맨시티급
            ...     fatigue_coef=0.95
            ... )
            >>> print(f"차단률: {result['predicted_blocking_rate']:.1f}%")
            차단률: 91.1%
        """
        # 1. 기본 차단률
        base_rate = self.formation_system.get_blocking_rate(formation, goal_category)

        if base_rate is None:
            return {
                'error': f"Formation '{formation}' or goal_category '{goal_category}' not found"
            }

        # 2. 통합 계수
        combined_coef = (
            team_ability_coef *
            fatigue_coef *
            psychology_coef *
            weather_coef *
            situation_coef
        )

        # 3. 최종 차단률
        predicted_rate = base_rate * combined_coef

        # 4. 0-100 범위로 제한
        predicted_rate = max(0, min(100, predicted_rate))

        return {
            'predicted_blocking_rate': round(predicted_rate, 2),
            'base_rate': base_rate,
            'combined_coefficient': round(combined_coef, 4),
            'components': {
                'team_ability': team_ability_coef,
                'fatigue': fatigue_coef,
                'psychology': psychology_coef,
                'weather': weather_coef,
                'situation': situation_coef
            },
            'formation': formation,
            'goal_category': goal_category
        }

    def calculate_team_defensive_score(
        self,
        formation: str,
        team_ability_coef: float = 1.0,
        goal_category_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, any]:
        """
        팀의 종합 수비 점수 계산

        Args:
            formation: 포메이션
            team_ability_coef: 팀 능력 계수
            goal_category_weights: 득점 경로별 가중치 (없으면 EPL 빈도 사용)

        Returns:
            {
                'overall_defensive_score': float (0-100),
                'by_category': dict,
                'formation': str,
                'team_ability': float
            }
        """
        # 기본 가중치: EPL 빈도
        if goal_category_weights is None:
            goal_category_weights = {}
            for category in self.formation_system.list_goal_categories():
                cat_info = self.formation_system.get_goal_category_info(category)
                goal_category_weights[category] = cat_info['epl_frequency']

        # 각 득점 경로별 차단률 계산
        category_scores = {}
        weighted_sum = 0
        total_weight = sum(goal_category_weights.values())

        for category, weight in goal_category_weights.items():
            result = self.calculate_blocking_rate(
                formation=formation,
                goal_category=category,
                team_ability_coef=team_ability_coef
            )

            if 'error' not in result:
                blocking_rate = result['predicted_blocking_rate']
                category_scores[category] = blocking_rate
                weighted_sum += blocking_rate * (weight / total_weight)

        overall_score = weighted_sum

        return {
            'overall_defensive_score': round(overall_score, 2),
            'by_category': category_scores,
            'formation': formation,
            'team_ability': team_ability_coef,
            'rating': self._get_rating(overall_score)
        }

    def _get_rating(self, score: float) -> str:
        """점수에 따른 등급"""
        if score >= 90:
            return "Exceptional"
        elif score >= 85:
            return "Excellent"
        elif score >= 80:
            return "Very Good"
        elif score >= 75:
            return "Good"
        elif score >= 70:
            return "Average"
        else:
            return "Below Average"

    def compare_formations_for_opponent(
        self,
        opponent_attacking_style: Dict[str, float],
        team_ability_coef: float = 1.0
    ) -> List[Dict]:
        """
        상대의 공격 스타일에 대한 최적 포메이션 추천

        Args:
            opponent_attacking_style: {득점 경로: 빈도} 딕셔너리
            team_ability_coef: 우리 팀 능력 계수

        Returns:
            포메이션 순위 리스트 (차단률 높은 순)

        Example:
            >>> calculator = EffectivenessCalculator()
            >>> opponent_style = {
            ...     'central_penetration': 0.35,
            ...     'wide_penetration': 0.30,
            ...     'cutback': 0.20,
            ...     'counter_fast': 0.15
            ... }
            >>> recommendations = calculator.compare_formations_for_opponent(
            ...     opponent_style,
            ...     team_ability_coef=1.05
            ... )
            >>> for idx, rec in enumerate(recommendations[:3]):
            ...     print(f"{idx+1}. {rec['formation']}: {rec['overall_score']:.1f}%")
        """
        formations = self.formation_system.list_formations()
        results = []

        for formation in formations:
            score_result = self.calculate_team_defensive_score(
                formation=formation,
                team_ability_coef=team_ability_coef,
                goal_category_weights=opponent_attacking_style
            )

            formation_data = self.formation_system.get_formation(formation)

            results.append({
                'formation': formation,
                'formation_name': formation_data['name_kr'],
                'overall_score': score_result['overall_defensive_score'],
                'by_category': score_result['by_category'],
                'rating': score_result['rating'],
                'base_defensive_rating': formation_data['overall_defensive_rating']
            })

        # 점수 순으로 정렬
        results.sort(key=lambda x: x['overall_score'], reverse=True)

        return results

    def calculate_matchup_advantage(
        self,
        home_formation: str,
        away_formation: str,
        home_ability: float = 1.0,
        away_ability: float = 1.0
    ) -> Dict[str, any]:
        """
        두 팀의 전술 매칭 분석

        Args:
            home_formation: 홈팀 포메이션
            away_formation: 원정팀 포메이션
            home_ability: 홈팀 능력 계수
            away_ability: 원정팀 능력 계수

        Returns:
            {
                'home_defensive_score': float,
                'away_defensive_score': float,
                'advantage': str ('home', 'away', 'balanced'),
                'difference': float,
                'analysis': dict
            }
        """
        # 홈팀 수비력
        home_defense = self.calculate_team_defensive_score(
            formation=home_formation,
            team_ability_coef=home_ability
        )

        # 원정팀 수비력
        away_defense = self.calculate_team_defensive_score(
            formation=away_formation,
            team_ability_coef=away_ability
        )

        home_score = home_defense['overall_defensive_score']
        away_score = away_defense['overall_defensive_score']
        difference = home_score - away_score

        if difference > 5:
            advantage = 'home'
        elif difference < -5:
            advantage = 'away'
        else:
            advantage = 'balanced'

        # 세부 분석
        analysis = {}
        for category in self.formation_system.list_goal_categories():
            home_rate = home_defense['by_category'].get(category, 0)
            away_rate = away_defense['by_category'].get(category, 0)

            cat_info = self.formation_system.get_goal_category_info(category)

            analysis[category] = {
                'name': cat_info['name'],
                'home_blocking': home_rate,
                'away_blocking': away_rate,
                'difference': home_rate - away_rate,
                'epl_frequency': cat_info['epl_frequency']
            }

        return {
            'home_defensive_score': home_score,
            'away_defensive_score': away_score,
            'advantage': advantage,
            'difference': round(difference, 2),
            'analysis_by_category': analysis,
            'home_formation': home_formation,
            'away_formation': away_formation
        }


# 사용 예시
if __name__ == "__main__":
    calculator = EffectivenessCalculator()

    # 1. 기본 차단률 계산
    print("=== 4-3-3 중앙 침투 차단률 (맨시티급) ===")
    result = calculator.calculate_blocking_rate(
        formation="4-3-3",
        goal_category="central_penetration",
        team_ability_coef=1.12,  # 맨시티급
        fatigue_coef=0.95,  # 중3일
        psychology_coef=1.00
    )
    print(f"예측 차단률: {result['predicted_blocking_rate']}%")
    print(f"기본 차단률: {result['base_rate']}%")
    print(f"통합 계수: {result['combined_coefficient']}")

    # 2. 팀 종합 수비 점수
    print("\n=== 4-2-3-1 종합 수비 점수 ===")
    defense_score = calculator.calculate_team_defensive_score(
        formation="4-2-3-1",
        team_ability_coef=1.05
    )
    print(f"종합 수비 점수: {defense_score['overall_defensive_score']:.1f}/100")
    print(f"등급: {defense_score['rating']}")
    print("\n득점 경로별 차단률:")
    for category, rate in list(defense_score['by_category'].items())[:5]:
        cat_info = calculator.formation_system.get_goal_category_info(category)
        print(f"  {cat_info['name']}: {rate:.1f}%")

    # 3. 상대 스타일에 맞는 포메이션 추천
    print("\n=== 상대 공격 스타일 대응 포메이션 추천 ===")
    opponent_style = {
        'central_penetration': 0.40,  # 중앙 집중 공격
        'cutback': 0.25,
        'wide_penetration': 0.20,
        'counter_fast': 0.15
    }
    recommendations = calculator.compare_formations_for_opponent(
        opponent_style,
        team_ability_coef=1.00
    )
    print("Top 3 추천:")
    for idx, rec in enumerate(recommendations[:3]):
        print(f"{idx+1}. {rec['formation_name']}: {rec['overall_score']:.1f}% ({rec['rating']})")

    # 4. 매칭 분석
    print("\n=== 맨시티 (4-3-3) vs 리버풀 (4-3-3) 매칭 ===")
    matchup = calculator.calculate_matchup_advantage(
        home_formation="4-3-3",
        away_formation="4-3-3",
        home_ability=1.12,  # 맨시티
        away_ability=1.10   # 리버풀
    )
    print(f"홈팀 수비력: {matchup['home_defensive_score']:.1f}")
    print(f"원정팀 수비력: {matchup['away_defensive_score']:.1f}")
    print(f"우위: {matchup['advantage']} (+{matchup['difference']:.1f})")
