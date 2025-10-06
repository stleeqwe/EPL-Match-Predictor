"""
Arbitrage Finder - 북메이커 간 차익거래 기회 탐지

무위험 차익거래 (Arbitrage):
- 서로 다른 북메이커의 배당률 차이를 이용
- 모든 결과에 베팅하여 무조건 수익 보장
- 현실적으로 매우 드물고 즉시 사라짐

계산 공식:
Arbitrage Percentage = (1/odds_home) + (1/odds_draw) + (1/odds_away)
- < 1.0이면 arbitrage 기회 존재
- 예: 0.95 → 5% 수익 보장
"""

from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

from .utils import (
    decimal_to_probability,
    get_best_odds
)
from .exceptions import NoArbitrageOpportunityError

logger = logging.getLogger(__name__)


class ArbitrageFinder:
    """
    Arbitrage 기회 탐지기
    
    주의사항:
    1. 실제로는 매우 드뭄 (현대 시장의 효율성)
    2. 발견 즉시 사라짐 (초 단위)
    3. 북메이커가 arbitrage 베터를 차단할 수 있음
    4. 베팅 제한, 계정 폐쇄 위험
    
    Attributes:
        min_profit (float): 최소 수익률 (예: 0.005 = 0.5%)
    """
    
    def __init__(self, min_profit: float = 0.005):
        """
        Args:
            min_profit: 최소 수익률 (0.5% 기본)
        """
        self.min_profit = min_profit
        logger.info(f"ArbitrageFinder initialized: min_profit={min_profit:.2%}")
    
    def find_arbitrage_opportunities(
        self,
        matches_analysis: List[Dict]
    ) -> List[Dict]:
        """
        여러 경기에서 arbitrage 기회 탐색
        
        Args:
            matches_analysis: 경기 분석 결과 리스트
        
        Returns:
            List[Dict]: Arbitrage 기회 목록
        """
        opportunities = []
        
        for match in matches_analysis:
            try:
                arb = self.check_arbitrage(match)
                if arb:
                    opportunities.append(arb)
            except Exception as e:
                logger.error(f"Error checking arbitrage: {e}")
                continue
        
        logger.info(f"Found {len(opportunities)} arbitrage opportunities")
        return opportunities
    
    def check_arbitrage(self, match_analysis: Dict) -> Optional[Dict]:
        """
        단일 경기의 arbitrage 기회 확인
        
        전략:
        1. 각 결과(home/draw/away)의 최고 배당률 찾기
        2. Arbitrage percentage 계산
        3. < 1.0이면 기회 존재
        
        Args:
            match_analysis: {
                'match_id': 'abc123',
                'home_team': 'Manchester City',
                'away_team': 'Liverpool',
                'best_odds': {
                    'home': {'bookmaker': 'bet365', 'odds': 2.1},
                    'draw': {'bookmaker': 'williamhill', 'odds': 3.6},
                    'away': {'bookmaker': 'betfair', 'odds': 4.5}
                }
            }
        
        Returns:
            Dict or None: Arbitrage 정보
        """
        best_odds = match_analysis.get('best_odds')
        
        if not best_odds or len(best_odds) != 3:
            return None
        
        # 각 결과의 최고 배당률
        home_odds = best_odds.get('home', {}).get('odds')
        draw_odds = best_odds.get('draw', {}).get('odds')
        away_odds = best_odds.get('away', {}).get('odds')
        
        if not all([home_odds, draw_odds, away_odds]):
            return None
        
        # Arbitrage percentage 계산
        arb_percentage = (
            (1 / home_odds) +
            (1 / draw_odds) +
            (1 / away_odds)
        )
        
        # Arbitrage 존재?
        if arb_percentage >= 1.0:
            return None
        
        # 수익률
        profit_margin = 1.0 - arb_percentage
        
        # 최소 수익률 이상?
        if profit_margin < self.min_profit:
            return None
        
        # Arbitrage 기회 발견!
        return {
            'match_id': match_analysis['match_id'],
            'home_team': match_analysis['home_team'],
            'away_team': match_analysis['away_team'],
            'arb_percentage': arb_percentage,
            'profit_margin': profit_margin,
            'best_odds': {
                'home': {
                    'bookmaker': best_odds['home']['bookmaker'],
                    'odds': home_odds
                },
                'draw': {
                    'bookmaker': best_odds['draw']['bookmaker'],
                    'odds': draw_odds
                },
                'away': {
                    'bookmaker': best_odds['away']['bookmaker'],
                    'odds': away_odds
                }
            },
            'stake_distribution': self._calculate_stakes(
                home_odds, draw_odds, away_odds, profit_margin
            ),
            'urgency': self._assess_urgency(profit_margin),
            'risk_level': self._assess_risk(best_odds),
            'detected_at': datetime.now()
        }
    
    def _calculate_stakes(
        self,
        home_odds: float,
        draw_odds: float,
        away_odds: float,
        profit_margin: float,
        total_stake: float = 100.0
    ) -> Dict[str, float]:
        """
        각 결과에 베팅할 금액 계산
        
        공식:
        - stake_home = (total_stake × (1/home_odds)) / (arb_percentage)
        - stake_draw = (total_stake × (1/draw_odds)) / (arb_percentage)
        - stake_away = (total_stake × (1/away_odds)) / (arb_percentage)
        
        Args:
            home_odds: 홈 배당률
            draw_odds: 무승부 배당률
            away_odds: 원정 배당률
            profit_margin: 수익률
            total_stake: 총 베팅 금액 (기본 100)
        
        Returns:
            Dict: {'home': 45.2, 'draw': 28.1, 'away': 22.4, 'total': 95.7, 'profit': 4.3}
        """
        arb_percentage = 1.0 - profit_margin
        
        stake_home = (total_stake * (1 / home_odds)) / arb_percentage
        stake_draw = (total_stake * (1 / draw_odds)) / arb_percentage
        stake_away = (total_stake * (1 / away_odds)) / arb_percentage
        
        total_invested = stake_home + stake_draw + stake_away
        guaranteed_return = total_stake
        guaranteed_profit = guaranteed_return - total_invested
        
        return {
            'home': round(stake_home, 2),
            'draw': round(stake_draw, 2),
            'away': round(stake_away, 2),
            'total_invested': round(total_invested, 2),
            'guaranteed_return': round(guaranteed_return, 2),
            'guaranteed_profit': round(guaranteed_profit, 2),
            'roi': round((guaranteed_profit / total_invested) * 100, 2)
        }
    
    def _assess_urgency(self, profit_margin: float) -> str:
        """
        긴급도 평가
        
        수익률이 높을수록 빨리 사라질 가능성 높음
        
        Args:
            profit_margin: 수익률
        
        Returns:
            str: 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
        """
        if profit_margin >= 0.03:  # 3% 이상
            return 'CRITICAL'  # 즉시 실행
        elif profit_margin >= 0.015:  # 1.5% 이상
            return 'HIGH'  # 빨리 실행
        elif profit_margin >= 0.01:  # 1% 이상
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _assess_risk(self, best_odds: Dict) -> str:
        """
        리스크 평가
        
        고려사항:
        1. 북메이커 수 (많을수록 리스크 상승)
        2. 북메이커 종류 (마이너 북메이커는 베팅 제한 위험)
        
        Args:
            best_odds: 최고 배당률 정보
        
        Returns:
            str: 'HIGH', 'MEDIUM', 'LOW'
        """
        # 서로 다른 북메이커 수
        bookmakers = set()
        for outcome, info in best_odds.items():
            bookmakers.add(info['bookmaker'])
        
        num_bookies = len(bookmakers)
        
        # 3개 북메이커 = 각각 다른 곳에 베팅 → 리스크 높음
        if num_bookies == 3:
            return 'HIGH'
        # 2개 북메이커 = 중간 리스크
        elif num_bookies == 2:
            return 'MEDIUM'
        # 1개 북메이커 = 낮은 리스크 (동일한 곳에서 모두 가능)
        else:
            return 'LOW'
    
    def calculate_arbitrage_from_raw_odds(
        self,
        bookmakers_odds: Dict[str, Dict[str, float]]
    ) -> Optional[Dict]:
        """
        원본 배당률 데이터에서 직접 arbitrage 계산
        
        Args:
            bookmakers_odds: {
                'bet365': {'home': 2.0, 'draw': 3.5, 'away': 4.0},
                'pinnacle': {'home': 2.1, 'draw': 3.4, 'away': 3.9}
            }
        
        Returns:
            Dict or None: Arbitrage 정보
        """
        # 각 결과의 최고 배당률 찾기
        best_home_bookie, best_home_odds = get_best_odds(bookmakers_odds, 'home')
        best_draw_bookie, best_draw_odds = get_best_odds(bookmakers_odds, 'draw')
        best_away_bookie, best_away_odds = get_best_odds(bookmakers_odds, 'away')
        
        if not all([best_home_odds, best_draw_odds, best_away_odds]):
            return None
        
        # Arbitrage percentage
        arb_percentage = (
            (1 / best_home_odds) +
            (1 / best_draw_odds) +
            (1 / best_away_odds)
        )
        
        if arb_percentage >= 1.0:
            return None
        
        profit_margin = 1.0 - arb_percentage
        
        if profit_margin < self.min_profit:
            return None
        
        return {
            'arb_percentage': arb_percentage,
            'profit_margin': profit_margin,
            'best_odds': {
                'home': {'bookmaker': best_home_bookie, 'odds': best_home_odds},
                'draw': {'bookmaker': best_draw_bookie, 'odds': best_draw_odds},
                'away': {'bookmaker': best_away_bookie, 'odds': best_away_odds}
            },
            'stake_distribution': self._calculate_stakes(
                best_home_odds, best_draw_odds, best_away_odds, profit_margin
            )
        }
