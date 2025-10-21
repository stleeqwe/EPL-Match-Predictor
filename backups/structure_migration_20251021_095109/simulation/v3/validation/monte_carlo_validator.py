"""
Monte Carlo Validator V3

간소화된 검증:
1. 각 시나리오 × 3000회 시뮬레이션
2. Zone/Player 모델 결과를 시뮬레이션 파라미터에 반영
3. 수렴된 확률 = 정답 (조정 없음)

NO MORE:
- Bias detection
- EPL baseline forcing
- Iterative adjustment
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from dataclasses import dataclass
from typing import List, Dict, Optional
import logging
from collections import Counter

from ai.enriched_data_models import EnrichedTeamInput
from simulation.v2.scenario import Scenario
from simulation.v2.event_simulation_engine import EventBasedSimulationEngine, MatchParameters
from simulation.v2.scenario_guide import ScenarioGuide

# Import ensemble and models
try:
    from ..models.model_ensemble import EnsembleResult
except ImportError:
    # For standalone execution
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "model_ensemble",
        os.path.join(os.path.dirname(__file__), '../models/model_ensemble.py')
    )
    model_ensemble = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(model_ensemble)
    EnsembleResult = model_ensemble.EnsembleResult

logger = logging.getLogger(__name__)


@dataclass
class ScenarioValidationResult:
    """단일 시나리오 검증 결과"""
    scenario_id: str
    scenario_name: str
    initial_probability: float           # AI가 예상한 확률
    convergence_probability: Dict[str, float]  # 수렴된 확률 {home_win, draw, away_win}
    avg_score: Dict[str, float]          # {home, away}
    total_runs: int                      # 시뮬레이션 실행 횟수
    outcome_distribution: Dict[str, int]  # {home_win: N, draw: N, away_win: N}


@dataclass
class ValidationResult:
    """전체 검증 결과"""
    scenario_results: List[ScenarioValidationResult]
    final_probabilities: Dict[str, float]  # 가중 평균된 최종 확률
    total_scenarios: int
    total_runs: int


class MonteCarloValidator:
    """
    Monte Carlo Validator V3

    간소화된 검증 로직:
    1. 시나리오별 3000회 시뮬레이션
    2. 수렴된 확률 계산
    3. 조정 없이 보고
    """

    # Validation runs per scenario
    VALIDATION_RUNS = 3000

    def __init__(self):
        """Initialize Monte Carlo Validator"""
        self.engine = EventBasedSimulationEngine()
        logger.info(f"[Validator] Initialized with {self.VALIDATION_RUNS} runs per scenario")

    def validate(self,
                 scenarios: List[Scenario],
                 home_team: EnrichedTeamInput,
                 away_team: EnrichedTeamInput,
                 ensemble_result: EnsembleResult) -> ValidationResult:
        """
        시나리오 검증

        Args:
            scenarios: AI 생성 시나리오 리스트
            home_team: 홈팀 데이터
            away_team: 원정팀 데이터
            ensemble_result: Ensemble 결과 (zone, player 반영용)

        Returns:
            ValidationResult with convergence probabilities
        """
        logger.info(f"[Validator] Validating {len(scenarios)} scenarios with {self.VALIDATION_RUNS} runs each")

        scenario_results = []

        for scenario in scenarios:
            logger.info(f"[Validator] Validating scenario: {scenario.id} - {scenario.name}")

            # MatchParameters 생성 (zone/player 모델 반영)
            match_params = self._create_match_parameters(
                home_team,
                away_team,
                ensemble_result,
                scenario
            )

            # ScenarioGuide 생성
            scenario_guide = ScenarioGuide(scenario)

            # 시뮬레이션 실행
            simulation_results = []
            for run in range(self.VALIDATION_RUNS):
                result = self.engine.simulate_match(
                    params=match_params,
                    scenario_guide=scenario_guide
                )
                simulation_results.append(result)

                # Progress logging (every 500 runs)
                if (run + 1) % 500 == 0:
                    logger.debug(f"[Validator] {scenario.id}: {run + 1}/{self.VALIDATION_RUNS} runs completed")

            # 결과 집계
            scenario_result = self._aggregate_results(scenario, simulation_results)
            scenario_results.append(scenario_result)

            logger.info(f"[Validator] {scenario.id}: Convergence - "
                       f"Home {scenario_result.convergence_probability['home_win']:.1%}, "
                       f"Draw {scenario_result.convergence_probability['draw']:.1%}, "
                       f"Away {scenario_result.convergence_probability['away_win']:.1%}")

        # 최종 확률 계산 (시나리오별 가중 평균)
        final_probs = self._calculate_final_probabilities(scenario_results)

        logger.info(f"[Validator] Final probabilities: "
                   f"Home {final_probs['home_win']:.1%}, "
                   f"Draw {final_probs['draw']:.1%}, "
                   f"Away {final_probs['away_win']:.1%}")

        return ValidationResult(
            scenario_results=scenario_results,
            final_probabilities=final_probs,
            total_scenarios=len(scenarios),
            total_runs=len(scenarios) * self.VALIDATION_RUNS
        )

    def _create_match_parameters(self,
                                  home_team: EnrichedTeamInput,
                                  away_team: EnrichedTeamInput,
                                  ensemble_result: EnsembleResult,
                                  scenario: Scenario) -> MatchParameters:
        """
        MatchParameters 생성

        Zone dominance와 Player influence를 attack/defense strength에 반영

        Args:
            home_team: 홈팀
            away_team: 원정팀
            ensemble_result: Ensemble 결과
            scenario: 시나리오

        Returns:
            MatchParameters object
        """
        # Base strengths (from user domain data)
        home_attack = home_team.derived_strengths.attack_strength
        home_defense = home_team.derived_strengths.defense_strength
        away_attack = away_team.derived_strengths.attack_strength
        away_defense = away_team.derived_strengths.defense_strength

        # Zone dominance 반영
        # Attack control이 50% 이상이면 보너스, 미만이면 페널티
        zone_summary = ensemble_result.zone_dominance_summary
        home_attack_control = zone_summary['attack_control']['home']
        away_attack_control = zone_summary['attack_control']['away']

        # Attack control: 0.5 = 0, 0.6 = +5, 0.7 = +10
        home_zone_boost = (home_attack_control - 0.5) * 50  # -25 ~ +25
        away_zone_boost = (away_attack_control - 0.5) * 50

        home_attack += home_zone_boost
        away_attack += away_zone_boost

        # Player influence 반영
        # Top 3 players의 평균 influence에 따라 보정
        home_influences = [p['influence'] for p in ensemble_result.key_player_impacts if p['team'] == 'home']
        away_influences = [p['influence'] for p in ensemble_result.key_player_impacts if p['team'] == 'away']

        if home_influences:
            avg_home_influence = sum(home_influences[:3]) / min(3, len(home_influences))
            # Influence 7.0 = 0, 8.0 = +3, 9.0 = +6, 10.0 = +9
            home_player_boost = max(0, (avg_home_influence - 7.0) * 3)
            home_attack += home_player_boost

        if away_influences:
            avg_away_influence = sum(away_influences[:3]) / min(3, len(away_influences))
            away_player_boost = max(0, (avg_away_influence - 7.0) * 3)
            away_attack += away_player_boost

        # Bounds check (0-100)
        home_attack = max(10, min(100, home_attack))
        home_defense = max(10, min(100, home_defense))
        away_attack = max(10, min(100, away_attack))
        away_defense = max(10, min(100, away_defense))

        logger.debug(f"[Validator] {scenario.id}: Adjusted strengths - "
                    f"Home Attack {home_attack:.1f}, Away Attack {away_attack:.1f}")

        return MatchParameters(
            home_team={
                'name': home_team.name,
                'attack_strength': home_attack,
                'defense_strength': home_defense,
                'midfield_control': home_team.derived_strengths.midfield_control,
                'physical_intensity': home_team.derived_strengths.physical_intensity,
            },
            away_team={
                'name': away_team.name,
                'attack_strength': away_attack,
                'defense_strength': away_defense,
                'midfield_control': away_team.derived_strengths.midfield_control,
                'physical_intensity': away_team.derived_strengths.physical_intensity,
            },
            home_formation=home_team.formation,
            away_formation=away_team.formation
        )

    def _aggregate_results(self,
                           scenario: Scenario,
                           simulation_results: List[Dict]) -> ScenarioValidationResult:
        """
        시뮬레이션 결과 집계

        Args:
            scenario: 시나리오
            simulation_results: 시뮬레이션 결과 리스트 (from EventBasedSimulationEngine)

        Returns:
            ScenarioValidationResult
        """
        # Extract scores and calculate outcomes
        outcomes = []
        total_home_goals = 0
        total_away_goals = 0

        for result in simulation_results:
            home_score = result['final_score']['home']
            away_score = result['final_score']['away']

            total_home_goals += home_score
            total_away_goals += away_score

            # Determine outcome
            if home_score > away_score:
                outcomes.append('home_win')
            elif home_score == away_score:
                outcomes.append('draw')
            else:
                outcomes.append('away_win')

        outcome_counts = Counter(outcomes)

        total = len(simulation_results)
        convergence_prob = {
            'home_win': outcome_counts.get('home_win', 0) / total,
            'draw': outcome_counts.get('draw', 0) / total,
            'away_win': outcome_counts.get('away_win', 0) / total,
        }

        avg_score = {
            'home': total_home_goals / total,
            'away': total_away_goals / total,
        }

        return ScenarioValidationResult(
            scenario_id=scenario.id,
            scenario_name=scenario.name,
            initial_probability=scenario.expected_probability,
            convergence_probability=convergence_prob,
            avg_score=avg_score,
            total_runs=total,
            outcome_distribution=dict(outcome_counts)
        )

    def _calculate_final_probabilities(self,
                                        scenario_results: List[ScenarioValidationResult]) -> Dict[str, float]:
        """
        최종 확률 계산 (시나리오별 가중 평균)

        Args:
            scenario_results: 시나리오별 검증 결과

        Returns:
            {home_win, draw, away_win}
        """
        final_probs = {
            'home_win': 0.0,
            'draw': 0.0,
            'away_win': 0.0,
        }

        total_weight = sum(r.initial_probability for r in scenario_results)

        for result in scenario_results:
            weight = result.initial_probability / total_weight if total_weight > 0 else 1.0 / len(scenario_results)

            for outcome in ['home_win', 'draw', 'away_win']:
                final_probs[outcome] += weight * result.convergence_probability[outcome]

        return final_probs


if __name__ == "__main__":
    # Test (requires full pipeline)
    logging.basicConfig(level=logging.INFO)

    print("\n" + "="*80)
    print("Monte Carlo Validator V3")
    print("="*80)
    print("\nThis is a simplified validator:")
    print("- 3000 runs per scenario")
    print("- Convergence = Truth")
    print("- NO bias detection")
    print("- NO EPL baseline forcing")
    print()
