"""
Kelly Criterion - 최적 베팅 금액 계산기

학술적 근거:
- Kelly (1956): "A New Interpretation of Information Rate"
- 장기적으로 자금을 극대화하는 최적 베팅 비율
- 과도한 위험 방지

Kelly Formula:
f* = (bp - q) / b

여기서:
- f* = 베팅할 자금 비율
- b = 순이익 배당률 (decimal_odds - 1)
- p = 승리 확률
- q = 패배 확률 (1 - p)

예시:
- 확률 60%, 배당률 2.0
- f* = (1.0 × 0.6 - 0.4) / 1.0 = 0.2 (20% 베팅)

Fractional Kelly:
- Full Kelly는 공격적 → 변동성 큼
- Half Kelly (f*/2) 권장 → 안정적
- Quarter Kelly (f*/4) 매우 보수적
"""

from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

from .exceptions import InvalidBankrollError, InvalidProbabilityError

logger = logging.getLogger(__name__)


class KellyCriterion:
    """
    Kelly Criterion 계산기
    
    기능:
    1. 단일 베팅의 최적 금액 계산
    2. 포트폴리오 배분 (여러 베팅)
    3. 시뮬레이션
    
    Attributes:
        fraction (float): Kelly 비율 (1.0=Full, 0.5=Half, 0.25=Quarter)
        max_bet (float): 최대 베팅 비율 (예: 0.05 = 5%)
    """
    
    def __init__(
        self,
        fraction: float = 0.25,
        max_bet: float = 0.05
    ):
        """
        Args:
            fraction: Kelly fraction (0.25 = Quarter Kelly 권장)
            max_bet: 최대 베팅 비율 (5% 권장)
        """
        if fraction <= 0 or fraction > 1:
            raise ValueError(f"Invalid fraction: {fraction}. Must be 0 < fraction <= 1")
        
        if max_bet <= 0 or max_bet > 1:
            raise ValueError(f"Invalid max_bet: {max_bet}. Must be 0 < max_bet <= 1")
        
        self.fraction = fraction
        self.max_bet = max_bet
        
        kelly_type = {
            1.0: 'Full Kelly',
            0.5: 'Half Kelly',
            0.25: 'Quarter Kelly'
        }.get(fraction, f'{fraction:.0%} Kelly')
        
        logger.info(
            f"KellyCriterion initialized: {kelly_type}, "
            f"max_bet={max_bet:.1%}"
        )
    
    def calculate_kelly(
        self,
        win_probability: float,
        decimal_odds: float
    ) -> float:
        """
        Kelly 베팅 비율 계산
        
        Args:
            win_probability: 승리 확률 (0~1)
            decimal_odds: Decimal 배당률 (예: 2.0)
        
        Returns:
            float: 베팅할 자금 비율 (0~1)
        
        Raises:
            InvalidProbabilityError: 확률이 유효하지 않으면
        
        Example:
            >>> kelly = KellyCriterion(fraction=0.5)
            >>> kelly.calculate_kelly(0.6, 2.0)
            0.1  # 10% 베팅 (Half Kelly)
        """
        # 입력 검증
        if win_probability <= 0 or win_probability >= 1:
            raise InvalidProbabilityError(
                f"Invalid win_probability: {win_probability}. Must be 0 < p < 1"
            )
        
        if decimal_odds <= 1.0:
            raise ValueError(
                f"Invalid decimal_odds: {decimal_odds}. Must be > 1.0"
            )
        
        # Kelly formula
        # f* = (bp - q) / b
        # 여기서 b = decimal_odds - 1 (순이익)
        b = decimal_odds - 1.0  # 순이익 배당률
        p = win_probability
        q = 1.0 - p  # 패배 확률
        
        kelly_percent = (b * p - q) / b
        
        # 음수면 베팅하지 않음
        if kelly_percent <= 0:
            logger.warning(
                f"Negative Kelly: {kelly_percent:.2%}. "
                f"Probability {p:.1%} too low for odds {decimal_odds:.2f}"
            )
            return 0.0
        
        # Fractional Kelly 적용
        adjusted_kelly = kelly_percent * self.fraction
        
        # 최대 베팅 제한
        final_kelly = min(adjusted_kelly, self.max_bet)
        
        if adjusted_kelly > self.max_bet:
            logger.info(
                f"Kelly {adjusted_kelly:.2%} capped at max_bet {self.max_bet:.1%}"
            )
        
        return final_kelly
    
    def calculate_bet_amount(
        self,
        win_probability: float,
        decimal_odds: float,
        bankroll: float
    ) -> Dict[str, float]:
        """
        실제 베팅 금액 계산
        
        Args:
            win_probability: 승리 확률
            decimal_odds: 배당률
            bankroll: 총 자금
        
        Returns:
            Dict: {
                'kelly_percent': 0.1,
                'bet_amount': 100.0,
                'potential_profit': 100.0,
                'potential_loss': 100.0,
                'expected_value': 20.0
            }
        """
        if bankroll <= 0:
            raise InvalidBankrollError(f"Invalid bankroll: {bankroll}. Must be > 0")
        
        kelly_percent = self.calculate_kelly(win_probability, decimal_odds)
        bet_amount = bankroll * kelly_percent
        
        # 수익/손실
        potential_profit = bet_amount * (decimal_odds - 1)
        potential_loss = bet_amount
        
        # Expected Value
        ev = (win_probability * potential_profit) - ((1 - win_probability) * potential_loss)
        
        return {
            'kelly_percent': kelly_percent,
            'bet_amount': round(bet_amount, 2),
            'potential_profit': round(potential_profit, 2),
            'potential_loss': round(potential_loss, 2),
            'expected_value': round(ev, 2),
            'bankroll_after_win': round(bankroll + potential_profit, 2),
            'bankroll_after_loss': round(bankroll - potential_loss, 2)
        }
    
    def calculate_bankroll_allocation(
        self,
        value_bets: List[Dict],
        bankroll: float
    ) -> Dict:
        """
        여러 베팅에 자금 배분
        
        Strategy:
        1. 각 베팅의 Kelly 비율 계산
        2. 총 Kelly 비율이 1.0 초과하면 정규화
        3. 실제 베팅 금액 계산
        
        Args:
            value_bets: ValueDetector.detect_value_bets() 결과
            bankroll: 총 자금
        
        Returns:
            Dict: 베팅 계획
        """
        if bankroll <= 0:
            raise InvalidBankrollError(f"Invalid bankroll: {bankroll}")
        
        if not value_bets:
            return {
                'total_bets': 0,
                'total_kelly_percent': 0,
                'total_bet_amount': 0,
                'allocations': [],
                'expected_roi': 0
            }
        
        allocations = []
        total_kelly = 0.0
        
        # 1. 각 베팅의 Kelly 비율 계산
        for bet in value_bets:
            kelly_percent = self.calculate_kelly(
                bet['estimated_probability'],
                bet['odds']
            )
            
            allocations.append({
                **bet,
                'kelly_percent': kelly_percent,
                'raw_bet_amount': bankroll * kelly_percent
            })
            
            total_kelly += kelly_percent
        
        # 2. 총 Kelly가 1.0 초과하면 정규화
        if total_kelly > 1.0:
            logger.warning(
                f"Total Kelly {total_kelly:.1%} exceeds 100%. "
                f"Normalizing allocations."
            )
            
            normalization_factor = 1.0 / total_kelly
            
            for allocation in allocations:
                allocation['kelly_percent'] *= normalization_factor
                allocation['raw_bet_amount'] *= normalization_factor
        
        # 3. 실제 베팅 금액 및 통계
        total_bet_amount = 0.0
        total_ev = 0.0
        
        for allocation in allocations:
            bet_amount = allocation['raw_bet_amount']
            odds = allocation['odds']
            prob = allocation['estimated_probability']
            
            potential_profit = bet_amount * (odds - 1)
            potential_loss = bet_amount
            ev = (prob * potential_profit) - ((1 - prob) * potential_loss)
            
            allocation['bet_amount'] = round(bet_amount, 2)
            allocation['potential_profit'] = round(potential_profit, 2)
            allocation['expected_value'] = round(ev, 2)
            
            total_bet_amount += bet_amount
            total_ev += ev
        
        # 정렬 (베팅 금액 큰 순)
        allocations.sort(key=lambda x: x['bet_amount'], reverse=True)
        
        return {
            'total_bets': len(allocations),
            'total_kelly_percent': min(total_kelly, 1.0),
            'total_bet_amount': round(total_bet_amount, 2),
            'remaining_bankroll': round(bankroll - total_bet_amount, 2),
            'allocations': allocations,
            'expected_total_ev': round(total_ev, 2),
            'expected_roi': round((total_ev / total_bet_amount) * 100, 2) if total_bet_amount > 0 else 0
        }
    
    def simulate_kelly_growth(
        self,
        win_probability: float,
        decimal_odds: float,
        initial_bankroll: float,
        num_bets: int = 100
    ) -> Dict:
        """
        Kelly 전략 시뮬레이션
        
        Args:
            win_probability: 승리 확률
            decimal_odds: 배당률
            initial_bankroll: 초기 자금
            num_bets: 시뮬레이션 베팅 횟수
        
        Returns:
            Dict: 시뮬레이션 결과
        """
        import random
        
        kelly_percent = self.calculate_kelly(win_probability, decimal_odds)
        
        bankroll = initial_bankroll
        history = [bankroll]
        
        wins = 0
        losses = 0
        
        for _ in range(num_bets):
            bet_amount = bankroll * kelly_percent
            
            # 승/패 시뮬레이션
            if random.random() < win_probability:
                # 승리
                profit = bet_amount * (decimal_odds - 1)
                bankroll += profit
                wins += 1
            else:
                # 패배
                bankroll -= bet_amount
                losses += 1
            
            history.append(bankroll)
            
            # 파산 방지
            if bankroll <= 0:
                logger.warning("Bankroll depleted in simulation")
                break
        
        return {
            'initial_bankroll': initial_bankroll,
            'final_bankroll': round(bankroll, 2),
            'total_return': round(bankroll - initial_bankroll, 2),
            'roi': round(((bankroll - initial_bankroll) / initial_bankroll) * 100, 2),
            'num_bets': len(history) - 1,
            'wins': wins,
            'losses': losses,
            'win_rate': round(wins / (wins + losses) * 100, 2) if (wins + losses) > 0 else 0,
            'kelly_percent': kelly_percent,
            'bankroll_history': history
        }
    
    def compare_strategies(
        self,
        win_probability: float,
        decimal_odds: float,
        bankroll: float,
        num_simulations: int = 1000,
        num_bets_per_sim: int = 100
    ) -> Dict:
        """
        다양한 Kelly 전략 비교
        
        Args:
            win_probability: 승리 확률
            decimal_odds: 배당률
            bankroll: 초기 자금
            num_simulations: 시뮬레이션 횟수
            num_bets_per_sim: 각 시뮬레이션의 베팅 횟수
        
        Returns:
            Dict: 전략별 평균 결과
        """
        strategies = {
            'Full Kelly': 1.0,
            'Half Kelly': 0.5,
            'Quarter Kelly': 0.25,
            'Fixed 5%': None  # Kelly가 아닌 고정 비율
        }
        
        results = {}
        
        for strategy_name, fraction in strategies.items():
            if fraction is not None:
                calculator = KellyCriterion(fraction=fraction, max_bet=self.max_bet)
            
            final_bankrolls = []
            
            for _ in range(num_simulations):
                if fraction is not None:
                    sim_result = calculator.simulate_kelly_growth(
                        win_probability, decimal_odds, bankroll, num_bets_per_sim
                    )
                else:
                    # Fixed 5% 전략
                    sim_result = self._simulate_fixed_percent(
                        win_probability, decimal_odds, bankroll, num_bets_per_sim, 0.05
                    )
                
                final_bankrolls.append(sim_result['final_bankroll'])
            
            avg_final = sum(final_bankrolls) / len(final_bankrolls)
            avg_roi = ((avg_final - bankroll) / bankroll) * 100
            
            results[strategy_name] = {
                'avg_final_bankroll': round(avg_final, 2),
                'avg_roi': round(avg_roi, 2),
                'best_case': round(max(final_bankrolls), 2),
                'worst_case': round(min(final_bankrolls), 2)
            }
        
        return results
    
    def _simulate_fixed_percent(
        self,
        win_probability: float,
        decimal_odds: float,
        initial_bankroll: float,
        num_bets: int,
        fixed_percent: float
    ) -> Dict:
        """고정 비율 전략 시뮬레이션 (비교용)"""
        import random
        
        bankroll = initial_bankroll
        wins = 0
        losses = 0
        
        for _ in range(num_bets):
            bet_amount = bankroll * fixed_percent
            
            if random.random() < win_probability:
                profit = bet_amount * (decimal_odds - 1)
                bankroll += profit
                wins += 1
            else:
                bankroll -= bet_amount
                losses += 1
            
            if bankroll <= 0:
                break
        
        return {
            'final_bankroll': bankroll,
            'wins': wins,
            'losses': losses
        }
