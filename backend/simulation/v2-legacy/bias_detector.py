"""
Bias Detector v2.0
Statistical bias detection in simulation results

핵심 기능:
1. EPL baseline 대비 편향 감지
2. 이상치 탐지 (outlier detection)
3. 문제 유형 분류 및 심각도 평가
"""

import logging
from typing import Dict, List, Optional
from simulation.shared.epl_baseline import get_epl_baseline

logger = logging.getLogger(__name__)


class BiasDetector:
    """
    Detects statistical biases in simulation results.

    Compares simulation output against EPL baseline to identify:
    - Goal distribution skew
    - Unrealistic scorelines
    - Outcome probability deviation
    - Event frequency anomalies
    """

    def __init__(self):
        """Initialize bias detector."""
        self.baseline = get_epl_baseline()
        logger.info("BiasDetector initialized")

    def analyze(self, simulation_results: Dict) -> Dict:
        """
        Analyze simulation results for statistical biases.

        Args:
            simulation_results: Aggregated results from IterativeEngine

        Returns:
            Bias analysis report:
            {
                'bias_detected': bool,
                'bias_score': float (0-100, 0=perfect),
                'issues': list of detected issues,
                'overall_assessment': str
            }
        """
        logger.info("Analyzing simulation results for biases")

        issues = []

        # Check goal distribution
        goal_issues = self._check_goal_distribution(simulation_results)
        issues.extend(goal_issues)

        # Check outcome probabilities
        outcome_issues = self._check_outcome_probabilities(simulation_results)
        issues.extend(outcome_issues)

        # Check scoreline realism
        scoreline_issues = self._check_scoreline_realism(simulation_results)
        issues.extend(scoreline_issues)

        # Check event frequencies
        event_issues = self._check_event_frequencies(simulation_results)
        issues.extend(event_issues)

        # Calculate overall bias score
        bias_score = self._calculate_bias_score(issues)

        # Determine if bias detected
        bias_detected = bias_score > 5.0

        # Overall assessment
        if bias_score < 5.0:
            assessment = "excellent"
        elif bias_score < 10.0:
            assessment = "acceptable"
        elif bias_score < 20.0:
            assessment = "moderate_bias"
        else:
            assessment = "severe_bias"

        result = {
            'bias_detected': bias_detected,
            'bias_score': round(bias_score, 2),
            'issues': issues,
            'overall_assessment': assessment
        }

        logger.info(f"Bias analysis complete: score={bias_score:.2f}, detected={bias_detected}")
        return result

    def _check_goal_distribution(self, results: Dict) -> List[Dict]:
        """
        Check if goal distribution is realistic.

        Returns:
            List of detected issues
        """
        issues = []

        # Get average total goals
        expected_goals = results.get('expected_goals', {})
        home_goals = expected_goals.get('home', 1.4)
        away_goals = expected_goals.get('away', 1.4)
        total_goals = home_goals + away_goals

        # Check against baseline (2.8 goals/match)
        baseline_goals = self.baseline.avg_goals_per_match
        deviation = abs(total_goals - baseline_goals)
        deviation_pct = (deviation / baseline_goals) * 100

        if deviation_pct > 15.0:  # More than 15% deviation
            severity = "high" if deviation_pct > 25.0 else "medium"
            issues.append({
                'type': 'goal_distribution_skew',
                'severity': severity,
                'description': f"평균 득점 {total_goals:.2f}, EPL 기준 {baseline_goals} ({deviation_pct:.1f}% 편차)",
                'impact_score': min(deviation_pct, 30.0)
            })

        return issues

    def _check_outcome_probabilities(self, results: Dict) -> List[Dict]:
        """
        Check if outcome probabilities are realistic.

        Returns:
            List of detected issues
        """
        issues = []

        probabilities = results.get('probabilities', {})
        home_win = probabilities.get('home_win', 0.45)
        draw = probabilities.get('draw', 0.27)
        away_win = probabilities.get('away_win', 0.28)

        # Check home win rate deviation
        home_dev = abs(home_win - self.baseline.home_win_rate)
        home_dev_pct = (home_dev / self.baseline.home_win_rate) * 100

        if home_dev_pct > 30.0:  # More than 30% deviation from baseline
            severity = "high" if home_dev_pct > 50.0 else "medium"
            issues.append({
                'type': 'outcome_probability_deviation',
                'severity': severity,
                'description': f"홈 승률 {home_win:.1%}, EPL 기준 {self.baseline.home_win_rate:.1%} ({home_dev_pct:.1f}% 편차)",
                'impact_score': min(home_dev_pct / 2, 20.0)
            })

        # Check for extreme probabilities
        max_prob = max(home_win, draw, away_win)
        if max_prob > 0.85:
            issues.append({
                'type': 'extreme_probability',
                'severity': 'medium',
                'description': f"극단적 확률 {max_prob:.1%} (85% 초과)",
                'impact_score': (max_prob - 0.85) * 50
            })

        return issues

    def _check_scoreline_realism(self, results: Dict) -> List[Dict]:
        """
        Check if scorelines are realistic.

        Returns:
            List of detected issues
        """
        issues = []

        score_distribution = results.get('score_distribution', {})

        # Check for high-scoring matches (5+ goals)
        high_scoring_prob = 0.0
        for score_str, prob in score_distribution.items():
            try:
                home_g, away_g = map(int, score_str.split('-'))
                total_g = home_g + away_g
                if total_g >= 5:
                    high_scoring_prob += prob
            except:
                continue

        # EPL: high-scoring matches (5+ goals) occur ~15-20% of time
        if high_scoring_prob > 0.30:  # More than 30%
            issues.append({
                'type': 'unrealistic_high_scoring',
                'severity': 'medium',
                'description': f"고득점 경기 비율 {high_scoring_prob:.1%} (EPL: ~18%)",
                'impact_score': (high_scoring_prob - 0.20) * 40
            })

        # Check for unrealistic scorelines (6+ goals for one team)
        unrealistic_prob = 0.0
        for score_str, prob in score_distribution.items():
            try:
                home_g, away_g = map(int, score_str.split('-'))
                if home_g >= 6 or away_g >= 6:
                    unrealistic_prob += prob
            except:
                continue

        if unrealistic_prob > 0.05:  # More than 5%
            issues.append({
                'type': 'unrealistic_scoreline',
                'severity': 'high',
                'description': f"6골 이상 스코어 비율 {unrealistic_prob:.1%} (EPL: ~1%)",
                'impact_score': unrealistic_prob * 100
            })

        return issues

    def _check_event_frequencies(self, results: Dict) -> List[Dict]:
        """
        Check if event frequencies are realistic.

        Returns:
            List of detected issues
        """
        issues = []

        events = results.get('events', {})

        # Check shots
        home_shots = events.get('home_shots', 12.5)
        away_shots = events.get('away_shots', 12.5)
        avg_shots = (home_shots + away_shots) / 2

        if avg_shots < 8.0 or avg_shots > 18.0:
            severity = "medium" if 7.0 < avg_shots < 20.0 else "high"
            issues.append({
                'type': 'unrealistic_shot_frequency',
                'severity': severity,
                'description': f"평균 슈팅 {avg_shots:.1f}, EPL 기준 {self.baseline.avg_shots_per_team}",
                'impact_score': abs(avg_shots - self.baseline.avg_shots_per_team)
            })

        # Check possession balance
        home_poss = events.get('home_possession', 50)
        if home_poss > 75 or home_poss < 25:
            issues.append({
                'type': 'unrealistic_possession',
                'severity': 'medium',
                'description': f"홈 점유율 {home_poss:.1f}% (극단적)",
                'impact_score': abs(50 - home_poss) / 2
            })

        return issues

    def _calculate_bias_score(self, issues: List[Dict]) -> float:
        """
        Calculate overall bias score from detected issues.

        Args:
            issues: List of detected issues with impact scores

        Returns:
            Bias score (0-100, 0=perfect)
        """
        if not issues:
            return 0.0

        # Sum impact scores
        total_impact = sum(issue.get('impact_score', 0.0) for issue in issues)

        # Weight by severity
        severity_weights = {'low': 0.5, 'medium': 1.0, 'high': 2.0}
        weighted_impact = 0.0
        for issue in issues:
            severity = issue.get('severity', 'medium')
            impact = issue.get('impact_score', 0.0)
            weighted_impact += impact * severity_weights.get(severity, 1.0)

        # Normalize to 0-100 scale
        bias_score = min(weighted_impact, 100.0)

        return bias_score


def get_bias_detector() -> BiasDetector:
    """
    Get bias detector instance.

    Returns:
        BiasDetector instance
    """
    return BiasDetector()
