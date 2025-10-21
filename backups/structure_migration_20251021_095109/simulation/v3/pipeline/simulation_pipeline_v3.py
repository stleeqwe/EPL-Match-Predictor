"""
Simulation Pipeline V3

완전히 재설계된 4단계 파이프라인:

Phase 1: Mathematical Models (Ensemble)
  - Poisson-Rating
  - Zone Dominance (9 zones)
  - Key Player Weighted
  - Ensemble (0.4/0.3/0.3)

Phase 2: AI Scenario Generation
  - Mathematical analysis → AI input
  - User commentary → Narrative
  - Dynamic scenario count (2-5)
  - NO Templates

Phase 3: Monte Carlo Validation
  - 3000 runs per scenario
  - Zone/Player models → simulation params
  - Convergence = Truth
  - NO Bias detection, NO EPL forcing

Phase 4: Final Report
  - Convergence probabilities
  - Scenarios with validation results
  - Tactical insights
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import logging
import time

from ai.enriched_data_models import EnrichedTeamInput

# Import V3 components
from ..models.model_ensemble import ModelEnsemble, EnsembleResult
from ..scenario.math_based_generator import MathBasedScenarioGenerator, GeneratedScenarioResult
from ..validation.monte_carlo_validator import MonteCarloValidator, ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Pipeline 설정"""
    validation_runs: int = 3000           # Per scenario
    enable_streaming: bool = False        # SSE streaming
    log_level: str = "INFO"


@dataclass
class PipelineResult:
    """Pipeline 실행 결과"""
    # Phase 1: Mathematical Models
    ensemble_result: EnsembleResult

    # Phase 2: AI Scenarios
    generated_scenarios: GeneratedScenarioResult

    # Phase 3: Validation
    validation_result: ValidationResult

    # Summary
    final_probabilities: Dict[str, float]    # {home_win, draw, away_win}
    execution_time: float                     # seconds
    home_team_name: str
    away_team_name: str


