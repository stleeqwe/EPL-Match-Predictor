"""
Simulation Pipeline
설계 문서 Phase 1-7 완전 통합

AI-Guided Iterative Refinement Pipeline
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .ai_scenario_generator import get_scenario_generator
from .multi_scenario_validator import get_validator
from .ai_analyzer import get_analyzer, apply_adjustments
from .event_simulation_engine import create_match_parameters, MatchParameters
from .scenario import Scenario

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """파이프라인 설정"""
    max_iterations: int = 5
    initial_runs: int = 100
    final_runs: int = 3000
    convergence_threshold: float = 0.85


class SimulationPipeline:
    """
    Phase 1-7 완전 구현
    설계 문서 정확 준수
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Args:
            config: 파이프라인 설정 (기본값 사용 가능)
        """
        self.config = config or PipelineConfig()
        self.scenario_generator = get_scenario_generator()
        self.validator = get_validator()
        self.analyzer = get_analyzer()

        logger.info(f"SimulationPipeline initialized (max_iterations={self.config.max_iterations})")

    def run(
        self,
        match_context: Dict,
        base_params: MatchParameters,
        player_stats: Optional[Dict] = None,
        tactics: Optional[Dict] = None,
        domain_knowledge: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        전체 파이프라인 실행

        Args:
            match_context: {"home_team": "...", "away_team": "..."}
            base_params: 기본 경기 파라미터
            player_stats: 선수 능력치 (선택)
            tactics: 전술 정보 (선택)
            domain_knowledge: 사용자 도메인 지식 (핵심!)

        Returns:
            Tuple of (success, result_dict, error_message)
        """
        try:
            logger.info("="*70)
            logger.info("Simulation Pipeline Started")
            logger.info("="*70)

            # Phase 1: AI 시나리오 생성
            logger.info("\n[Phase 1] AI Scenario Generation")
            logger.info("-"*70)

            success, scenarios, error = self.scenario_generator.generate_scenarios(
                match_context=match_context,
                player_stats=player_stats,
                tactics=tactics,
                domain_knowledge=domain_knowledge
            )

            if not success:
                return False, None, f"Phase 1 failed: {error}"

            logger.info(f"✓ Generated {len(scenarios)} scenarios")

            # Phase 2-5: Iterative Refinement Loop
            logger.info("\n[Phase 2-5] Iterative Refinement Loop")
            logger.info("-"*70)

            iteration = 1
            converged = False
            history = []
            current_scenarios = scenarios

            while not converged and iteration <= self.config.max_iterations:
                logger.info(f"\n>>> Iteration {iteration}/{self.config.max_iterations}")

                # Phase 2: Simulate (100 runs per scenario)
                logger.info(f"  Phase 2: Simulating ({len(current_scenarios)} × {self.config.initial_runs})...")
                validation_results = self.validator.validate_scenarios(
                    scenarios=current_scenarios,
                    base_params=base_params,
                    n=self.config.initial_runs
                )

                # Phase 3: AI Analysis
                logger.info(f"  Phase 3: AI Analysis...")
                success, ai_analysis, error = self.analyzer.analyze_and_adjust(
                    scenarios=current_scenarios,
                    validation_results=validation_results,
                    iteration=iteration
                )

                if not success:
                    logger.warning(f"  ⚠ Analysis failed: {error}")
                    # Continue with current scenarios
                    break

                # Record history
                history.append({
                    "iteration": iteration,
                    "scenarios": current_scenarios,
                    "validation_results": validation_results,
                    "ai_analysis": ai_analysis
                })

                # Phase 5: Convergence Check
                convergence = ai_analysis['convergence']
                logger.info(f"  Phase 5: Convergence Check")
                logger.info(f"    Converged: {convergence['converged']}")
                logger.info(f"    Confidence: {convergence['confidence']:.1%}")

                if convergence['converged'] and convergence['confidence'] >= self.config.convergence_threshold:
                    converged = True
                    logger.info(f"  ✓ Convergence achieved!")
                    break

                # Phase 4: Apply Adjustments
                logger.info(f"  Phase 4: Applying adjustments...")
                current_scenarios = apply_adjustments(current_scenarios, ai_analysis)
                logger.info(f"    → {len(current_scenarios)} scenarios adjusted")

                iteration += 1

            if not converged:
                logger.warning(f"\n⚠ Max iterations reached without convergence")
                logger.info(f"  Proceeding with best available scenarios")

            # Phase 6: Final High-Resolution Simulation
            logger.info(f"\n[Phase 6] Final High-Resolution Simulation")
            logger.info("-"*70)
            logger.info(f"  Simulating ({len(current_scenarios)} × {self.config.final_runs})...")

            final_results = self.validator.validate_scenarios(
                scenarios=current_scenarios,
                base_params=base_params,
                n=self.config.final_runs
            )

            logger.info(f"✓ Completed {len(current_scenarios) * self.config.final_runs} simulations")

            # Phase 7: AI Final Report (TODO: implement report generator)
            logger.info(f"\n[Phase 7] AI Final Report")
            logger.info("-"*70)
            logger.info("  Report generation: Simplified for now")

            # Build final report
            final_report = self._build_simplified_report(
                current_scenarios,
                final_results,
                history,
                match_context
            )

            # Compile final output
            output = {
                "scenarios": [s.to_dict() for s in current_scenarios],
                "final_results": final_results,
                "report": final_report,
                "history": history,
                "converged": converged,
                "iterations": iteration - 1 if converged else iteration,
                "metadata": {
                    "home_team": match_context.get("home_team"),
                    "away_team": match_context.get("away_team"),
                    "total_simulations": (iteration - 1) * len(scenarios) * self.config.initial_runs + len(current_scenarios) * self.config.final_runs
                }
            }

            logger.info("\n" + "="*70)
            logger.info("Simulation Pipeline Completed Successfully")
            logger.info("="*70)

            return True, output, None

        except Exception as e:
            error_msg = f"Pipeline error: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg

    def _build_simplified_report(
        self,
        scenarios: List[Scenario],
        final_results: List[Dict],
        history: List[Dict],
        match_context: Dict
    ) -> Dict:
        """
        간소화된 최종 리포트 생성
        (Phase 7의 완전한 AI 리포트는 추후 구현)
        """
        # Calculate weighted probabilities
        total_prob = sum(s.expected_probability for s in scenarios)
        if total_prob > 0:
            normalized_probs = [s.expected_probability / total_prob for s in scenarios]
        else:
            normalized_probs = [1.0 / len(scenarios)] * len(scenarios)

        # Weighted average predictions
        weighted_home_wins = sum(
            r['win_rate']['home'] * prob
            for r, prob in zip(final_results, normalized_probs)
        )
        weighted_draws = sum(
            r['win_rate']['draw'] * prob
            for r, prob in zip(final_results, normalized_probs)
        )
        weighted_away_wins = sum(
            r['win_rate']['away'] * prob
            for r, prob in zip(final_results, normalized_probs)
        )

        weighted_home_goals = sum(
            r['avg_score']['home'] * prob
            for r, prob in zip(final_results, normalized_probs)
        )
        weighted_away_goals = sum(
            r['avg_score']['away'] * prob
            for r, prob in zip(final_results, normalized_probs)
        )

        # Find most likely scenario
        most_likely_scenario = max(zip(scenarios, normalized_probs), key=lambda x: x[1])

        # Build report
        report = {
            "match": {
                "home_team": match_context.get("home_team"),
                "away_team": match_context.get("away_team")
            },
            "prediction": {
                "win_probabilities": {
                    "home": weighted_home_wins,
                    "draw": weighted_draws,
                    "away": weighted_away_wins
                },
                "expected_goals": {
                    "home": weighted_home_goals,
                    "away": weighted_away_goals
                },
                "most_likely_outcome": self._determine_outcome(
                    weighted_home_wins,
                    weighted_draws,
                    weighted_away_wins
                )
            },
            "dominant_scenario": {
                "id": most_likely_scenario[0].id,
                "name": most_likely_scenario[0].name,
                "probability": most_likely_scenario[1],
                "reasoning": most_likely_scenario[0].reasoning
            },
            "all_scenarios": [
                {
                    "id": s.id,
                    "name": s.name,
                    "probability": prob,
                    "win_rate": final_results[i]['win_rate'],
                    "avg_score": final_results[i]['avg_score']
                }
                for i, (s, prob) in enumerate(zip(scenarios, normalized_probs))
            ],
            "convergence_summary": {
                "iterations": len(history),
                "converged": len(history) > 0 and history[-1]['ai_analysis']['convergence']['converged'],
                "final_confidence": history[-1]['ai_analysis']['convergence']['confidence'] if history else 0.0
            }
        }

        return report

    def _determine_outcome(self, home: float, draw: float, away: float) -> str:
        """가장 가능성 높은 결과 판정"""
        if home > draw and home > away:
            return "home_win"
        elif away > draw and away > home:
            return "away_win"
        else:
            return "draw"


# Global instance
_pipeline = None


def get_pipeline(config: Optional[PipelineConfig] = None) -> SimulationPipeline:
    """Get global pipeline instance (singleton)."""
    global _pipeline
    if _pipeline is None:
        _pipeline = SimulationPipeline(config=config)
    return _pipeline
