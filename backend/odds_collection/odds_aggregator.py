"""
Odds Aggregator
여러 북메이커의 배당률을 통합 및 분석
"""

from typing import Dict, List, Tuple, Optional
import numpy as np
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class OddsAggregator:
    """
    배당률 통합 및 분석기
    
    주요 기능:
    1. 다중 북메이커 배당률 통합
    2. Overround(마진) 제거
    3. Consensus(합의) 확률 계산
    4. 북메이커별 신뢰도 가중치
    """
    
    # 북메이커별 신뢰도 (낮은 마진 = 높은 신뢰도)
    BOOKMAKER_TRUST_SCORES = {
        'pinnacle': 1.0,      # 가장 낮은 마진 (~2%), Sharp 북메이커
        'betfair': 0.95,      # P2P 거래소, 낮은 마진
        'bet365': 0.85,       # 대형 북메이커
        'williamhill': 0.80,
        'unibet': 0.80,
        '1xbet': 0.70,        # 높은 마진
        'default': 0.75       # 기본값
    }
    
    def __init__(self):
        self.trust_scores = self.BOOKMAKER_TRUST_SCORES.copy()
    
    def calculate_overround(self, odds: Dict[str, float]) -> float:
        """
        Overround(북메이커 마진) 계산
        
        Overround = Sum(1/odds) - 1
        
        예시:
        - 홈 1.80, 무 3.50, 원정 4.20
        - 1/1.80 + 1/3.50 + 1/4.20 = 1.052
        - Overround = 5.2% (북메이커 수익)
        
        Args:
            odds: {'home': 1.80, 'draw': 3.50, 'away': 4.20}
        
        Returns:
            float: Overround (0.052 = 5.2%)
        """
        if not all(k in odds for k in ['home', 'draw', 'away']):
            logger.warning(f"Missing odds data: {odds}")
            return 0.0
        
        implied_probs = sum(1/odds[k] for k in ['home', 'draw', 'away'])
        overround = implied_probs - 1.0
        
        return max(0.0, overround)
    
    def convert_odds_to_probability(
        self,
        odds: Dict[str, float],
        remove_overround: bool = True
    ) -> Dict[str, float]:
        """
        배당률 → 확률 변환
        
        Args:
            odds: {'home': 1.80, 'draw': 3.50, 'away': 4.20}
            remove_overround: True면 마진 제거 (정규화)
        
        Returns:
            Dict[str, float]: {'home': 0.55, 'draw': 0.27, 'away': 0.18}
        """
        # 암묵적 확률 계산
        probs = {
            'home': 1 / odds['home'],
            'draw': 1 / odds['draw'],
            'away': 1 / odds['away']
        }
        
        # Overround 제거 (정규화)
        if remove_overround:
            total = sum(probs.values())
            probs = {k: v/total for k, v in probs.items()}
        
        return probs
    
    def get_best_odds(
        self,
        bookmakers: Dict[str, Dict[str, float]]
    ) -> Dict[str, Tuple[str, float]]:
        """
        각 결과별 최고 배당률 찾기
        
        Args:
            bookmakers: {
                'bet365': {'home': 1.80, 'draw': 3.50, 'away': 4.20},
                'pinnacle': {'home': 1.75, 'draw': 3.60, 'away': 4.50}
            }
        
        Returns:
            {
                'home': ('bet365', 1.80),
                'draw': ('pinnacle', 3.60),
                'away': ('pinnacle', 4.50)
            }
        """
        best_odds = {}
        
        for outcome in ['home', 'draw', 'away']:
            max_odds = 0.0
            best_bookie = None
            
            for bookie, odds in bookmakers.items():
                if outcome in odds and odds[outcome] > max_odds:
                    max_odds = odds[outcome]
                    best_bookie = bookie
            
            if best_bookie:
                best_odds[outcome] = (best_bookie, max_odds)
        
        return best_odds
    
    def get_consensus_probability(
        self,
        bookmakers: Dict[str, Dict[str, float]],
        method: str = 'weighted_average'
    ) -> Dict[str, float]:
        """
        북메이커들의 합의 확률 계산
        
        Args:
            bookmakers: 북메이커별 배당률
            method: 'weighted_average', 'pinnacle_only', 'median'
        
        Returns:
            Dict[str, float]: Consensus 확률
        """
        if method == 'pinnacle_only':
            # Pinnacle만 사용 (가장 정확)
            if 'pinnacle' in bookmakers:
                return self.convert_odds_to_probability(
                    bookmakers['pinnacle'],
                    remove_overround=True
                )
            else:
                logger.warning("Pinnacle odds not available, falling back to weighted average")
                method = 'weighted_average'
        
        if method == 'weighted_average':
            # 신뢰도 가중 평균
            weighted_probs = {'home': 0.0, 'draw': 0.0, 'away': 0.0}
            total_weight = 0.0
            
            for bookie, odds in bookmakers.items():
                weight = self.trust_scores.get(bookie, self.trust_scores['default'])
                probs = self.convert_odds_to_probability(odds, remove_overround=True)
                
                for outcome in ['home', 'draw', 'away']:
                    weighted_probs[outcome] += probs[outcome] * weight
                
                total_weight += weight
            
            # 정규화
            if total_weight > 0:
                weighted_probs = {
                    k: v/total_weight for k, v in weighted_probs.items()
                }
            
            return weighted_probs
        
        if method == 'median':
            # 중앙값 (이상치 제거)
            all_probs = {
                'home': [],
                'draw': [],
                'away': []
            }
            
            for odds in bookmakers.values():
                probs = self.convert_odds_to_probability(odds, remove_overround=True)
                for outcome in ['home', 'draw', 'away']:
                    all_probs[outcome].append(probs[outcome])
            
            median_probs = {
                outcome: np.median(probs_list)
                for outcome, probs_list in all_probs.items()
            }
            
            return median_probs
        
        raise ValueError(f"Unknown method: {method}")
    
    def analyze_match_odds(
        self,
        match_data: Dict
    ) -> Dict:
        """
        경기 배당률 종합 분석
        
        Args:
            match_data: {
                'home_team': 'Man City',
                'away_team': 'Liverpool',
                'bookmakers': {...}
            }
        
        Returns:
            Dict: 분석 결과
        """
        bookmakers = match_data['bookmakers']
        
        # 1. 각 북메이커의 overround 계산
        overrounds = {}
        for bookie, odds in bookmakers.items():
            overrounds[bookie] = self.calculate_overround(odds)
        
        # 2. 최저 마진 북메이커 (가장 fair한 배당률)
        min_overround_bookie = min(overrounds, key=overrounds.get)
        min_overround = overrounds[min_overround_bookie]
        
        # 3. 최고 배당률
        best_odds = self.get_best_odds(bookmakers)
        
        # 4. Consensus 확률
        consensus_prob = self.get_consensus_probability(bookmakers, method='weighted_average')
        
        # 5. Pinnacle 확률 (기준)
        pinnacle_prob = None
        if 'pinnacle' in bookmakers:
            pinnacle_prob = self.convert_odds_to_probability(
                bookmakers['pinnacle'],
                remove_overround=True
            )
        
        # 6. 배당률 분산 (북메이커들 간 의견 차이)
        odds_variance = self._calculate_odds_variance(bookmakers)
        
        return {
            'home_team': match_data['home_team'],
            'away_team': match_data['away_team'],
            'commence_time': match_data.get('commence_time'),
            'num_bookmakers': len(bookmakers),
            'overrounds': overrounds,
            'fairest_bookmaker': {
                'name': min_overround_bookie,
                'margin': min_overround * 100  # % 형식
            },
            'best_odds': best_odds,
            'consensus_probability': consensus_prob,
            'pinnacle_probability': pinnacle_prob,
            'odds_variance': odds_variance,
            'market_efficiency': self._assess_market_efficiency(odds_variance, min_overround)
        }
    
    def _calculate_odds_variance(
        self,
        bookmakers: Dict[str, Dict[str, float]]
    ) -> Dict[str, float]:
        """배당률 분산 계산 (북메이커 간 의견 불일치 정도)"""
        variance = {}
        
        for outcome in ['home', 'draw', 'away']:
            odds_list = [
                odds[outcome] for odds in bookmakers.values()
                if outcome in odds
            ]
            
            if len(odds_list) >= 2:
                variance[outcome] = float(np.var(odds_list))
            else:
                variance[outcome] = 0.0
        
        return variance
    
    def _assess_market_efficiency(
        self,
        variance: Dict[str, float],
        min_overround: float
    ) -> str:
        """
        시장 효율성 평가
        
        낮은 분산 + 낮은 마진 = 효율적 시장 (예측 어려움)
        높은 분산 + 높은 마진 = 비효율적 시장 (기회 있음)
        """
        avg_variance = np.mean(list(variance.values()))
        
        if avg_variance < 0.01 and min_overround < 0.03:
            return "highly_efficient"  # 북메이커들 의견 일치, 낮은 마진
        elif avg_variance < 0.02 and min_overround < 0.05:
            return "efficient"
        elif avg_variance > 0.05 or min_overround > 0.08:
            return "inefficient"  # 기회 있을 수 있음
        else:
            return "moderate"