class SimulationPipelineV3:
    """
    Simulation Pipeline V3

    완전히 재설계된 시뮬레이션 파이프라인:
    - 100% 사용자 도메인 데이터 기반
    - NO Templates
    - NO EPL baseline forcing
    - Convergence = Truth
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        """
        Initialize Pipeline V3

        Args:
            config: Pipeline 설정
        """
        self.config = config or PipelineConfig()

        # Set logging level
        logging.getLogger().setLevel(self.config.log_level)

        # Initialize components
        self.ensemble = ModelEnsemble()
        self.scenario_generator = MathBasedScenarioGenerator()
        self.validator = MonteCarloValidator()

        logger.info("[Pipeline V3] Initialized")
        logger.info(f"[Pipeline V3] Validation runs per scenario: {self.config.validation_runs}")

    def run(self,
            home_team: EnrichedTeamInput,
            away_team: EnrichedTeamInput) -> PipelineResult:
        """
        전체 파이프라인 실행

        Args:
            home_team: 홈팀 데이터 (사용자 입력)
            away_team: 원정팀 데이터 (사용자 입력)

        Returns:
            PipelineResult with all results
        """
        start_time = time.time()

        logger.info("="*80)
        logger.info(f"SIMULATION PIPELINE V3: {home_team.name} vs {away_team.name}")
        logger.info("="*80)

        # Phase 1: Mathematical Models (Ensemble)
        logger.info("\n[Phase 1/4] Running Mathematical Models (Ensemble)...")
        ensemble_result = self._run_phase1_ensemble(home_team, away_team)

        # Phase 2: AI Scenario Generation
        logger.info("\n[Phase 2/4] Generating AI Scenarios...")
        generated_scenarios = self._run_phase2_scenarios(home_team, away_team, ensemble_result)

        # Phase 3: Monte Carlo Validation
        logger.info("\n[Phase 3/4] Running Monte Carlo Validation...")
        validation_result = self._run_phase3_validation(
            generated_scenarios.scenarios,
            home_team,
            away_team,
            ensemble_result
        )

        # Phase 4: Final Report
        logger.info("\n[Phase 4/4] Generating Final Report...")
        final_probs = validation_result.final_probabilities

        execution_time = time.time() - start_time

        logger.info("\n" + "="*80)
        logger.info("PIPELINE V3 COMPLETED")
        logger.info("="*80)
        logger.info(f"Execution time: {execution_time:.1f}s")
        logger.info(f"\nFinal Probabilities (Converged):")
        logger.info(f"  Home win: {final_probs['home_win']:.1%}")
        logger.info(f"  Draw:     {final_probs['draw']:.1%}")
        logger.info(f"  Away win: {final_probs['away_win']:.1%}")
        logger.info("="*80)

        return PipelineResult(
            ensemble_result=ensemble_result,
            generated_scenarios=generated_scenarios,
            validation_result=validation_result,
            final_probabilities=final_probs,
            execution_time=execution_time,
            home_team_name=home_team.name,
            away_team_name=away_team.name
        )

    def _run_phase1_ensemble(self,
                              home_team: EnrichedTeamInput,
                              away_team: EnrichedTeamInput) -> EnsembleResult:
        """
        Phase 1: Mathematical Models (Ensemble)

        Returns:
            EnsembleResult
        """
        logger.info("[Phase 1] Calculating Poisson-Rating, Zone Dominance, Key Player models...")

        ensemble_result = self.ensemble.calculate(home_team, away_team)

        logger.info("[Phase 1] ✓ Ensemble probabilities calculated:")
        logger.info(f"  Home: {ensemble_result.ensemble_probabilities['home_win']:.1%}")
        logger.info(f"  Draw: {ensemble_result.ensemble_probabilities['draw']:.1%}")
        logger.info(f"  Away: {ensemble_result.ensemble_probabilities['away_win']:.1%}")

        return ensemble_result

    def _run_phase2_scenarios(self,
                               home_team: EnrichedTeamInput,
                               away_team: EnrichedTeamInput,
                               ensemble_result: EnsembleResult) -> GeneratedScenarioResult:
        """
        Phase 2: AI Scenario Generation

        Returns:
            GeneratedScenarioResult
        """
        logger.info("[Phase 2] Calling AI to generate scenarios (NO Templates)...")

        generated_scenarios = self.scenario_generator.generate(
            home_team,
            away_team,
            ensemble_result
        )

        logger.info(f"[Phase 2] ✓ Generated {generated_scenarios.scenario_count} scenarios")
        for scenario in generated_scenarios.scenarios:
            logger.info(f"  - {scenario.id}: {scenario.name} ({scenario.expected_probability:.1%})")

        return generated_scenarios

    def _run_phase3_validation(self,
                                scenarios: List,
                                home_team: EnrichedTeamInput,
                                away_team: EnrichedTeamInput,
                                ensemble_result: EnsembleResult) -> ValidationResult:
        """
        Phase 3: Monte Carlo Validation

        Returns:
            ValidationResult
        """
        logger.info(f"[Phase 3] Validating {len(scenarios)} scenarios...")
        logger.info(f"[Phase 3] Runs per scenario: {self.config.validation_runs}")
        logger.info(f"[Phase 3] Total runs: {len(scenarios) * self.config.validation_runs}")

        validation_result = self.validator.validate(
            scenarios,
            home_team,
            away_team,
            ensemble_result
        )

        logger.info("[Phase 3] ✓ Validation complete")
        logger.info(f"[Phase 3] Convergence probabilities:")
        logger.info(f"  Home: {validation_result.final_probabilities['home_win']:.1%}")
        logger.info(f"  Draw: {validation_result.final_probabilities['draw']:.1%}")
        logger.info(f"  Away: {validation_result.final_probabilities['away_win']:.1%}")

        return validation_result


if __name__ == "__main__":
    # Test
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s'
    )

    from services.enriched_data_loader import EnrichedDomainDataLoader

    loader = EnrichedDomainDataLoader()
    arsenal = loader.load_team_data("Arsenal")
    liverpool = loader.load_team_data("Liverpool")

    # Run pipeline
    config = PipelineConfig(
        validation_runs=100,  # Reduced for testing
        log_level="INFO"
    )

    pipeline = SimulationPipelineV3(config=config)

    print("\n" + "="*80)
    print("TESTING SIMULATION PIPELINE V3")
    print("="*80)
    print(f"\nMatch: {arsenal.name} vs {liverpool.name}")
    print(f"Validation runs: {config.validation_runs} (reduced for testing)")
    print()

    result = pipeline.run(arsenal, liverpool)

    print("\n" + "="*80)
    print("TEST RESULTS")
    print("="*80)
    print(f"\nExecution time: {result.execution_time:.1f}s")
    print(f"\nScenarios generated: {result.generated_scenarios.scenario_count}")
    print(f"Total validation runs: {result.validation_result.total_runs}")
    print(f"\nFinal probabilities:")
    print(f"  Home: {result.final_probabilities['home_win']:.1%}")
    print(f"  Draw: {result.final_probabilities['draw']:.1%}")
    print(f"  Away: {result.final_probabilities['away_win']:.1%}")
    print()
