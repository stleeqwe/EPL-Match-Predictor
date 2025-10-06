"""
Value Betting Module
배당률 기반 가치 베팅 시스템

주요 기능:
1. Value Detector - Pinnacle 대비 Edge 계산 및 Value Bet 탐지
2. Arbitrage Finder - 북메이커 간 차익거래 기회 탐지
3. Kelly Criterion - 최적 베팅 금액 계산

학술적 근거:
- Constantinou & Fenton (2012): 북메이커 배당률이 통계 모델보다 정확
- Kelly (1956): 최적 자금 관리 공식
- Dixon & Coles (1997): 축구 득점 예측 모델 (비교용)
"""

from .value_detector import ValueDetector
from .arbitrage_finder import ArbitrageFinder
from .kelly_criterion import KellyCriterion

__version__ = '2.0.0'
__all__ = ['ValueDetector', 'ArbitrageFinder', 'KellyCriterion']