# ============================================================
# CLI 테스트
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Odds Aggregator Test")
    print("=" * 60)
    
    # 테스트 데이터
    test_match = {
        'home_team': 'Manchester City',
        'away_team': 'Liverpool',
        'commence_time': datetime(2025, 10, 5, 15, 0),
        'bookmakers': {
            'bet365': {'home': 1.80, 'draw': 3.50, 'away': 4.20},
            'pinnacle': {'home': 1.75, 'draw': 3.60, 'away': 4.50},
            'betfair': {'home': 1.82, 'draw': 3.45, 'away': 4.10},
            'williamhill': {'home': 1.78, 'draw': 3.55, 'away': 4.30}
        }
    }
    
    aggregator = OddsAggregator()
    
    # 분석 실행
    analysis = aggregator.analyze_match_odds(test_match)
    
    # 결과 출력
    print(f"\n📊 Match: {analysis['home_team']} vs {analysis['away_team']}")
    print(f"   Bookmakers: {analysis['num_bookmakers']}")
    
    print(f"\n💰 Overrounds (Bookmaker Margins):")
    for bookie, margin in analysis['overrounds'].items():
        print(f"   {bookie:12s}: {margin*100:.2f}%")
    
    print(f"\n✅ Fairest Bookmaker:")
    print(f"   {analysis['fairest_bookmaker']['name']} "
          f"(margin: {analysis['fairest_bookmaker']['margin']:.2f}%)")
    
    print(f"\n🎯 Best Odds:")
    for outcome, (bookie, odds) in analysis['best_odds'].items():
        print(f"   {outcome.capitalize():5s}: {odds:.2f} @ {bookie}")
    
    print(f"\n📈 Consensus Probability (Weighted Avg):")
    for outcome, prob in analysis['consensus_probability'].items():
        print(f"   {outcome.capitalize():5s}: {prob*100:.1f}%")
    
    if analysis['pinnacle_probability']:
        print(f"\n🏆 Pinnacle Probability (Most Accurate):")
        for outcome, prob in analysis['pinnacle_probability'].items():
            print(f"   {outcome.capitalize():5s}: {prob*100:.1f}%")
    
    print(f"\n📊 Odds Variance (Disagreement):")
    for outcome, var in analysis['odds_variance'].items():
        print(f"   {outcome.capitalize():5s}: {var:.4f}")
    
    print(f"\n🎲 Market Efficiency: {analysis['market_efficiency']}")
    
    print("\n" + "=" * 60)
    print("✅ Test Complete!")
    print("=" * 60)
