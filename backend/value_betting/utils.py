"""
Utility functions for value betting calculations
"""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


def decimal_to_probability(decimal_odds: float) -> float:
    """
    Decimal 배당률을 암시 확률로 변환
    
    Args:
        decimal_odds: Decimal 형식 배당률 (예: 2.00)
    
    Returns:
        float: 암시 확률 (0~1)
    
    Example:
        >>> decimal_to_probability(2.00)
        0.5  # 50% 확률
    """
    if decimal_odds <= 1.0:
        raise ValueError(f"Invalid decimal odds: {decimal_odds}. Must be > 1.0")
    
    return 1.0 / decimal_odds


def probability_to_decimal(probability: float) -> float:
    """
    확률을 Decimal 배당률로 변환
    
    Args:
        probability: 확률 (0~1)
    
    Returns:
        float: Decimal 배당률
    
    Example:
        >>> probability_to_decimal(0.5)
        2.00
    """
    if probability <= 0 or probability >= 1:
        raise ValueError(f"Invalid probability: {probability}. Must be between 0 and 1")
    
    return 1.0 / probability


def calculate_overround(odds_dict: Dict[str, float]) -> float:
    """
    Overround (마진) 계산
    
    북메이커의 마진 = 모든 결과의 암시 확률 합 - 1
    
    Args:
        odds_dict: {'home': 2.0, 'draw': 3.5, 'away': 4.0}
    
    Returns:
        float: Overround (예: 0.05 = 5% 마진)
    
    Example:
        >>> calculate_overround({'home': 2.0, 'draw': 3.5, 'away': 4.0})
        0.071  # 7.1% 마진
    """
    total_probability = sum(decimal_to_probability(odds) for odds in odds_dict.values())
    overround = total_probability - 1.0
    
    return overround


def remove_overround(odds_dict: Dict[str, float]) -> Dict[str, float]:
    """
    Overround를 제거하여 진짜 확률 계산
    
    Args:
        odds_dict: 북메이커 배당률
    
    Returns:
        Dict[str, float]: Overround 제거된 "진짜" 확률
    
    Example:
        >>> remove_overround({'home': 2.0, 'draw': 3.5, 'away': 4.0})
        {'home': 0.467, 'draw': 0.267, 'away': 0.233}
    """
    # 암시 확률 계산
    implied_probs = {
        outcome: decimal_to_probability(odds)
        for outcome, odds in odds_dict.items()
    }
    
    # 총합 (1보다 큼 → overround 존재)
    total = sum(implied_probs.values())
    
    # 정규화 (총합 = 1)
    true_probs = {
        outcome: prob / total
        for outcome, prob in implied_probs.items()
    }
    
    return true_probs


def calculate_expected_value(
    win_probability: float,
    decimal_odds: float
) -> float:
    """
    Expected Value (기댓값) 계산
    
    EV = (확률 × 배당률) - 1
    
    Args:
        win_probability: 승리 확률 (0~1)
        decimal_odds: Decimal 배당률
    
    Returns:
        float: Expected Value (양수면 가치 있음)
    
    Example:
        >>> calculate_expected_value(0.6, 2.0)
        0.2  # 20% positive EV
    """
    ev = (win_probability * decimal_odds) - 1.0
    return ev


def calculate_edge(
    estimated_probability: float,
    decimal_odds: float
) -> float:
    """
    Edge (우위) 계산
    
    Edge = (추정 확률 × 배당률 - 1) × 100
    
    Args:
        estimated_probability: 추정한 진짜 확률
        decimal_odds: 북메이커 배당률
    
    Returns:
        float: Edge (퍼센트, 양수면 가치 있음)
    
    Example:
        >>> calculate_edge(0.55, 2.0)
        10.0  # 10% edge
    """
    edge = (estimated_probability * decimal_odds - 1) * 100
    return edge


def get_best_odds(
    bookmakers_odds: Dict[str, Dict[str, float]],
    outcome: str
) -> tuple[Optional[str], Optional[float]]:
    """
    특정 결과에 대한 최고 배당률 찾기
    
    Args:
        bookmakers_odds: {
            'bet365': {'home': 2.0, 'draw': 3.5, 'away': 4.0},
            'pinnacle': {'home': 2.1, 'draw': 3.4, 'away': 3.9}
        }
        outcome: 'home', 'draw', 또는 'away'
    
    Returns:
        tuple: (북메이커명, 최고 배당률)
    
    Example:
        >>> get_best_odds(bookmakers_odds, 'home')
        ('pinnacle', 2.1)
    """
    best_bookie = None
    best_odds = 0.0
    
    for bookie, odds in bookmakers_odds.items():
        if outcome in odds and odds[outcome] > best_odds:
            best_odds = odds[outcome]
            best_bookie = bookie
    
    if best_bookie is None:
        return None, None
    
    return best_bookie, best_odds


def calculate_implied_probability_from_multiple_bookies(
    bookmakers_odds: Dict[str, Dict[str, float]],
    outcome: str,
    method: str = 'average'
) -> Optional[float]:
    """
    여러 북메이커의 배당률에서 합의 확률 계산
    
    Args:
        bookmakers_odds: 북메이커별 배당률
        outcome: 'home', 'draw', 또는 'away'
        method: 'average', 'median', 'best' (최고 배당률)
    
    Returns:
        float: 합의 확률
    """
    probabilities = []
    
    for bookie, odds in bookmakers_odds.items():
        if outcome in odds:
            # Overround 제거
            true_probs = remove_overround(odds)
            probabilities.append(true_probs[outcome])
    
    if not probabilities:
        return None
    
    if method == 'average':
        return sum(probabilities) / len(probabilities)
    elif method == 'median':
        sorted_probs = sorted(probabilities)
        mid = len(sorted_probs) // 2
        if len(sorted_probs) % 2 == 0:
            return (sorted_probs[mid - 1] + sorted_probs[mid]) / 2
        else:
            return sorted_probs[mid]
    elif method == 'best':
        # 최고 배당률 → 최저 확률
        return min(probabilities)
    else:
        raise ValueError(f"Invalid method: {method}")


def validate_probabilities(probabilities: Dict[str, float]) -> bool:
    """
    확률 유효성 검증
    
    Args:
        probabilities: {'home': 0.5, 'draw': 0.3, 'away': 0.2}
    
    Returns:
        bool: 유효하면 True
    
    Raises:
        ValueError: 확률이 유효하지 않으면
    """
    # 모든 확률이 0~1 사이인지
    for outcome, prob in probabilities.items():
        if prob < 0 or prob > 1:
            raise ValueError(f"Invalid probability for {outcome}: {prob}")
    
    # 합이 대략 1인지 (오차 허용)
    total = sum(probabilities.values())
    if abs(total - 1.0) > 0.01:
        logger.warning(f"Probabilities sum to {total:.3f}, not 1.0")
    
    return True
