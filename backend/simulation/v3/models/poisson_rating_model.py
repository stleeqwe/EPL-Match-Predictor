"""
Poisson-Rating Hybrid Model

사용자 도메인 데이터 기반 Expected Goals 계산:
1. Attack/Defense Ratings (derived_strengths)
2. Formation Compatibility (formation_tactics)
3. Poisson Distribution으로 스코어 확률 도출

NO Templates, NO EPL baseline forcing
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from scipy.stats import poisson
import logging

from ai.enriched_data_models import EnrichedTeamInput, FormationTactics

logger = logging.getLogger(__name__)


@dataclass
class PoissonRatingResult:
    """Poisson-Rating 모델 출력"""
    lambda_home: float                              # Expected goals (home)
    lambda_away: float                              # Expected goals (away)
    probabilities: Dict[str, float]                 # {home_win, draw, away_win}
    most_likely_scores: List[Tuple[str, float]]     # [("1-1", 0.18), ("1-2", 0.16), ...]
    score_probabilities: Dict[Tuple[int, int], float]  # {(1, 2): 0.16, ...}
    formation_compatibility: float                  # 포메이션 궁합도


class PoissonRatingModel:
    """
    Poisson-Rating Hybrid Model

    사용자 도메인 데이터만 사용:
    - derived_strengths.attack_strength (0-100)
    - derived_strengths.defense_strength (0-100)
    - formation_tactics (style, pressing)

    출력:
    - Expected goals (Poisson λ)
    - Win/Draw/Loss probabilities
    - Score probabilities

    정규화 방식:
    - 70 = EPL 중위권 팀 (리그 평균)
    - 100 = 최고 수준
    - 50 = 하위권
    """

    # EPL 평균 골 (실제 통계 기반, 참고만 - 강제 아님)
    EPL_AVG_HOME_GOALS = 1.5      # 홈팀 평균 득점
    EPL_AVG_AWAY_GOALS = 1.2      # 원정팀 평균 득점

    # 리그 평균 레이팅 (0-100 스케일에서 중위권)
    LEAGUE_AVG_RATING = 70.0

    def __init__(self):
        """Initialize Poisson-Rating Model"""
        pass

    def calculate(self,
                  home_team: EnrichedTeamInput,
                  away_team: EnrichedTeamInput) -> PoissonRatingResult:
        """
        Poisson-Rating 모델 계산

        Args:
            home_team: 홈팀 데이터 (사용자 입력)
            away_team: 원정팀 데이터 (사용자 입력)

        Returns:
            PoissonRatingResult with probabilities
        """
        logger.info(f"[Poisson-Rating] Calculating for {home_team.name} vs {away_team.name}")

        # 1. Attack/Defense Ratings 추출
        home_attack = home_team.derived_strengths.attack_strength
        home_defense = home_team.derived_strengths.defense_strength
        away_attack = away_team.derived_strengths.attack_strength
        away_defense = away_team.derived_strengths.defense_strength

        logger.debug(f"[Poisson-Rating] {home_team.name}: Attack {home_attack:.1f}, Defense {home_defense:.1f}")
        logger.debug(f"[Poisson-Rating] {away_team.name}: Attack {away_attack:.1f}, Defense {away_defense:.1f}")

        # 2. Formation Compatibility 계산
        formation_factor = calculate_formation_compatibility(
            home_tactics=home_team.formation_tactics,
            away_tactics=away_team.formation_tactics
        )

        logger.debug(f"[Poisson-Rating] Formation compatibility: {formation_factor:.3f}")

        # 3. Expected Goals (Poisson λ) 계산
        lambda_home = self._calculate_expected_goals(
            attack=home_attack,
            opponent_defense=away_defense,
            formation_factor=formation_factor,
            is_home=True
        )

        lambda_away = self._calculate_expected_goals(
            attack=away_attack,
            opponent_defense=home_defense,
            formation_factor=formation_factor,
            is_home=False
        )

        logger.info(f"[Poisson-Rating] Expected goals: Home {lambda_home:.2f}, Away {lambda_away:.2f}")

        # 4. Poisson Distribution으로 스코어 확률 계산
        score_probs = self._calculate_score_probabilities(lambda_home, lambda_away)

        # 5. Win/Draw/Loss 확률 도출
        probabilities = self._calculate_outcome_probabilities(score_probs)

        # 6. Most likely scores
        most_likely_scores = self._get_most_likely_scores(score_probs, top_n=5)

        logger.info(f"[Poisson-Rating] Probabilities: Home {probabilities['home_win']:.1%}, "
                   f"Draw {probabilities['draw']:.1%}, Away {probabilities['away_win']:.1%}")

        return PoissonRatingResult(
            lambda_home=lambda_home,
            lambda_away=lambda_away,
            probabilities=probabilities,
            most_likely_scores=most_likely_scores,
            score_probabilities=score_probs,
            formation_compatibility=formation_factor
        )

    def _calculate_expected_goals(self,
                                   attack: float,
                                   opponent_defense: float,
                                   formation_factor: float,
                                   is_home: bool) -> float:
        """
        Expected Goals (Poisson λ) 계산

        표준 Poisson 모델 기반:
        λ = (공격력/평균) * (평균/상대수비) * 포메이션궁합 * 리그평균골

        정규화:
        - 70 = 리그 평균 팀
        - attack/70 = 공격 상대 강도
        - 70/defense = 상대 수비 약점

        Args:
            attack: 공격력 (0-100, 70 = 평균)
            opponent_defense: 상대 수비력 (0-100, 70 = 평균)
            formation_factor: 포메이션 궁합도
            is_home: 홈팀 여부

        Returns:
            Expected goals (λ)
        """
        # 공격 상대 강도 (70 = 1.0)
        attack_strength = attack / self.LEAGUE_AVG_RATING

        # 상대 수비 약점 (수비가 높을수록 약점 작음)
        # 70/defense: defense=70이면 1.0, defense=100이면 0.7, defense=50이면 1.4
        defense_weakness = self.LEAGUE_AVG_RATING / max(opponent_defense, 1.0)

        # Base expected goals (리그 평균)
        base_goals = self.EPL_AVG_HOME_GOALS if is_home else self.EPL_AVG_AWAY_GOALS

        # λ 계산
        lambda_value = attack_strength * defense_weakness * formation_factor * base_goals

        # 최소값 보장 (너무 낮은 xG 방지)
        return max(0.1, lambda_value)

    def _calculate_score_probabilities(self,
                                        lambda_home: float,
                                        lambda_away: float,
                                        max_goals: int = 6) -> Dict[Tuple[int, int], float]:
        """
        Poisson 분포로 스코어별 확률 계산

        P(home_goals, away_goals) = Poisson(home_goals | λ_home) * Poisson(away_goals | λ_away)

        Args:
            lambda_home: Home team expected goals
            lambda_away: Away team expected goals
            max_goals: 계산할 최대 골 수 (0-max_goals)

        Returns:
            {(home_goals, away_goals): probability}
        """
        score_probs = {}

        for home_goals in range(max_goals + 1):
            for away_goals in range(max_goals + 1):
                prob = poisson.pmf(home_goals, lambda_home) * poisson.pmf(away_goals, lambda_away)
                score_probs[(home_goals, away_goals)] = prob

        return score_probs

    def _calculate_outcome_probabilities(self,
                                          score_probs: Dict[Tuple[int, int], float]) -> Dict[str, float]:
        """
        Win/Draw/Loss 확률 계산

        Args:
            score_probs: {(home_goals, away_goals): probability}

        Returns:
            {home_win, draw, away_win}
        """
        home_win = 0.0
        draw = 0.0
        away_win = 0.0

        for (h, a), prob in score_probs.items():
            if h > a:
                home_win += prob
            elif h == a:
                draw += prob
            else:  # h < a
                away_win += prob

        # 정규화 (합이 1.0이 되도록)
        total = home_win + draw + away_win
        if total > 0:
            home_win /= total
            draw /= total
            away_win /= total

        return {
            'home_win': home_win,
            'draw': draw,
            'away_win': away_win
        }

    def _get_most_likely_scores(self,
                                 score_probs: Dict[Tuple[int, int], float],
                                 top_n: int = 5) -> List[Tuple[str, float]]:
        """
        가장 가능성 높은 스코어 추출

        Args:
            score_probs: {(home_goals, away_goals): probability}
            top_n: 상위 N개

        Returns:
            [("1-1", 0.18), ("1-2", 0.16), ...]
        """
        # 확률 높은 순으로 정렬
        sorted_scores = sorted(score_probs.items(), key=lambda x: x[1], reverse=True)

        # 상위 N개 추출
        top_scores = []
        for (h, a), prob in sorted_scores[:top_n]:
            score_str = f"{h}-{a}"
            top_scores.append((score_str, prob))

        return top_scores


def calculate_formation_compatibility(home_tactics: Optional[FormationTactics],
                                       away_tactics: Optional[FormationTactics]) -> float:
    """
    포메이션 전술 궁합도 계산

    전술 스타일 조합에 따라 경기 스타일이 달라짐:
    - 공격적 vs 공격적 → 고득점 경기 예상 (1.15)
    - 공격적 vs 수비적 → 전술 충돌 (0.9)
    - 수비적 vs 수비적 → 저득점 경기 (0.85)
    - 균형 vs 균형 → 중립 (1.0)

    압박 스타일도 고려:
    - 높은 압박 vs 높은 압박 → 혼란스러운 경기 (1.1)
    - 낮은 압박 vs 낮은 압박 → 느린 경기 (0.95)

    Args:
        home_tactics: 홈팀 전술 정보
        away_tactics: 원정팀 전술 정보

    Returns:
        궁합도 (0.8 ~ 1.2)
    """
    if not home_tactics or not away_tactics:
        # 전술 정보 없으면 중립
        return 1.0

    # 1. 전술 스타일 점수화
    style_score = _calculate_style_compatibility(
        home_tactics.style,
        away_tactics.style
    )

    # 2. 압박 스타일 점수화
    pressing_score = _calculate_pressing_compatibility(
        home_tactics.pressing,
        away_tactics.pressing
    )

    # 3. 가중 평균 (스타일 70%, 압박 30%)
    compatibility = style_score * 0.7 + pressing_score * 0.3

    # 범위 제한 (0.8 ~ 1.2)
    return max(0.8, min(1.2, compatibility))


def _calculate_style_compatibility(home_style: str, away_style: str) -> float:
    """
    전술 스타일 궁합도

    Args:
        home_style: "공격적", "수비적", "균형잡힌" 등
        away_style: "공격적", "수비적", "균형잡힌" 등

    Returns:
        궁합도 (0.85 ~ 1.15)
    """
    # 스타일 분류
    aggressive_styles = ["공격적", "attacking", "aggressive", "offensive"]
    defensive_styles = ["수비적", "defensive", "defensive-minded", "cautious"]
    balanced_styles = ["균형잡힌", "balanced", "neutral"]

    home_is_aggressive = any(s in home_style.lower() for s in aggressive_styles)
    home_is_defensive = any(s in home_style.lower() for s in defensive_styles)

    away_is_aggressive = any(s in away_style.lower() for s in aggressive_styles)
    away_is_defensive = any(s in away_style.lower() for s in defensive_styles)

    # 조합별 궁합도
    if home_is_aggressive and away_is_aggressive:
        # 공격적 vs 공격적 → 고득점
        return 1.15
    elif home_is_defensive and away_is_defensive:
        # 수비적 vs 수비적 → 저득점
        return 0.85
    elif (home_is_aggressive and away_is_defensive) or (home_is_defensive and away_is_aggressive):
        # 공격적 vs 수비적 → 전술 충돌
        return 0.9
    else:
        # 균형 또는 기타 조합 → 중립
        return 1.0


def _calculate_pressing_compatibility(home_pressing: str, away_pressing: str) -> float:
    """
    압박 스타일 궁합도

    Args:
        home_pressing: "높은 라인에서 적극적 압박" 등
        away_pressing: "중간 라인 압박" 등

    Returns:
        궁합도 (0.95 ~ 1.1)
    """
    # 압박 강도 분류
    high_press_keywords = ["높은", "적극적", "high", "aggressive", "intense"]
    low_press_keywords = ["낮은", "소극적", "low", "passive", "deep"]

    home_high_press = any(k in home_pressing.lower() for k in high_press_keywords)
    away_high_press = any(k in away_pressing.lower() for k in high_press_keywords)

    home_low_press = any(k in home_pressing.lower() for k in low_press_keywords)
    away_low_press = any(k in away_pressing.lower() for k in low_press_keywords)

    # 조합별 궁합도
    if home_high_press and away_high_press:
        # 높은 압박 vs 높은 압박 → 혼란스러운 경기
        return 1.1
    elif home_low_press and away_low_press:
        # 낮은 압박 vs 낮은 압박 → 느린 경기
        return 0.95
    else:
        # 기타 조합 → 중립
        return 1.0


if __name__ == "__main__":
    # 간단한 테스트
    logging.basicConfig(level=logging.DEBUG)

    from services.enriched_data_loader import EnrichedDomainDataLoader

    loader = EnrichedDomainDataLoader()
    arsenal = loader.load_team_data("Arsenal")
    liverpool = loader.load_team_data("Liverpool")

    model = PoissonRatingModel()
    result = model.calculate(arsenal, liverpool)

    print("\n" + "="*80)
    print("Poisson-Rating Model Test")
    print("="*80)
    print(f"Expected Goals: Home {result.lambda_home:.2f}, Away {result.lambda_away:.2f}")
    print(f"Probabilities:")
    print(f"  Home win: {result.probabilities['home_win']:.1%}")
    print(f"  Draw: {result.probabilities['draw']:.1%}")
    print(f"  Away win: {result.probabilities['away_win']:.1%}")
    print(f"\nMost likely scores:")
    for score, prob in result.most_likely_scores:
        print(f"  {score}: {prob:.1%}")
    print(f"\nFormation compatibility: {result.formation_compatibility:.3f}")
    print()
