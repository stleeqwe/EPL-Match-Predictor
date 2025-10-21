"""
Model Ensemble

네 가지 모델을 가중 평균으로 통합:
1. Poisson-Rating (0.3) - 통계적 신뢰성
2. Zone Dominance (0.2) - 전술적 분석 (구역 지배)
3. Key Player (0.2) - 개인 영향력
4. AI Tactical (0.3) - AI의 tactical reasoning (user commentary 반영)

100% 사용자 도메인 데이터 기반 + AI의 tactical intelligence
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from scipy.stats import poisson
import math
import logging

from ai.enriched_data_models import EnrichedTeamInput

# Import models (absolute for __main__ execution)
try:
    from .poisson_rating_model import PoissonRatingModel, PoissonRatingResult
    from .zone_dominance_calculator import ZoneDominanceCalculator, ZoneDominanceResult
    from .key_player_influence import KeyPlayerInfluenceCalculator, KeyPlayerInfluenceResult
    from .ai_tactical_model import AITacticalModel, AITacticalResult
except ImportError:
    from poisson_rating_model import PoissonRatingModel, PoissonRatingResult
    from zone_dominance_calculator import ZoneDominanceCalculator, ZoneDominanceResult
    from key_player_influence import KeyPlayerInfluenceCalculator, KeyPlayerInfluenceResult
    from ai_tactical_model import AITacticalModel, AITacticalResult

logger = logging.getLogger(__name__)


@dataclass
class EnsembleResult:
    """Ensemble 통합 결과"""
    # Ensemble probabilities
    ensemble_probabilities: Dict[str, float]        # {home_win, draw, away_win}

    # Expected goals (weighted average)
    expected_goals: Dict[str, float]                # {home, away}

    # Zone dominance summary
    zone_dominance_summary: Dict[str, any]

    # Key player impacts
    key_player_impacts: List[Dict[str, any]]

    # Tactical insights
    tactical_insights: Dict[str, str]

    # Individual model results (for transparency)
    poisson_result: PoissonRatingResult
    zone_result: ZoneDominanceResult
    player_result: KeyPlayerInfluenceResult
    ai_result: AITacticalResult

    # Model weights used
    weights: Dict[str, float]


class ModelEnsemble:
    """
    Model Ensemble: 네 가지 모델 통합 (수학 3개 + AI 1개)

    가중치:
    - Poisson: 0.3 (통계적 신뢰성)
    - Zone: 0.2 (전술적 분석, 구역 지배)
    - Player: 0.2 (개인 영향력)
    - AI Tactical: 0.3 (AI의 tactical reasoning, user commentary 반영)
    """

    # Model weights
    WEIGHTS = {
        'poisson': 0.3,
        'zone': 0.2,
        'player': 0.2,
        'ai_tactical': 0.3
    }

    def __init__(self):
        """Initialize Model Ensemble"""
        self.poisson_model = PoissonRatingModel()
        self.zone_calculator = ZoneDominanceCalculator()
        self.player_calculator = KeyPlayerInfluenceCalculator()
        self.ai_tactical_model = AITacticalModel()

    def calculate(self,
                  home_team: EnrichedTeamInput,
                  away_team: EnrichedTeamInput) -> EnsembleResult:
        """
        전체 모델 실행 및 앙상블

        Args:
            home_team: 홈팀 데이터
            away_team: 원정팀 데이터

        Returns:
            EnsembleResult with integrated probabilities and insights
        """
        logger.info(f"[Ensemble] Calculating for {home_team.name} vs {away_team.name}")

        # 1. Model 1: Poisson-Rating
        logger.info("[Ensemble] Running Model 1: Poisson-Rating...")
        poisson_result = self.poisson_model.calculate(home_team, away_team)

        # 2. Model 2: Zone Dominance
        logger.info("[Ensemble] Running Model 2: Zone Dominance...")
        zone_result = self.zone_calculator.calculate(home_team, away_team)

        # 3. Model 3: Key Player Influence
        logger.info("[Ensemble] Running Model 3: Key Player Influence...")
        player_result = self.player_calculator.calculate(home_team, away_team, zone_result)

        # 4. Model 4: AI Tactical (NEW)
        logger.info("[Ensemble] Running Model 4: AI Tactical...")
        # Pass math results as reference (AI can agree or disagree)
        math_reference = {
            'home_win': poisson_result.probabilities['home_win'],
            'draw': poisson_result.probabilities['draw'],
            'away_win': poisson_result.probabilities['away_win']
        }
        ai_result = self.ai_tactical_model.calculate(home_team, away_team, math_reference)

        # 5. Ensemble probabilities
        logger.info("[Ensemble] Integrating model results...")

        # Convert all models to probabilities
        poisson_probs = poisson_result.probabilities
        zone_probs = self._zone_to_probabilities(zone_result)
        player_probs = self._player_to_probabilities(player_result, zone_result)
        ai_probs = ai_result.probabilities

        # Weighted average (4 models)
        ensemble_probs = {
            'home_win': (
                self.WEIGHTS['poisson'] * poisson_probs['home_win'] +
                self.WEIGHTS['zone'] * zone_probs['home_win'] +
                self.WEIGHTS['player'] * player_probs['home_win'] +
                self.WEIGHTS['ai_tactical'] * ai_probs['home_win']
            ),
            'draw': (
                self.WEIGHTS['poisson'] * poisson_probs['draw'] +
                self.WEIGHTS['zone'] * zone_probs['draw'] +
                self.WEIGHTS['player'] * player_probs['draw'] +
                self.WEIGHTS['ai_tactical'] * ai_probs['draw']
            ),
            'away_win': (
                self.WEIGHTS['poisson'] * poisson_probs['away_win'] +
                self.WEIGHTS['zone'] * zone_probs['away_win'] +
                self.WEIGHTS['player'] * player_probs['away_win'] +
                self.WEIGHTS['ai_tactical'] * ai_probs['away_win']
            )
        }

        logger.info(f"[Ensemble] Final probabilities: "
                   f"Home {ensemble_probs['home_win']:.1%}, "
                   f"Draw {ensemble_probs['draw']:.1%}, "
                   f"Away {ensemble_probs['away_win']:.1%}")

        # 5. Expected goals (weighted average)
        expected_goals = {
            'home': (
                self.WEIGHTS['poisson'] * poisson_result.lambda_home +
                self.WEIGHTS['zone'] * zone_result.xG_home +
                self.WEIGHTS['player'] * zone_result.xG_home  # Player doesn't produce xG, use zone
            ),
            'away': (
                self.WEIGHTS['poisson'] * poisson_result.lambda_away +
                self.WEIGHTS['zone'] * zone_result.xG_away +
                self.WEIGHTS['player'] * zone_result.xG_away
            )
        }

        logger.info(f"[Ensemble] Expected goals: Home {expected_goals['home']:.2f}, Away {expected_goals['away']:.2f}")

        # 6. Tactical insights
        tactical_insights = self._generate_tactical_insights(
            home_team, away_team, poisson_result, zone_result, player_result
        )

        # 7. Zone dominance summary
        zone_summary = {
            'home_strengths': [z for z in zone_result.dominant_zones_home],
            'away_strengths': [z for z in zone_result.dominant_zones_away],
            'attack_control': {
                'home': zone_result.attack_control_home,
                'away': zone_result.attack_control_away
            }
        }

        # 8. Key player impacts
        key_player_impacts = []
        if player_result.top_home_player:
            key_player_impacts.append({
                'player': player_result.top_home_player.player_name,
                'team': 'home',
                'influence': player_result.top_home_player.influence
            })
        if player_result.top_away_player:
            key_player_impacts.append({
                'player': player_result.top_away_player.player_name,
                'team': 'away',
                'influence': player_result.top_away_player.influence
            })

        return EnsembleResult(
            ensemble_probabilities=ensemble_probs,
            expected_goals=expected_goals,
            zone_dominance_summary=zone_summary,
            key_player_impacts=key_player_impacts,
            tactical_insights=tactical_insights,
            poisson_result=poisson_result,
            zone_result=zone_result,
            player_result=player_result,
            ai_result=ai_result,
            weights=self.WEIGHTS
        )

    def _zone_to_probabilities(self, zone_result: ZoneDominanceResult) -> Dict[str, float]:
        """
        Zone Dominance 결과 → Win/Draw/Loss 확률 변환

        xG를 Poisson distribution으로 변환하여 확률 계산

        Args:
            zone_result: Zone Dominance 결과

        Returns:
            {home_win, draw, away_win}
        """
        # xG를 Poisson λ로 사용
        lambda_home = zone_result.xG_home
        lambda_away = zone_result.xG_away

        # Poisson distribution으로 스코어 확률 계산
        score_probs = {}
        for h in range(7):  # 0-6 goals
            for a in range(7):
                prob = poisson.pmf(h, lambda_home) * poisson.pmf(a, lambda_away)
                score_probs[(h, a)] = prob

        # Win/Draw/Loss 확률
        home_win = sum(score_probs[(h, a)] for h, a in score_probs if h > a)
        draw = sum(score_probs[(h, a)] for h, a in score_probs if h == a)
        away_win = sum(score_probs[(h, a)] for h, a in score_probs if h < a)

        # 정규화
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

    def _player_to_probabilities(self,
                                  player_result: KeyPlayerInfluenceResult,
                                  zone_result: ZoneDominanceResult) -> Dict[str, float]:
        """
        Player Influence 결과 → Win/Draw/Loss 확률 변환

        Top player influence를 바탕으로 확률 조정

        Args:
            player_result: Key Player 결과
            zone_result: Zone Dominance 결과 (baseline)

        Returns:
            {home_win, draw, away_win}
        """
        # Baseline: zone probabilities
        base_probs = self._zone_to_probabilities(zone_result)

        # Top player influence 차이 계산
        top_home_inf = player_result.top_home_player.influence if player_result.top_home_player else 5.0
        top_away_inf = player_result.top_away_player.influence if player_result.top_away_player else 5.0

        # Influence 차이 (-10 ~ +10)
        influence_diff = top_home_inf - top_away_inf

        # Sigmoid adjustment (-1 ~ +1)
        # influence_diff = +5 → home favored
        # influence_diff = -5 → away favored
        adjustment = math.tanh(influence_diff / 10.0)  # -1 ~ +1

        # Adjust probabilities
        # adjustment > 0 → boost home_win, reduce away_win
        # adjustment < 0 → boost away_win, reduce home_win
        home_win = base_probs['home_win'] * (1.0 + adjustment * 0.2)  # ±20% max
        away_win = base_probs['away_win'] * (1.0 - adjustment * 0.2)
        draw = base_probs['draw']

        # 정규화
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

    def _generate_tactical_insights(self,
                                      home_team: EnrichedTeamInput,
                                      away_team: EnrichedTeamInput,
                                      poisson_result: PoissonRatingResult,
                                      zone_result: ZoneDominanceResult,
                                      player_result: KeyPlayerInfluenceResult) -> Dict[str, str]:
        """
        전술적 인사이트 생성

        Args:
            All model results

        Returns:
            {formation_matchup, critical_zones, key_matchup}
        """
        # Formation matchup
        home_formation = home_team.formation
        away_formation = away_team.formation
        home_style = home_team.formation_tactics.style if home_team.formation_tactics else "Unknown"
        away_style = away_team.formation_tactics.style if away_team.formation_tactics else "Unknown"

        formation_matchup = f"{home_formation} ({home_style}) vs {away_formation} ({away_style})"

        # Critical zones (most contested)
        critical_zones = []
        for zone, ctrl in zone_result.zone_control.items():
            if 0.45 <= ctrl.home_control <= 0.55:  # Close contest
                critical_zones.append(zone)

        # Key matchup (top players)
        top_home = player_result.top_home_player.player_name if player_result.top_home_player else "Unknown"
        top_away = player_result.top_away_player.player_name if player_result.top_away_player else "Unknown"
        key_matchup = f"{top_home} vs {top_away}"

        return {
            'formation_matchup': formation_matchup,
            'critical_zones': ', '.join(critical_zones) if critical_zones else 'All zones balanced',
            'key_matchup': key_matchup
        }


if __name__ == "__main__":
    # 간단한 테스트
    logging.basicConfig(level=logging.INFO)

    from services.enriched_data_loader import EnrichedDomainDataLoader

    loader = EnrichedDomainDataLoader()
    arsenal = loader.load_team_data("Arsenal")
    liverpool = loader.load_team_data("Liverpool")

    ensemble = ModelEnsemble()
    result = ensemble.calculate(arsenal, liverpool)

    print("\n" + "="*80)
    print("Model Ensemble Test")
    print("="*80)

    print(f"\n{'='*80}")
    print("ENSEMBLE PROBABILITIES (Weighted 0.4/0.3/0.3)")
    print(f"{'='*80}")
    print(f"  Home win: {result.ensemble_probabilities['home_win']:.1%}")
    print(f"  Draw:     {result.ensemble_probabilities['draw']:.1%}")
    print(f"  Away win: {result.ensemble_probabilities['away_win']:.1%}")

    print(f"\n{'='*80}")
    print("EXPECTED GOALS (Weighted Average)")
    print(f"{'='*80}")
    print(f"  Home: {result.expected_goals['home']:.2f}")
    print(f"  Away: {result.expected_goals['away']:.2f}")

    print(f"\n{'='*80}")
    print("TACTICAL INSIGHTS")
    print(f"{'='*80}")
    print(f"  Formation matchup: {result.tactical_insights['formation_matchup']}")
    print(f"  Critical zones: {result.tactical_insights['critical_zones']}")
    print(f"  Key matchup: {result.tactical_insights['key_matchup']}")

    print(f"\n{'='*80}")
    print("ZONE DOMINANCE SUMMARY")
    print(f"{'='*80}")
    print(f"  Home strengths: {result.zone_dominance_summary['home_strengths']}")
    print(f"  Away strengths: {result.zone_dominance_summary['away_strengths']}")

    print(f"\n{'='*80}")
    print("KEY PLAYER IMPACTS")
    print(f"{'='*80}")
    for impact in result.key_player_impacts:
        print(f"  {impact['player']} ({impact['team']}): influence {impact['influence']:.1f}/10")

    print(f"\n{'='*80}")
    print("INDIVIDUAL MODEL RESULTS")
    print(f"{'='*80}")
    print(f"\nModel 1 (Poisson-Rating, weight={result.weights['poisson']}):")
    print(f"  Home {result.poisson_result.probabilities['home_win']:.1%}, "
          f"Draw {result.poisson_result.probabilities['draw']:.1%}, "
          f"Away {result.poisson_result.probabilities['away_win']:.1%}")

    zone_probs = ensemble._zone_to_probabilities(result.zone_result)
    print(f"\nModel 2 (Zone Dominance, weight={result.weights['zone']}):")
    print(f"  Home {zone_probs['home_win']:.1%}, "
          f"Draw {zone_probs['draw']:.1%}, "
          f"Away {zone_probs['away_win']:.1%}")

    player_probs = ensemble._player_to_probabilities(result.player_result, result.zone_result)
    print(f"\nModel 3 (Key Player, weight={result.weights['player']}):")
    print(f"  Home {player_probs['home_win']:.1%}, "
          f"Draw {player_probs['draw']:.1%}, "
          f"Away {player_probs['away_win']:.1%}")

    print(f"\nModel 4 (AI Tactical, weight={result.weights['ai_tactical']}):")
    print(f"  Home {result.ai_result.probabilities['home_win']:.1%}, "
          f"Draw {result.ai_result.probabilities['draw']:.1%}, "
          f"Away {result.ai_result.probabilities['away_win']:.1%}")
    print(f"  Confidence: {result.ai_result.confidence:.1%}")
    print(f"  Reasoning: {result.ai_result.reasoning}")

    print()
