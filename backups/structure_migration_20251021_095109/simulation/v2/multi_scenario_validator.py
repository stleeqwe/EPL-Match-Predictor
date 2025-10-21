"""
Multi-Scenario Validator
설계 문서 Section 2 (Phase 2) 구현

각 시나리오를 N회 시뮬레이션하여 통계적 타당성 검증
"""

import logging
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass

from .scenario import Scenario
from .scenario_guide import ScenarioGuide
from .event_simulation_engine import (
    EventBasedSimulationEngine,
    MatchParameters,
    EPL_BASELINE
)

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """단일 시나리오 검증 결과"""
    scenario_id: str
    total_runs: int
    win_rate: Dict[str, float]
    avg_score: Dict[str, float]
    score_variance: Dict[str, float]
    narrative_adherence: Dict[str, float]
    bias_metrics: Dict[str, float]
    event_distribution: Dict


class MultiScenarioValidator:
    """
    각 시나리오를 N회 시뮬레이션하여 검증
    설계 문서 Phase 2 구현
    """

    def __init__(self):
        """Initialize validator"""
        self.engine = EventBasedSimulationEngine()
        logger.info("MultiScenarioValidator initialized")

    def validate_scenarios(
        self,
        scenarios: List[Scenario],
        base_params: MatchParameters,
        n: int = 100
    ) -> List[Dict]:
        """
        각 시나리오 × n회 시뮬레이션

        Args:
            scenarios: 검증할 시나리오 리스트
            base_params: 기본 경기 파라미터
            n: 반복 횟수 (기본: 100)

        Returns:
            검증 결과 리스트
        """
        logger.info(f"Validating {len(scenarios)} scenarios × {n} runs...")

        validation_results = []

        for i, scenario in enumerate(scenarios, 1):
            logger.info(f"[{i}/{len(scenarios)}] Validating {scenario.id}: {scenario.name}")

            # 1. ScenarioGuide 생성
            guide = ScenarioGuide(scenario)

            # 2. 시나리오별 파라미터 병합
            scenario_params = self._merge_parameters(base_params, scenario)

            # 3. N회 시뮬레이션
            outcomes = []
            for run_idx in range(n):
                result = self.engine.simulate_match(scenario_params, guide)
                outcomes.append(result)

            # 4. 통계 집계
            stats = self._aggregate_outcomes(outcomes, scenario, n)
            validation_results.append(stats)

            logger.info(f"   ✓ Win rate: H={stats['win_rate']['home']:.1%}, "
                       f"D={stats['win_rate']['draw']:.1%}, A={stats['win_rate']['away']:.1%}")
            logger.info(f"   ✓ Avg score: {stats['avg_score']['home']:.2f}-{stats['avg_score']['away']:.2f}")
            logger.info(f"   ✓ Narrative adherence: {stats['narrative_adherence']['mean']:.1%}")

        logger.info("✓ All scenarios validated")
        return validation_results

    def _merge_parameters(
        self,
        base_params: MatchParameters,
        scenario: Scenario
    ) -> MatchParameters:
        """
        기본 파라미터 + 시나리오 조정 병합

        Args:
            base_params: 기본 파라미터
            scenario: 시나리오

        Returns:
            병합된 파라미터
        """
        # Copy base params
        home_team = base_params.home_team.copy()
        away_team = base_params.away_team.copy()

        # Apply scenario adjustments
        for param_name, adjustment_value in scenario.parameter_adjustments.items():
            # Parse parameter name (e.g., "Son_speed_modifier")
            if "_modifier" in param_name:
                # Extract team/player and stat
                parts = param_name.split("_")

                # Simple heuristic: if it looks like a team name, apply to team
                if "home" in param_name.lower() or "Tottenham" in param_name:
                    # Apply to home team
                    if "attack" in param_name:
                        home_team["attack_strength"] = home_team.get("attack_strength", 75) * adjustment_value
                    elif "defense" in param_name:
                        home_team["defense_strength"] = home_team.get("defense_strength", 75) * adjustment_value
                    elif "midfield" in param_name:
                        home_team["midfield_strength"] = home_team.get("midfield_strength", 75) * adjustment_value

                elif "away" in param_name.lower() or "Arsenal" in param_name:
                    # Apply to away team
                    if "attack" in param_name:
                        away_team["attack_strength"] = away_team.get("attack_strength", 75) * adjustment_value
                    elif "defense" in param_name:
                        away_team["defense_strength"] = away_team.get("defense_strength", 75) * adjustment_value
                    elif "midfield" in param_name:
                        away_team["midfield_strength"] = away_team.get("midfield_strength", 75) * adjustment_value

        return MatchParameters(
            home_team=home_team,
            away_team=away_team,
            home_formation=base_params.home_formation,
            away_formation=base_params.away_formation
        )

    def _aggregate_outcomes(
        self,
        outcomes: List[Dict],
        scenario: Scenario,
        n: int
    ) -> Dict:
        """
        시뮬레이션 결과 통계 집계

        Args:
            outcomes: 시뮬레이션 결과 리스트
            scenario: 시나리오
            n: 반복 횟수

        Returns:
            집계된 통계
        """
        # Win rates
        home_wins = sum(1 for o in outcomes if o["final_score"]["home"] > o["final_score"]["away"])
        away_wins = sum(1 for o in outcomes if o["final_score"]["away"] > o["final_score"]["home"])
        draws = n - home_wins - away_wins

        win_rate = {
            "home": home_wins / n,
            "away": away_wins / n,
            "draw": draws / n
        }

        # Average scores
        home_scores = [o["final_score"]["home"] for o in outcomes]
        away_scores = [o["final_score"]["away"] for o in outcomes]

        avg_score = {
            "home": np.mean(home_scores),
            "away": np.mean(away_scores)
        }

        score_variance = {
            "home": np.var(home_scores),
            "away": np.var(away_scores)
        }

        # Narrative adherence
        adherence_scores = [o["narrative_adherence"] for o in outcomes]
        narrative_adherence = {
            "mean": np.mean(adherence_scores),
            "std": np.std(adherence_scores),
            "min": np.min(adherence_scores),
            "max": np.max(adherence_scores)
        }

        # Bias metrics
        bias_metrics = self._calculate_bias_metrics(outcomes, scenario)

        # Event distribution
        event_distribution = self._analyze_event_distribution(outcomes, scenario)

        # Score distribution
        score_distribution = self._calculate_score_distribution(outcomes)

        return {
            "scenario_id": scenario.id,
            "scenario_name": scenario.name,
            "total_runs": n,
            "win_rate": win_rate,
            "avg_score": avg_score,
            "score_variance": score_variance,
            "narrative_adherence": narrative_adherence,
            "bias_metrics": bias_metrics,
            "event_distribution": event_distribution,
            "score_distribution": score_distribution
        }

    def _calculate_bias_metrics(
        self,
        outcomes: List[Dict],
        scenario: Scenario
    ) -> Dict[str, float]:
        """
        편향도 계산 (EPL 기준 대비)

        Returns:
            {
                "score_bias": float,  # |실제 - EPL| / EPL
                "home_advantage_bias": float
            }
        """
        # Average total goals
        total_goals = np.mean([
            o["final_score"]["home"] + o["final_score"]["away"]
            for o in outcomes
        ])

        # Score bias (vs EPL 2.8)
        epl_avg_goals = EPL_BASELINE["avg_goals_per_game"]
        score_bias = abs(total_goals - epl_avg_goals) / epl_avg_goals

        # Home advantage bias
        home_wins = sum(1 for o in outcomes if o["final_score"]["home"] > o["final_score"]["away"])
        home_win_rate = home_wins / len(outcomes)
        epl_home_win_rate = EPL_BASELINE["home_win_rate"]
        home_advantage_bias = abs(home_win_rate - epl_home_win_rate) / epl_home_win_rate

        return {
            "score_bias": score_bias,
            "home_advantage_bias": home_advantage_bias,
            "total_goals_avg": total_goals,
            "epl_reference": epl_avg_goals
        }

    def _analyze_event_distribution(
        self,
        outcomes: List[Dict],
        scenario: Scenario
    ) -> Dict:
        """
        이벤트 분포 분석

        Returns:
            {
                "expected_events_occurred": float,  # 예상 이벤트 발생률
                "goal_timing": {...}
            }
        """
        # Count expected events that occurred
        expected_event_types = [e.type.value for e in scenario.events]

        occurred_count = 0
        for outcome in outcomes:
            for expected_type in expected_event_types:
                # Check if this event type occurred
                matching_events = [
                    e for e in outcome["events"]
                    if e["type"] == expected_type
                ]
                if matching_events:
                    occurred_count += 1
                    break  # Count once per outcome

        expected_events_occurred = occurred_count / len(outcomes)

        # Goal timing analysis
        all_goals = []
        for outcome in outcomes:
            goals = [e for e in outcome["events"] if e["type"] == "goal"]
            all_goals.extend(goals)

        goal_timing = {
            "0-30min": len([g for g in all_goals if g["minute"] < 30]) / max(len(all_goals), 1),
            "30-60min": len([g for g in all_goals if 30 <= g["minute"] < 60]) / max(len(all_goals), 1),
            "60-90min": len([g for g in all_goals if g["minute"] >= 60]) / max(len(all_goals), 1),
            "total_goals": len(all_goals)
        }

        return {
            "expected_events_occurred": expected_events_occurred,
            "goal_timing": goal_timing
        }

    def _calculate_score_distribution(self, outcomes: List[Dict]) -> Dict[str, float]:
        """
        스코어 분포 계산

        Returns:
            {"0-0": 0.03, "1-0": 0.12, ...}
        """
        score_counts = {}

        for outcome in outcomes:
            home = outcome["final_score"]["home"]
            away = outcome["final_score"]["away"]
            score_str = f"{home}-{away}"
            score_counts[score_str] = score_counts.get(score_str, 0) + 1

        # Convert to probabilities
        total = len(outcomes)
        score_distribution = {
            score: count / total
            for score, count in score_counts.items()
        }

        # Sort by probability (descending)
        score_distribution = dict(
            sorted(score_distribution.items(), key=lambda x: x[1], reverse=True)
        )

        return score_distribution


# Global instance
_validator = None


def get_validator() -> MultiScenarioValidator:
    """Get global validator instance (singleton)."""
    global _validator
    if _validator is None:
        _validator = MultiScenarioValidator()
    return _validator
