"""
Narrative Analyzer v2.0
Analyzes alignment between expected scenario and simulation results

핵심 기능:
1. 예상 시나리오 정의
2. 시뮬레이션 결과와 비교
3. 서사 일치율 계산
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class NarrativeAnalyzer:
    """
    Analyzes narrative alignment between expectations and results.

    Scenarios:
    - balanced_standard: 균형잡힌 일반적 경기
    - high_tempo_low_scoring: 치열하지만 저득점
    - high_scoring: 양팀 다득점
    - defensive_low_scoring: 수비적 저득점
    - one_sided_domination: 일방적 우세
    """

    def __init__(self):
        """Initialize narrative analyzer."""
        self.scenario_definitions = self._define_scenarios()
        logger.info("NarrativeAnalyzer initialized")

    def analyze(
        self,
        simulation_results: Dict,
        expected_scenario: str
    ) -> Dict:
        """
        Analyze narrative alignment.

        Args:
            simulation_results: Aggregated simulation results
            expected_scenario: Expected match scenario from AI

        Returns:
            Narrative analysis report:
            {
                'expected_scenario': str,
                'narrative_alignment': float (0-100, 100=perfect match),
                'misalignments': list of discrepancies,
                'assessment': str
            }
        """
        logger.info(f"Analyzing narrative alignment for scenario: {expected_scenario}")

        if expected_scenario not in self.scenario_definitions:
            logger.warning(f"Unknown scenario: {expected_scenario}, using balanced_standard")
            expected_scenario = 'balanced_standard'

        # Get scenario expectations
        expectations = self.scenario_definitions[expected_scenario]

        # Check alignment for each aspect
        misalignments = []
        alignment_scores = []

        # Check goal total alignment
        goal_align, goal_issues = self._check_goal_alignment(
            simulation_results,
            expectations
        )
        alignment_scores.append(goal_align)
        misalignments.extend(goal_issues)

        # Check outcome distribution alignment
        outcome_align, outcome_issues = self._check_outcome_alignment(
            simulation_results,
            expectations
        )
        alignment_scores.append(outcome_align)
        misalignments.extend(outcome_issues)

        # Check tempo alignment
        tempo_align, tempo_issues = self._check_tempo_alignment(
            simulation_results,
            expectations
        )
        alignment_scores.append(tempo_align)
        misalignments.extend(tempo_issues)

        # Calculate overall alignment
        overall_alignment = sum(alignment_scores) / len(alignment_scores)

        # Assessment
        if overall_alignment > 85.0:
            assessment = "excellent"
        elif overall_alignment > 70.0:
            assessment = "good"
        elif overall_alignment > 50.0:
            assessment = "acceptable"
        else:
            assessment = "poor"

        result = {
            'expected_scenario': expected_scenario,
            'narrative_alignment': round(overall_alignment, 2),
            'misalignments': misalignments,
            'assessment': assessment
        }

        logger.info(f"Narrative analysis complete: alignment={overall_alignment:.2f}%")
        return result

    def _define_scenarios(self) -> Dict:
        """
        Define scenario expectations.

        Returns:
            Dictionary of scenario definitions
        """
        return {
            'balanced_standard': {
                'name': '균형잡힌 일반적 경기',
                'expected_goals': (2.5, 3.0),  # Range
                'expected_home_win': (0.40, 0.50),
                'expected_shots': (11, 14),
                'expected_tempo': 'medium'
            },
            'high_tempo_low_scoring': {
                'name': '치열하지만 저득점',
                'expected_goals': (1.5, 2.5),
                'expected_home_win': (0.35, 0.55),
                'expected_shots': (14, 18),
                'expected_tempo': 'high'
            },
            'high_scoring': {
                'name': '양팀 다득점',
                'expected_goals': (3.5, 5.0),
                'expected_home_win': (0.35, 0.50),
                'expected_shots': (13, 17),
                'expected_tempo': 'high'
            },
            'defensive_low_scoring': {
                'name': '수비적 저득점',
                'expected_goals': (1.0, 2.0),
                'expected_home_win': (0.35, 0.45),
                'expected_shots': (8, 12),
                'expected_tempo': 'low'
            },
            'one_sided_domination': {
                'name': '일방적 우세',
                'expected_goals': (2.5, 4.0),
                'expected_home_win': (0.65, 0.85),
                'expected_shots': (12, 16),
                'expected_tempo': 'medium'
            }
        }

    def _check_goal_alignment(
        self,
        results: Dict,
        expectations: Dict
    ) -> tuple:
        """
        Check goal total alignment.

        Returns:
            Tuple of (alignment_score, issues_list)
        """
        expected_goals = results.get('expected_goals', {})
        total_goals = expected_goals.get('home', 1.4) + expected_goals.get('away', 1.4)

        expected_range = expectations['expected_goals']
        min_goals, max_goals = expected_range

        if min_goals <= total_goals <= max_goals:
            # Perfect alignment
            alignment_score = 100.0
            issues = []
        else:
            # Calculate deviation
            if total_goals < min_goals:
                deviation = min_goals - total_goals
                description = f"평균 득점 {total_goals:.2f}, 예상 범위 {min_goals}-{max_goals}골 (과소)"
            else:
                deviation = total_goals - max_goals
                description = f"평균 득점 {total_goals:.2f}, 예상 범위 {min_goals}-{max_goals}골 (과다)"

            # Score decreases with deviation
            alignment_score = max(0, 100 - (deviation / max_goals * 100))

            issues = [{
                'type': 'goal_misalignment',
                'description': description,
                'deviation': round(deviation, 2)
            }]

        return alignment_score, issues

    def _check_outcome_alignment(
        self,
        results: Dict,
        expectations: Dict
    ) -> tuple:
        """
        Check outcome probability alignment.

        Returns:
            Tuple of (alignment_score, issues_list)
        """
        probabilities = results.get('probabilities', {})
        home_win_prob = probabilities.get('home_win', 0.45)

        expected_range = expectations['expected_home_win']
        min_prob, max_prob = expected_range

        if min_prob <= home_win_prob <= max_prob:
            alignment_score = 100.0
            issues = []
        else:
            if home_win_prob < min_prob:
                deviation = min_prob - home_win_prob
                description = f"홈 승률 {home_win_prob:.1%}, 예상 범위 {min_prob:.0%}-{max_prob:.0%} (낮음)"
            else:
                deviation = home_win_prob - max_prob
                description = f"홈 승률 {home_win_prob:.1%}, 예상 범위 {min_prob:.0%}-{max_prob:.0%} (높음)"

            alignment_score = max(0, 100 - (deviation * 200))

            issues = [{
                'type': 'outcome_misalignment',
                'description': description,
                'deviation': round(deviation, 3)
            }]

        return alignment_score, issues

    def _check_tempo_alignment(
        self,
        results: Dict,
        expectations: Dict
    ) -> tuple:
        """
        Check tempo/intensity alignment.

        Returns:
            Tuple of (alignment_score, issues_list)
        """
        events = results.get('events', {})
        avg_shots = (events.get('home_shots', 12) + events.get('away_shots', 12)) / 2

        expected_range = expectations['expected_shots']
        min_shots, max_shots = expected_range

        if min_shots <= avg_shots <= max_shots:
            alignment_score = 100.0
            issues = []
        else:
            if avg_shots < min_shots:
                deviation = min_shots - avg_shots
                description = f"평균 슈팅 {avg_shots:.1f}, 예상 {min_shots}-{max_shots} (낮음)"
            else:
                deviation = avg_shots - max_shots
                description = f"평균 슈팅 {avg_shots:.1f}, 예상 {min_shots}-{max_shots} (높음)"

            alignment_score = max(0, 100 - (deviation / max_shots * 100))

            issues = [{
                'type': 'tempo_misalignment',
                'description': description,
                'deviation': round(deviation, 1)
            }]

        return alignment_score, issues


def get_narrative_analyzer() -> NarrativeAnalyzer:
    """
    Get narrative analyzer instance.

    Returns:
        NarrativeAnalyzer instance
    """
    return NarrativeAnalyzer()
