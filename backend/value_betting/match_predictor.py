"""
Match Predictor
배당률 기반 경기 결과 예측 시스템
"""

import logging
from typing import Dict, List, Tuple, Optional
from scipy.stats import poisson
import numpy as np

logger = logging.getLogger(__name__)

# Sharp 북메이커 리스트 (가장 정확한 배당률 제공)
# 연구 결과: Sharp 북메이커 평균 정확도 ~60% vs 전체 평균 ~57%
SHARP_BOOKMAKERS = {
    'pinnacle',           # 가장 효율적인 시장
    'betfair_ex_uk',      # 베팅 거래소 (시장가)
    'betfair_ex_eu',      # 베팅 거래소 (시장가)
    'smarkets',           # 베팅 거래소
    'betclic',            # 유럽 Sharp 북메이커
    'marathonbet',        # Sharp 북메이커
}


class MatchPredictor:
    """
    배당률을 기반으로 경기 결과를 예측하는 클래스
    """

    def __init__(self):
        """MatchPredictor 초기화"""
        logger.info("MatchPredictor initialized")

    @staticmethod
    def odds_to_probability(odds: float) -> float:
        """
        배당률을 암시 확률로 변환

        Args:
            odds: 배당률 (decimal odds)

        Returns:
            확률 (0-1 사이)
        """
        if not odds or odds <= 0:
            return 0.0
        return 1.0 / odds

    @staticmethod
    def remove_margin(probabilities: Dict[str, float]) -> Dict[str, float]:
        """
        북메이커 마진 제거 (확률 합계를 1로 정규화)

        Args:
            probabilities: {'home': p1, 'draw': p2, 'away': p3}

        Returns:
            마진이 제거된 확률
        """
        total = sum(probabilities.values())
        if total == 0:
            return probabilities

        return {
            outcome: prob / total
            for outcome, prob in probabilities.items()
        }

    def calculate_consensus_probabilities(self, bookmakers: Dict[str, Dict], return_details: bool = False):
        """
        여러 북메이커의 배당률로부터 합의 확률(consensus probability) 계산

        Sharp 북메이커만 사용하여 정확도 향상 (~60%)

        Args:
            bookmakers: 북메이커 배당률 딕셔너리
                {'betfair': {'home': 1.5, 'draw': 4.0, 'away': 6.0}, ...}
            return_details: True일 경우 계산 과정 상세 정보도 반환

        Returns:
            return_details=False: {'home': 확률, 'draw': 확률, 'away': 확률}
            return_details=True: (확률, 상세정보)
        """
        # 1. Sharp 북메이커만 필터링
        sharp_bookmakers = {
            k: v for k, v in bookmakers.items()
            if k in SHARP_BOOKMAKERS
        }

        # 2. Sharp 북메이커가 너무 적으면 (3개 미만) 전체 사용
        MIN_SHARP_BOOKMAKERS = 3
        if len(sharp_bookmakers) < MIN_SHARP_BOOKMAKERS:
            logger.warning(
                f"Only {len(sharp_bookmakers)} Sharp bookmakers available "
                f"({list(sharp_bookmakers.keys())}), using all {len(bookmakers)} bookmakers"
            )
            sharp_bookmakers = bookmakers
        else:
            logger.info(
                f"Using {len(sharp_bookmakers)} Sharp bookmakers: {list(sharp_bookmakers.keys())}"
            )

        home_probs = []
        draw_probs = []
        away_probs = []

        # 상세 정보 저장 (북메이커별)
        bookmaker_details = []

        # 3. Sharp 북메이커 데이터 처리
        for bookmaker_key, odds_data in sharp_bookmakers.items():
            if not isinstance(odds_data, dict):
                continue

            bookmaker_info = {'name': bookmaker_key}

            # 홈 배당률
            if 'home' in odds_data:
                home_odd = odds_data['home']
                home_prob = self.odds_to_probability(home_odd)
                home_probs.append(home_prob)
                bookmaker_info['home_odds'] = round(home_odd, 2)
                bookmaker_info['home_prob'] = round(home_prob * 100, 2)

            # 무승부 배당률
            if 'draw' in odds_data:
                draw_odd = odds_data['draw']
                draw_prob = self.odds_to_probability(draw_odd)
                draw_probs.append(draw_prob)
                bookmaker_info['draw_odds'] = round(draw_odd, 2)
                bookmaker_info['draw_prob'] = round(draw_prob * 100, 2)

            # 원정 배당률
            if 'away' in odds_data:
                away_odd = odds_data['away']
                away_prob = self.odds_to_probability(away_odd)
                away_probs.append(away_prob)
                bookmaker_info['away_odds'] = round(away_odd, 2)
                bookmaker_info['away_prob'] = round(away_prob * 100, 2)

            if len(bookmaker_info) > 1:  # name 외에 데이터가 있을 때만 추가
                bookmaker_details.append(bookmaker_info)

        # 4. 평균 계산 후 마진 제거
        raw_probs = {
            'home': np.mean(home_probs) if home_probs else 0.33,
            'draw': np.mean(draw_probs) if draw_probs else 0.33,
            'away': np.mean(away_probs) if away_probs else 0.33
        }

        consensus_probs = self.remove_margin(raw_probs)

        if not return_details:
            return consensus_probs

        # 상세 정보 포함하여 반환
        details = {
            'bookmakers': bookmaker_details,
            'raw_average': {
                'home': round(raw_probs['home'] * 100, 2),
                'draw': round(raw_probs['draw'] * 100, 2),
                'away': round(raw_probs['away'] * 100, 2)
            },
            'margin_removed': {
                'home': round(consensus_probs['home'] * 100, 2),
                'draw': round(consensus_probs['draw'] * 100, 2),
                'away': round(consensus_probs['away'] * 100, 2)
            },
            'num_bookmakers': len(bookmaker_details)
        }

        return consensus_probs, details

    def extract_totals_odds(self, bookmakers: Dict[str, Dict]) -> Optional[Dict[str, float]]:
        """
        언더/오버 배당률 추출

        Args:
            bookmakers: 북메이커 데이터 (원본 API 응답)

        Returns:
            {'over': odds, 'under': odds, 'point': 2.5} 또는 None
        """
        over_odds = []
        under_odds = []

        # 원본 API 응답에서 totals 마켓 찾기
        if isinstance(bookmakers, list):
            # 디버그: 사용 가능한 마켓 확인
            if bookmakers:
                first_bookie_markets = [m.get('key') for m in bookmakers[0].get('markets', [])]
                logger.debug(f"Available markets: {first_bookie_markets}")

            for bookmaker in bookmakers:
                for market in bookmaker.get('markets', []):
                    if market.get('key') == 'totals':
                        for outcome in market.get('outcomes', []):
                            if outcome.get('name') == 'Over':
                                over_odds.append(outcome.get('price', 0))
                            elif outcome.get('name') == 'Under':
                                under_odds.append(outcome.get('price', 0))

        if over_odds and under_odds:
            logger.info(f"Extracted totals odds: Over={np.mean(over_odds):.2f}, Under={np.mean(under_odds):.2f}")
            return {
                'over': np.mean(over_odds),
                'under': np.mean(under_odds),
                'point': 2.5
            }
        else:
            logger.debug("No totals market data found")
        return None

    def calculate_total_goals_from_totals(self, totals_odds: Dict[str, float]) -> float:
        """
        언더/오버 배당률로 총 득점 기댓값 계산

        Args:
            totals_odds: {'over': odds, 'under': odds, 'point': 2.5}

        Returns:
            총 득점 기댓값
        """
        over_odds = totals_odds['over']
        under_odds = totals_odds['under']
        point = totals_odds['point']

        # 배당률 → 확률
        over_prob = self.odds_to_probability(over_odds)
        under_prob = self.odds_to_probability(under_odds)

        # 마진 제거
        total_prob = over_prob + under_prob
        if total_prob > 0:
            over_prob = over_prob / total_prob
            under_prob = under_prob / total_prob

        # 총 득점 기댓값 추정
        # Over 2.5 확률이 높으면 → 총 득점 많음
        # 간단한 선형 근사: E[Total] ≈ point + (over_prob - 0.5) * adjustment
        adjustment = 0.8  # 조정 계수
        expected_total = point + (over_prob - 0.5) * adjustment

        # 현실적인 범위로 제한 (1.5 ~ 4.5골)
        expected_total = max(1.5, min(4.5, expected_total))

        return round(expected_total, 2)

    def probabilities_to_expected_goals(
        self,
        probabilities: Dict[str, float],
        total_goals: Optional[float] = None
    ) -> Tuple[float, float]:
        """
        승/무/패 확률과 총 득점으로 각 팀의 예상 득점 계산

        Args:
            probabilities: {'home': p1, 'draw': p2, 'away': p3}
            total_goals: 총 득점 기댓값 (언더/오버에서 계산)

        Returns:
            (home_goals, away_goals) 예상 득점
        """
        home_prob = probabilities.get('home', 0.33)
        draw_prob = probabilities.get('draw', 0.33)
        away_prob = probabilities.get('away', 0.33)

        # 총 득점이 제공되지 않으면 경험적 공식 사용
        if total_goals is None:
            if draw_prob < 0.01:
                draw_prob = 0.01
            total_goals = -np.log(draw_prob) * 0.5 * 2

        # 승/무/패 확률로 득점 비율 분배
        # 홈 승리 확률이 높으면 → 홈팀 득점 비율 높음
        strength_diff = home_prob - away_prob

        # 기본 50:50 분배에서 확률 차이만큼 조정
        home_ratio = 0.5 + strength_diff * 0.3
        away_ratio = 1 - home_ratio

        home_expected = total_goals * home_ratio
        away_expected = total_goals * away_ratio

        # 현실적인 범위로 제한 (0.3 ~ 4.0골)
        home_expected = max(0.3, min(4.0, home_expected))
        away_expected = max(0.3, min(4.0, away_expected))

        return round(home_expected, 2), round(away_expected, 2)

    @staticmethod
    def calculate_score_probabilities(
        home_lambda: float,
        away_lambda: float,
        max_goals: int = 6
    ) -> Dict[str, Dict[Tuple[int, int], float]]:
        """
        Poisson distribution으로 스코어 확률 계산

        Args:
            home_lambda: 홈팀 예상 득점
            away_lambda: 원정팀 예상 득점
            max_goals: 최대 득점 수 (기본 6골)

        Returns:
            {
                'scores': {(home, away): probability},
                'home_win': probability,
                'draw': probability,
                'away_win': probability
            }
        """
        score_matrix = {}
        home_win_prob = 0.0
        draw_prob = 0.0
        away_win_prob = 0.0

        for home_goals in range(max_goals + 1):
            for away_goals in range(max_goals + 1):
                # Poisson 확률 계산
                prob = (
                    poisson.pmf(home_goals, home_lambda) *
                    poisson.pmf(away_goals, away_lambda)
                )
                score_matrix[(home_goals, away_goals)] = prob

                # 승/무/패 집계
                if home_goals > away_goals:
                    home_win_prob += prob
                elif home_goals == away_goals:
                    draw_prob += prob
                else:
                    away_win_prob += prob

        return {
            'scores': score_matrix,
            'home_win': home_win_prob,
            'draw': draw_prob,
            'away_win': away_win_prob
        }

    def get_most_likely_score(
        self,
        score_probs: Dict[Tuple[int, int], float],
        top_n: int = 5
    ) -> List[Dict]:
        """
        가장 가능성 높은 스코어 예측

        Args:
            score_probs: {(home, away): probability}
            top_n: 반환할 상위 스코어 개수

        Returns:
            [{'score': '2-1', 'home': 2, 'away': 1, 'probability': 0.15}, ...]
        """
        # 확률 기준 정렬
        sorted_scores = sorted(
            score_probs.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

        return [
            {
                'score': f"{home}-{away}",
                'home_goals': home,
                'away_goals': away,
                'probability': round(prob * 100, 1)
            }
            for (home, away), prob in sorted_scores
        ]

    def calculate_confidence(
        self,
        probabilities: Dict[str, float],
        num_bookmakers: int,
        uses_totals: bool = False
    ) -> Dict[str, float]:
        """
        개선된 신뢰도 계산

        신뢰도 = "이 예측이 실제 경기 결과와 맞을 확률"

        배당률 기반 예측의 신뢰도는:
        1. 기본 정확도: 배당률 기반 예측의 역사적 정확도 (55-60% 연구 결과)
        2. 예측 명확성: 1위와 2위의 차이가 클수록 신뢰도 증가
        3. 데이터 품질: 북메이커 수, totals 데이터 사용 여부

        Args:
            probabilities: {'home': p1, 'draw': p2, 'away': p3}
            num_bookmakers: 북메이커 수
            uses_totals: 언더/오버 데이터 사용 여부

        Returns:
            {
                'confidence': 최종 신뢰도 (0-1),
                'base': 기본 정확도,
                'clarity_bonus': 예측 명확성 보너스,
                'quality_bonus': 데이터 품질 보너스
            }
        """
        # 확률을 내림차순 정렬
        sorted_probs = sorted(probabilities.values(), reverse=True)

        # 1. 기본 신뢰도: 배당률 기반 예측의 역사적 정확도
        #    연구 결과: Sharp 북메이커 평균 정확도는 약 60% (전체 평균 57%)
        #    우리 시스템은 Sharp 북메이커만 사용하므로 더 높은 정확도를 가짐
        base_confidence = 0.60

        # 2. 예측 명확성 조정
        #    1위와 2위의 차이가 클수록 해당 경기의 예측 정확도가 약간 높음
        #    하지만 55-60% 평균은 이미 모든 경기를 포함한 결과이므로 큰 변동은 없음
        clarity_gap = sorted_probs[0] - sorted_probs[1]

        # 명확성에 따른 소폭 조정 (최대 ±5%)
        if clarity_gap >= 0.30:
            clarity_bonus = 0.05  # 매우 명확한 경기
        elif clarity_gap >= 0.20:
            clarity_bonus = 0.03
        elif clarity_gap >= 0.15:
            clarity_bonus = 0.02
        elif clarity_gap >= 0.10:
            clarity_bonus = 0.0  # 보통 경기
        elif clarity_gap >= 0.05:
            clarity_bonus = -0.03
        else:
            clarity_bonus = -0.07  # 매우 불확실한 경기 (3파전)

        # 3. 데이터 품질 조정
        quality_bonus = 0.0

        # 북메이커 수가 많을수록 합의의 신뢰도 증가 (최대 ±3%)
        if num_bookmakers >= 20:
            quality_bonus += 0.03
        elif num_bookmakers >= 15:
            quality_bonus += 0.02
        elif num_bookmakers >= 10:
            quality_bonus += 0.01
        elif num_bookmakers >= 5:
            quality_bonus += 0.0
        else:
            quality_bonus -= 0.03  # 데이터가 적으면 신뢰도 하락

        # 언더/오버 데이터 사용 시 득점 예측 정확도 향상
        if uses_totals:
            quality_bonus += 0.02

        # 최종 신뢰도 계산
        # Sharp 북메이커 정확도 60% 근처를 유지 (대략 50-70% 범위)
        final_confidence = base_confidence + clarity_bonus + quality_bonus
        final_confidence = min(0.70, final_confidence)  # 70% 상한선 (Sharp 북메이커 최고 정확도)
        final_confidence = max(0.50, final_confidence)  # 50% 하한선 (불확실한 경기)

        logger.debug(
            f"Confidence breakdown: base={base_confidence:.3f}, "
            f"clarity={clarity_bonus:.3f}, quality={quality_bonus:.3f}, "
            f"final={final_confidence:.3f}"
        )

        return {
            'confidence': final_confidence,
            'base': base_confidence,
            'clarity_bonus': clarity_bonus,
            'quality_bonus': quality_bonus,
            'clarity_gap': clarity_gap
        }

    def predict_match(self, match_data: Dict) -> Dict:
        """
        경기 결과 예측 (메인 메서드)

        Args:
            match_data: {
                'home_team': str,
                'away_team': str,
                'commence_time': str,
                'bookmakers': {...},  # Parsed h2h odds
                'bookmakers_raw': [...]  # Raw API data with totals
            }

        Returns:
            {
                'home_team': str,
                'away_team': str,
                'commence_time': str,
                'prediction': {
                    'outcome': 'home' | 'draw' | 'away',
                    'confidence': float (0-100),
                    'probabilities': {'home': %, 'draw': %, 'away': %},
                    'expected_goals': {'home': float, 'away': float},
                    'most_likely_scores': [...],
                    'poisson_probabilities': {'home_win': %, 'draw': %, 'away_win': %}
                },
                'methodology': {
                    'data_source': str,
                    'num_bookmakers': int,
                    'approach': str,
                    'uses_totals_odds': bool
                }
            }
        """
        home_team = match_data.get('home_team', 'Unknown')
        away_team = match_data.get('away_team', 'Unknown')
        bookmakers = match_data.get('bookmakers', {})
        bookmakers_raw = match_data.get('bookmakers_raw', [])

        # 1. Consensus 확률 계산 (h2h 승무패 확률) - 상세 정보 포함
        consensus_probs, consensus_details = self.calculate_consensus_probabilities(bookmakers, return_details=True)

        # 2. 언더/오버 배당률에서 총 득점 기댓값 계산
        total_goals = None
        uses_totals = False
        totals_odds = self.extract_totals_odds(bookmakers_raw)

        if totals_odds:
            total_goals = self.calculate_total_goals_from_totals(totals_odds)
            uses_totals = True
            logger.info(f"Using totals odds: {totals_odds} → Expected total goals: {total_goals}")

        # 3. 예상 득점 계산 (totals 기반 또는 경험 공식)
        home_goals, away_goals = self.probabilities_to_expected_goals(
            consensus_probs,
            total_goals
        )

        # 4. Poisson으로 스코어 확률 계산
        poisson_result = self.calculate_score_probabilities(home_goals, away_goals)

        # 5. 가장 가능성 높은 스코어
        most_likely_scores = self.get_most_likely_score(poisson_result['scores'])

        # 6. 최종 예측 결과
        predicted_outcome = max(consensus_probs, key=consensus_probs.get)

        # 7. 개선된 신뢰도 계산
        confidence_data = self.calculate_confidence(
            probabilities=consensus_probs,
            num_bookmakers=len(bookmakers),
            uses_totals=uses_totals
        )

        return {
            'home_team': home_team,
            'away_team': away_team,
            'commence_time': match_data.get('commence_time'),
            'match_id': match_data.get('id'),
            'prediction': {
                'outcome': predicted_outcome,
                'confidence': round(confidence_data['confidence'] * 100, 1),
                'confidence_breakdown': {
                    'base': round(confidence_data['base'] * 100, 1),
                    'clarity_bonus': round(confidence_data['clarity_bonus'] * 100, 1),
                    'quality_bonus': round(confidence_data['quality_bonus'] * 100, 1),
                    'clarity_gap': round(confidence_data['clarity_gap'] * 100, 1)
                },
                'probabilities': {
                    k: round(v * 100, 1) for k, v in consensus_probs.items()
                },
                'expected_goals': {
                    'home': home_goals,
                    'away': away_goals
                },
                'most_likely_scores': most_likely_scores,
                'poisson_probabilities': {
                    'home_win': round(poisson_result['home_win'] * 100, 1),
                    'draw': round(poisson_result['draw'] * 100, 1),
                    'away_win': round(poisson_result['away_win'] * 100, 1)
                },
                # 계산 과정 상세 정보 추가
                'calculation_details': {
                    'consensus': consensus_details,
                    'total_goals': total_goals,
                    'poisson_lambda': {
                        'home': home_goals,
                        'away': away_goals
                    }
                }
            },
            'methodology': {
                'data_source': 'The Odds API (Sharp bookmakers: Pinnacle, Betfair, etc.)',
                'num_bookmakers': len(bookmakers),
                'approach': 'Sharp bookmaker consensus with Poisson distribution',
                'uses_totals_odds': uses_totals
            }
        }

    def predict_all_matches(self, matches: List[Dict]) -> List[Dict]:
        """
        모든 경기 예측

        Args:
            matches: 경기 리스트

        Returns:
            예측 결과 리스트
        """
        predictions = []

        for match in matches:
            try:
                # 데이터 유효성 검사
                if not isinstance(match, dict):
                    logger.error(f"Invalid match data type: {type(match)}, value: {match}")
                    continue

                prediction = self.predict_match(match)
                predictions.append(prediction)
            except Exception as e:
                import traceback
                match_id = match.get('id') if isinstance(match, dict) else 'Unknown'
                logger.error(f"Error predicting match {match_id}: {str(e)}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                continue

        logger.info(f"Predicted {len(predictions)} matches")
        return predictions
