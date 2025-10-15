"""
Match Simulator v2.0 - AI-Guided Iterative Refinement
Main orchestrator for the complete simulation workflow

워크플로우:
1. AI 파라미터 생성
2. 초기 시뮬레이션 (100회)
3. 반복 루프:
   - 편향 감지
   - 서사 일치율 분석
   - 수렴 판정
   - 파라미터 조정 (if not converged)
   - 재시뮬레이션 (100회)
4. 최종 시뮬레이션 (3000회)
5. 완전한 예측 결과 반환
"""

import logging
from typing import Dict, Optional, Tuple
from datetime import datetime

from simulation.v2.ai_parameter_generator import get_parameter_generator
from simulation.v2.iterative_engine import get_iterative_engine
from simulation.v2.bias_detector import get_bias_detector
from simulation.v2.narrative_analyzer import get_narrative_analyzer
from simulation.v2.convergence_judge import get_convergence_judge
from simulation.v2.parameter_adjuster import get_parameter_adjuster

logger = logging.getLogger(__name__)


class MatchSimulatorV2:
    """
    v2.0 Match Simulator with AI-guided iterative refinement.

    Complete workflow orchestrator that combines all v2 components
    to produce high-quality match predictions.
    """

    def __init__(self):
        """Initialize match simulator v2."""
        self.param_generator = get_parameter_generator()
        self.simulation_engine = get_iterative_engine()
        self.bias_detector = get_bias_detector()
        self.narrative_analyzer = get_narrative_analyzer()
        self.convergence_judge = get_convergence_judge()
        self.param_adjuster = get_parameter_adjuster()

        logger.info("MatchSimulatorV2 initialized")

    def predict(
        self,
        home_team_data: Dict,
        away_team_data: Dict,
        user_insight: Optional[str] = None
    ) -> Tuple[bool, Dict, Optional[str]]:
        """
        Main prediction method with full iterative refinement.

        Args:
            home_team_data: Home team tactical data
                Format: {
                    'name': str,
                    'overall_rating': float,
                    'tactical_profile': {
                        'attacking_efficiency': float,
                        'defensive_stability': float,
                        ...
                    }
                }
            away_team_data: Away team tactical data (same format)
            user_insight: Optional user analysis/insights

        Returns:
            Tuple of (success, prediction_dict, error_message)
            prediction_dict format:
            {
                'match': {...},
                'prediction': {...},
                'ai_analysis': {...},
                'convergence_report': {...},
                'metadata': {...}
            }
        """
        start_time = datetime.now()
        home_name = home_team_data.get('name', 'Home')
        away_name = away_team_data.get('name', 'Away')

        logger.info(f"=== Starting v2.0 Prediction: {home_name} vs {away_name} ===")

        try:
            # Step 1: Generate initial parameters
            logger.info("Step 1: Generating AI parameters")
            success, param_result, error = self.param_generator.generate_parameters(
                home_team_data,
                away_team_data,
                user_insight
            )

            if not success:
                return False, {}, f"Parameter generation failed: {error}"

            parameters = param_result
            expected_scenario = parameters['simulation_parameters']['expected_scenario']
            logger.info(f"Parameters generated: scenario={expected_scenario}")

            # Step 2: Iterative refinement loop
            iteration = 0
            max_iterations = 8
            convergence_history = []

            logger.info("Step 2: Starting iterative refinement loop")

            while iteration < max_iterations:
                logger.info(f"\n--- Iteration {iteration} ---")

                # Simulate (100 runs for iteration, or skip if iteration 0)
                if iteration == 0:
                    logger.info("Initial simulation (100 runs)")
                else:
                    logger.info("Re-simulation with adjusted parameters (100 runs)")

                sim_results = self.simulation_engine.simulate(
                    home_team_data,
                    away_team_data,
                    parameters['simulation_parameters'],
                    num_runs=100
                )

                # Analyze bias
                logger.info("Analyzing bias...")
                bias_analysis = self.bias_detector.analyze(sim_results)
                logger.info(f"Bias score: {bias_analysis['bias_score']}")

                # Analyze narrative alignment
                logger.info("Analyzing narrative alignment...")
                narrative_analysis = self.narrative_analyzer.analyze(
                    sim_results,
                    expected_scenario
                )
                logger.info(f"Narrative alignment: {narrative_analysis['narrative_alignment']}%")

                # Check convergence
                logger.info("Checking convergence...")
                convergence_result = self.convergence_judge.check_convergence(
                    bias_analysis['bias_score'],
                    narrative_analysis['narrative_alignment'],
                    iteration
                )
                convergence_history.append(convergence_result)

                logger.info(f"Converged: {convergence_result['converged']}")
                logger.info(f"Reason: {convergence_result['reason']}")

                if convergence_result['converged']:
                    logger.info(f"✅ Convergence achieved at iteration {iteration}")
                    break

                # Adjust parameters
                logger.info("Adjusting parameters...")
                adjusted = self.param_adjuster.adjust_parameters(
                    parameters,
                    bias_analysis,
                    narrative_analysis,
                    use_ai=True
                )
                parameters = adjusted
                logger.info(f"Parameters adjusted: {adjusted.get('adjustment_reasoning', 'N/A')}")

                iteration += 1

            # Step 3: Final simulation (3000 runs)
            logger.info(f"\n--- Final Simulation (3000 runs) ---")
            logger.info(f"Total iterations: {iteration + 1}")

            final_results = self.simulation_engine.simulate(
                home_team_data,
                away_team_data,
                parameters['simulation_parameters'],
                num_runs=3000
            )

            # Generate convergence summary
            convergence_summary = self.convergence_judge.get_convergence_summary(
                convergence_history
            )

            # Build complete prediction response
            end_time = datetime.now()
            elapsed = (end_time - start_time).total_seconds()

            prediction = {
                'match': {
                    'home_team': home_name,
                    'away_team': away_name,
                    'timestamp': start_time.isoformat(),
                    'user_insight': user_insight
                },
                'prediction': {
                    'probabilities': final_results['probabilities'],
                    'predicted_score': final_results['predicted_score'],
                    'expected_goals': final_results['expected_goals'],
                    'confidence': final_results['confidence'],
                    'score_distribution': final_results['score_distribution']
                },
                'match_events': final_results.get('events', {}),
                'ai_analysis': {
                    'initial_parameters': param_result.get('simulation_parameters', {}),
                    'final_parameters': parameters.get('simulation_parameters', {}),
                    'expected_scenario': expected_scenario,
                    'ai_reasoning': param_result.get('ai_reasoning', ''),
                    'parameter_adjustments': iteration
                },
                'convergence_report': {
                    'total_iterations': convergence_summary['total_iterations'],
                    'converged': convergence_summary['converged'],
                    'final_bias_score': convergence_summary['final_bias'],
                    'final_narrative_alignment': convergence_summary['final_narrative'],
                    'bias_improvement': convergence_summary.get('bias_improvement', 0),
                    'narrative_improvement': convergence_summary.get('narrative_improvement', 0),
                    'convergence_reason': convergence_summary.get('convergence_reason', 'N/A'),
                    'history': convergence_history
                },
                'metadata': {
                    'version': '2.0.0',
                    'engine': 'MatchSimulatorV2',
                    'total_simulations': 100 * (iteration + 1) + 3000,
                    'elapsed_seconds': round(elapsed, 2),
                    'ai_provider': 'qwen'
                }
            }

            logger.info(f"=== Prediction Complete ===")
            logger.info(f"Result: {final_results['predicted_score']}")
            logger.info(f"Probabilities: {final_results['probabilities']}")
            logger.info(f"Iterations: {iteration + 1}")
            logger.info(f"Converged: {convergence_summary['converged']}")
            logger.info(f"Time: {elapsed:.2f}s")

            return True, prediction, None

        except Exception as e:
            logger.error(f"Prediction error: {e}", exc_info=True)
            return False, {}, str(e)

    def quick_predict(
        self,
        home_team: str,
        away_team: str,
        home_rating: float = 75.0,
        away_rating: float = 75.0,
        user_insight: Optional[str] = None
    ) -> Tuple[bool, Dict, Optional[str]]:
        """
        Quick prediction with minimal team data.

        Args:
            home_team: Home team name
            away_team: Away team name
            home_rating: Home team overall rating (0-100)
            away_rating: Away team overall rating (0-100)
            user_insight: Optional user insights

        Returns:
            Tuple of (success, prediction_dict, error_message)
        """
        # Build minimal team data
        home_data = {
            'name': home_team,
            'overall_rating': home_rating,
            'tactical_profile': {
                'attacking_efficiency': home_rating,
                'defensive_stability': home_rating,
                'tactical_organization': home_rating,
                'physicality_stamina': home_rating,
                'psychological_factors': home_rating
            }
        }

        away_data = {
            'name': away_team,
            'overall_rating': away_rating,
            'tactical_profile': {
                'attacking_efficiency': away_rating,
                'defensive_stability': away_rating,
                'tactical_organization': away_rating,
                'physicality_stamina': away_rating,
                'psychological_factors': away_rating
            }
        }

        return self.predict(home_data, away_data, user_insight)


def get_match_simulator_v2() -> MatchSimulatorV2:
    """
    Get match simulator v2 instance.

    Returns:
        MatchSimulatorV2 instance
    """
    return MatchSimulatorV2()
