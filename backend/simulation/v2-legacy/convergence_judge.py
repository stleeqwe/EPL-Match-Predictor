"""
Convergence Judge v2.0
Determines if simulation results have converged

핵심 기능:
1. 편향 점수 및 서사 일치율 기반 수렴 판정
2. 반복 종료 조건 평가
3. 조기 종료 또는 계속 반복 결정
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class ConvergenceJudge:
    """
    Judges convergence of iterative simulation.

    Convergence criteria:
    - bias_score < 5.0 (excellent quality)
    - narrative_alignment > 85.0% (good scenario match)
    - iteration > 0 (at least one refinement)

    OR relaxed criteria after 5 iterations:
    - bias_score < 10.0
    - narrative_alignment > 75.0%
    """

    def __init__(self):
        """Initialize convergence judge."""
        # Strict convergence criteria (iterations 1-5)
        self.strict_bias_threshold = 5.0
        self.strict_narrative_threshold = 85.0

        # Relaxed convergence criteria (iterations 6+)
        self.relaxed_bias_threshold = 10.0
        self.relaxed_narrative_threshold = 75.0

        # Maximum iterations before forced termination
        self.max_iterations = 8

        logger.info("ConvergenceJudge initialized")

    def check_convergence(
        self,
        bias_score: float,
        narrative_alignment: float,
        iteration: int
    ) -> Dict:
        """
        Check if simulation has converged.

        Args:
            bias_score: Bias score from BiasDetector (0-100)
            narrative_alignment: Alignment from NarrativeAnalyzer (0-100)
            iteration: Current iteration number (0-based)

        Returns:
            Convergence report:
            {
                'converged': bool,
                'reason': str,
                'bias_score': float,
                'narrative_alignment': float,
                'iteration': int,
                'recommendation': str
            }
        """
        logger.info(f"Checking convergence: iteration={iteration}, bias={bias_score:.2f}, narrative={narrative_alignment:.2f}%")

        # Forced termination after max iterations
        if iteration >= self.max_iterations:
            return {
                'converged': True,
                'reason': f'max_iterations_reached (iteration {iteration})',
                'bias_score': bias_score,
                'narrative_alignment': narrative_alignment,
                'iteration': iteration,
                'recommendation': '최대 반복 횟수 도달. 현재 결과로 최종 시뮬레이션 진행'
            }

        # Determine thresholds based on iteration
        if iteration < 5:
            bias_threshold = self.strict_bias_threshold
            narrative_threshold = self.strict_narrative_threshold
            criteria_type = 'strict'
        else:
            bias_threshold = self.relaxed_bias_threshold
            narrative_threshold = self.relaxed_narrative_threshold
            criteria_type = 'relaxed'

        # Check convergence
        bias_acceptable = bias_score < bias_threshold
        narrative_acceptable = narrative_alignment > narrative_threshold
        min_iterations_met = iteration > 0  # At least one refinement

        if bias_acceptable and narrative_acceptable and min_iterations_met:
            return {
                'converged': True,
                'reason': f'{criteria_type}_criteria_met',
                'bias_score': bias_score,
                'narrative_alignment': narrative_alignment,
                'iteration': iteration,
                'recommendation': f'수렴 완료 ({criteria_type} criteria). 최종 3000회 시뮬레이션 시작'
            }

        # Not converged - provide detailed feedback
        issues = []
        if not min_iterations_met:
            issues.append('최소 1회 반복 필요')
        if not bias_acceptable:
            issues.append(f'편향 점수 높음 ({bias_score:.2f} > {bias_threshold})')
        if not narrative_acceptable:
            issues.append(f'서사 일치율 낮음 ({narrative_alignment:.2f}% < {narrative_threshold}%)')

        return {
            'converged': False,
            'reason': 'criteria_not_met',
            'bias_score': bias_score,
            'narrative_alignment': narrative_alignment,
            'iteration': iteration,
            'issues': issues,
            'recommendation': f'파라미터 조정 후 재시뮬 필요 ({", ".join(issues)})'
        }

    def should_continue(self, convergence_report: Dict) -> bool:
        """
        Determine if iteration should continue.

        Args:
            convergence_report: Report from check_convergence

        Returns:
            True if should continue iteration, False if should finalize
        """
        return not convergence_report['converged']

    def get_convergence_summary(
        self,
        all_iterations: list
    ) -> Dict:
        """
        Generate summary of convergence process.

        Args:
            all_iterations: List of convergence reports from each iteration

        Returns:
            Summary report
        """
        if not all_iterations:
            return {
                'total_iterations': 0,
                'converged': False,
                'final_bias': None,
                'final_narrative': None
            }

        final_report = all_iterations[-1]

        # Calculate improvement
        if len(all_iterations) > 1:
            first_bias = all_iterations[0]['bias_score']
            final_bias = final_report['bias_score']
            bias_improvement = first_bias - final_bias

            first_narrative = all_iterations[0]['narrative_alignment']
            final_narrative = final_report['narrative_alignment']
            narrative_improvement = final_narrative - first_narrative
        else:
            bias_improvement = 0
            narrative_improvement = 0

        return {
            'total_iterations': len(all_iterations),
            'converged': final_report['converged'],
            'final_bias': final_report['bias_score'],
            'final_narrative': final_report['narrative_alignment'],
            'bias_improvement': round(bias_improvement, 2),
            'narrative_improvement': round(narrative_improvement, 2),
            'convergence_reason': final_report['reason']
        }


def get_convergence_judge() -> ConvergenceJudge:
    """
    Get convergence judge instance.

    Returns:
        ConvergenceJudge instance
    """
    return ConvergenceJudge()
