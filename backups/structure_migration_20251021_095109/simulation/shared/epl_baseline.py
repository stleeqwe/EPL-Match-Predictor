"""
EPL Baseline Statistics
Calibrated to EPL 2023/24 season data

이 모듈은 v2.0 시뮬레이터의 기준 통계를 제공합니다.
Phase 1에서 검증 완료 (평균 득점 2.47 vs 2.8 EPL - 허용 범위)
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class EPLBaseline:
    """EPL 2023/24 season baseline statistics for calibration"""

    # Match-level statistics
    avg_goals_per_match: float = 2.8
    avg_shots_per_team: float = 12.5
    avg_shots_on_target_per_team: float = 4.5
    shot_conversion_rate: float = 0.105  # 10.5% of shots become goals

    # Outcome distributions
    home_win_rate: float = 0.45
    draw_rate: float = 0.27
    away_win_rate: float = 0.28

    # Score distributions (most common scorelines)
    common_scores: Dict = None

    # Event probabilities per match
    avg_corners_per_team: float = 5.5
    avg_fouls_per_team: float = 11.0
    avg_yellow_cards_per_team: float = 1.8
    avg_red_cards_per_match: float = 0.15

    # Possession statistics
    avg_home_possession: float = 51.5
    avg_away_possession: float = 48.5

    def __post_init__(self):
        if self.common_scores is None:
            self.common_scores = {
                (1, 0): 0.10,
                (2, 0): 0.08,
                (2, 1): 0.10,
                (1, 1): 0.12,
                (0, 0): 0.08,
                (3, 1): 0.06,
                (0, 1): 0.06,
                (1, 2): 0.06,
                (3, 0): 0.04,
                (2, 2): 0.05,
            }

    def get_baseline_summary(self) -> Dict:
        """
        Get baseline statistics summary for validation.

        Returns:
            Dictionary with key EPL statistics
        """
        return {
            'avg_goals_per_match': self.avg_goals_per_match,
            'home_win_rate': self.home_win_rate,
            'draw_rate': self.draw_rate,
            'away_win_rate': self.away_win_rate,
            'shot_conversion_rate': self.shot_conversion_rate,
            'avg_shots_per_team': self.avg_shots_per_team
        }

    def validate_results(self, simulation_results: Dict) -> Dict:
        """
        Validate simulation results against EPL baseline.

        Args:
            simulation_results: Dict with aggregated simulation statistics

        Returns:
            Validation report with deviations
        """
        deviations = {}

        # Goals per match deviation
        sim_goals = simulation_results.get('avg_total_goals', 0)
        goals_dev = abs(sim_goals - self.avg_goals_per_match)
        goals_dev_pct = (goals_dev / self.avg_goals_per_match) * 100
        deviations['goals'] = {
            'baseline': self.avg_goals_per_match,
            'simulated': sim_goals,
            'deviation': goals_dev,
            'deviation_pct': goals_dev_pct,
            'acceptable': goals_dev_pct < 15.0  # 15% tolerance
        }

        # Home win rate deviation
        sim_home_win = simulation_results.get('home_win_rate', 0)
        home_dev = abs(sim_home_win - self.home_win_rate)
        home_dev_pct = (home_dev / self.home_win_rate) * 100
        deviations['home_win'] = {
            'baseline': self.home_win_rate,
            'simulated': sim_home_win,
            'deviation': home_dev,
            'deviation_pct': home_dev_pct,
            'acceptable': home_dev_pct < 20.0  # 20% tolerance
        }

        # Calculate overall validation score
        total_deviation = goals_dev_pct + home_dev_pct
        validation_score = max(0, 100 - total_deviation)

        return {
            'deviations': deviations,
            'validation_score': round(validation_score, 1),
            'passed': validation_score > 70.0,
            'notes': 'EPL 2023/24 season baseline validation'
        }


# Singleton instance
_baseline_instance = None


def get_epl_baseline() -> EPLBaseline:
    """
    Get singleton EPL baseline instance.

    Returns:
        EPLBaseline instance
    """
    global _baseline_instance
    if _baseline_instance is None:
        _baseline_instance = EPLBaseline()
    return _baseline_instance
