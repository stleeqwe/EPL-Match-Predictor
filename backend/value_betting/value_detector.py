"""
Value Detector - 배당률 기반 Value Bet 탐지 엔진

학술적 근거:
- Constantinou & Fenton (2012): 북메이커 배당률 > 통계 모델
- Pinnacle은 "sharp bookmaker"로 시장 효율성 대표
- Edge = (진짜 확률 × 배당률) - 1
"""

from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

from .utils import (
    decimal_to_probability,
    remove_overround,
    calculate_edge,
    get_best_odds,
    calculate_implied_probability_from_multiple_bookies,
    validate_probabilities
)
from .exceptions import InsufficientOddsDataError, InvalidProbabilityError

logger = logging.getLogger(__name__)


class ValueDetector:
    """
    Value Bet 탐지기
    
    핵심 원리:
    1. Pinnacle을 "진짜 확률" 기준으로 사용
    2. 다른 북메이커의 배당률과 비교
    3. Edge가 임계값 이상이면 Value Bet
    
    Attributes:
        min_edge (float): 최소 edge (예: 0.03 = 3%)
        min_confidence (float): 최소 신뢰도 (예: 0.65 = 65%)
        sharp_bookmaker (str): 기준 북메이커 (기본: 'pinnacle')
    """
    
    def __init__(
        self,
        min_edge: float = 0.02,
        min_confidence: float = 0.65,
        sharp_bookmaker: str = 'pinnacle'
    ):
        """
        Args:
            min_edge: 최소 edge (2% 기본)
            min_confidence: 최소 신뢰도 (65% 기본)
            sharp_bookmaker: 기준 북메이커
        """
        self.min_edge = min_edge
        self.min_confidence = min_confidence
        self.sharp_bookmaker = sharp_bookmaker
        
        logger.info(
            f"ValueDetector initialized: min_edge={min_edge:.1%}, "
            f"min_confidence={min_confidence:.1%}, "
            f"sharp_bookmaker={sharp_bookmaker}"
        )
    
    def detect_value_bets(
        self,
        match_analysis: Dict
    ) -> List[Dict]:
        """
        경기 분석 결과에서 Value Bet 탐지
        
        Args:
            match_analysis: {
                'match_id': 'abc123',
                'home_team': 'Manchester City',
                'away_team': 'Liverpool',
                'commence_time': datetime(...),
                'consensus_probability': {'home': 0.5, 'draw': 0.3, 'away': 0.2},
                'best_odds': {
                    'home': {'bookmaker': 'bet365', 'odds': 2.1},
                    'draw': {'bookmaker': 'williamhill', 'odds': 3.6},
                    'away': {'bookmaker': 'betfair', 'odds': 4.5}
                },
                'bookmakers_raw': {
                    'pinnacle': {'home': 2.0, 'draw': 3.5, 'away': 4.0},
                    'bet365': {'home': 2.1, 'draw': 3.4, 'away': 3.9}
                }
            }
        
        Returns:
            List[Dict]: Value Bet 목록
            [
                {
                    'match_id': 'abc123',
                    'home_team': 'Manchester City',
                    'away_team': 'Liverpool',
                    'outcome': 'home',
                    'bookmaker': 'bet365',
                    'odds': 2.1,
                    'edge': 0.05,  # 5%
                    'confidence': 0.75,
                    'estimated_probability': 0.524,
                    'recommendation': 'MODERATE_BET',
                    'commence_time': datetime(...)
                }
            ]
        """
        value_bets = []
        
        # 필수 필드 확인
        required_fields = ['match_id', 'home_team', 'away_team', 'bookmakers_raw']
        for field in required_fields:
            if field not in match_analysis:
                logger.warning(f"Missing field: {field}")
                return value_bets
        
        bookmakers = match_analysis['bookmakers_raw']
        
        # Pinnacle 배당률 확인 (기준점)
        if self.sharp_bookmaker not in bookmakers:
            logger.warning(
                f"{self.sharp_bookmaker} not found. "
                f"Available: {list(bookmakers.keys())}"
            )
            # Pinnacle이 없으면 consensus를 사용
            reference_probs = match_analysis.get('consensus_probability')
            if not reference_probs:
                logger.error("No reference probabilities available")
                return value_bets
        else:
            # Pinnacle에서 진짜 확률 추정
            pinnacle_odds = bookmakers[self.sharp_bookmaker]
            reference_probs = remove_overround(pinnacle_odds)
        
        # 각 결과(home/draw/away)에 대해 Value 탐지
        for outcome in ['home', 'draw', 'away']:
            if outcome not in reference_probs:
                continue
            
            estimated_prob = reference_probs[outcome]
            
            # 모든 북메이커의 배당률 확인
            for bookmaker, odds_dict in bookmakers.items():
                if outcome not in odds_dict:
                    continue
                
                # Pinnacle 자체는 제외 (기준점이므로)
                if bookmaker == self.sharp_bookmaker:
                    continue
                
                odds = odds_dict[outcome]
                
                # Edge 계산
                edge = calculate_edge(estimated_prob, odds)
                
                # Edge가 임계값 이상인가?
                if edge < self.min_edge * 100:  # min_edge는 0.02 → 2%
                    continue
                
                # 신뢰도 계산
                confidence = self._calculate_confidence(
                    estimated_prob,
                    odds,
                    bookmakers,
                    outcome
                )
                
                # 신뢰도가 임계값 이상인가?
                if confidence < self.min_confidence:
                    continue
                
                # Value Bet 발견!
                value_bet = {
                    'match_id': match_analysis['match_id'],
                    'home_team': match_analysis['home_team'],
                    'away_team': match_analysis['away_team'],
                    'outcome': outcome,
                    'bookmaker': bookmaker,
                    'odds': odds,
                    'edge': edge / 100,  # 0.05 = 5%
                    'confidence': confidence,
                    'estimated_probability': estimated_prob,
                    'recommendation': self._get_recommendation(edge / 100, confidence),
                    'commence_time': match_analysis.get('commence_time'),
                    'detected_at': datetime.now()
                }
                
                value_bets.append(value_bet)
                
                logger.info(
                    f"Value Bet: {match_analysis['home_team']} vs {match_analysis['away_team']} | "
                    f"{outcome} @ {bookmaker} ({odds:.2f}) | "
                    f"Edge: {edge:.1f}% | Confidence: {confidence:.1%}"
                )
        
        return value_bets
    
    def _calculate_confidence(
        self,
        estimated_prob: float,
        offered_odds: float,
        all_bookmakers: Dict[str, Dict[str, float]],
        outcome: str
    ) -> float:
        """
        신뢰도 계산
        
        고려 사항:
        1. Edge의 크기 (클수록 신뢰도 상승)
        2. 북메이커 수 (많을수록 신뢰도 상승)
        3. 배당률 분산 (일관성 있을수록 신뢰도 상승)
        
        Args:
            estimated_prob: 추정 확률
            offered_odds: 제공된 배당률
            all_bookmakers: 모든 북메이커 배당률
            outcome: 결과 ('home', 'draw', 'away')
        
        Returns:
            float: 신뢰도 (0~1)
        """
        # 1. Edge 기반 신뢰도 (0~0.4)
        edge = calculate_edge(estimated_prob, offered_odds) / 100
        edge_confidence = min(edge * 8, 0.4)  # 5% edge → 0.4
        
        # 2. 북메이커 수 기반 (0~0.3)
        num_bookies = len(all_bookmakers)
        bookie_confidence = min(num_bookies / 10, 0.3)  # 10개 이상 → 0.3
        
        # 3. 배당률 일관성 (0~0.3)
        odds_list = []
        for bookie, odds_dict in all_bookmakers.items():
            if outcome in odds_dict:
                odds_list.append(odds_dict[outcome])
        
        if len(odds_list) > 1:
            # 표준편차가 작을수록 일관성 높음
            mean_odds = sum(odds_list) / len(odds_list)
            variance = sum((x - mean_odds) ** 2 for x in odds_list) / len(odds_list)
            std_dev = variance ** 0.5
            
            # 표준편차가 0.5 이하면 일관성 높음
            consistency_confidence = max(0.3 - std_dev * 0.6, 0)
        else:
            consistency_confidence = 0.15  # 기본값
        
        # 총 신뢰도
        total_confidence = edge_confidence + bookie_confidence + consistency_confidence
        
        return min(total_confidence, 1.0)
    
    def _get_recommendation(self, edge: float, confidence: float) -> str:
        """
        베팅 추천 등급
        
        Args:
            edge: Edge (0.05 = 5%)
            confidence: 신뢰도 (0~1)
        
        Returns:
            str: 'STRONG_BET', 'MODERATE_BET', 'SMALL_BET'
        """
        # Strong: Edge >= 5% AND Confidence >= 75%
        if edge >= 0.05 and confidence >= 0.75:
            return 'STRONG_BET'
        
        # Moderate: Edge >= 3% AND Confidence >= 65%
        elif edge >= 0.03 and confidence >= 0.65:
            return 'MODERATE_BET'
        
        # Small: 그 외
        else:
            return 'SMALL_BET'
    
    def summarize_value_bets(self, value_bets: List[Dict]) -> Dict:
        """
        Value Bet 통계 요약
        
        Args:
            value_bets: detect_value_bets() 결과
        
        Returns:
            Dict: 통계 요약
        """
        if not value_bets:
            return {
                'total_count': 0,
                'by_recommendation': {},
                'by_outcome': {},
                'avg_edge': 0,
                'avg_confidence': 0,
                'top_opportunities': []
            }
        
        # 추천 등급별 집계
        by_recommendation = {}
        for bet in value_bets:
            rec = bet['recommendation']
            by_recommendation[rec] = by_recommendation.get(rec, 0) + 1
        
        # 결과별 집계
        by_outcome = {}
        for bet in value_bets:
            outcome = bet['outcome']
            by_outcome[outcome] = by_outcome.get(outcome, 0) + 1
        
        # 평균 계산
        avg_edge = sum(bet['edge'] for bet in value_bets) / len(value_bets)
        avg_confidence = sum(bet['confidence'] for bet in value_bets) / len(value_bets)
        
        # 상위 기회 (edge × confidence 기준)
        sorted_bets = sorted(
            value_bets,
            key=lambda x: x['edge'] * x['confidence'],
            reverse=True
        )
        top_opportunities = sorted_bets[:5]
        
        return {
            'total_count': len(value_bets),
            'by_recommendation': by_recommendation,
            'by_outcome': by_outcome,
            'avg_edge': avg_edge,
            'avg_confidence': avg_confidence,
            'top_opportunities': top_opportunities
        }
