"""
Iterative Simulation Engine v2.0
Monte Carlo simulation with dynamic parameter application

Phase 1과의 차이점:
- 파라미터 기반 시뮬레이션 (동적 조정 가능)
- 100회 (초기/반복) 또는 3000회 (최종) 모드
- 사용자 인사이트를 파라미터로 직접 반영
"""

import random
import logging
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

from simulation.shared.epl_baseline import get_epl_baseline

logger = logging.getLogger(__name__)


class IterativeSimulationEngine:
    """
    Parameter-driven Monte Carlo simulation engine for v2.0.

    Features:
    - Dynamic parameter application
    - Variable simulation runs (100/3000)
    - EPL-calibrated baseline (2.47 goals validated)
    - Detailed event generation
    """

    def __init__(self):
        """Initialize iterative simulation engine."""
        self.baseline = get_epl_baseline()
        logger.info("IterativeSimulationEngine v2.0 initialized")

    def simulate(
        self,
        home_team_data: Dict,
        away_team_data: Dict,
        parameters: Dict,
        num_runs: int = 100
    ) -> Dict:
        """
        Run Monte Carlo simulation with given parameters.

        Args:
            home_team_data: Home team stats
            away_team_data: Away team stats
            parameters: Simulation parameters from AI
                Format: {
                    'home_attack_modifier': float (0.5-1.5),
                    'away_attack_modifier': float (0.5-1.5),
                    'home_defense_modifier': float (0.5-1.5),
                    'away_defense_modifier': float (0.5-1.5),
                    'home_morale': float (0.8-1.2),
                    'away_morale': float (0.8-1.2),
                    'tempo_modifier': float (0.8-1.2),
                    'shot_conversion_modifier': float (0.8-1.2),
                    'expected_scenario': str
                }
            num_runs: Number of simulations (100 for iteration, 3000 for final)

        Returns:
            Aggregated simulation results with statistics
        """
        logger.info(f"Running {num_runs} simulations with parameters")
        logger.debug(f"Parameters: {parameters}")

        # Run simulations
        simulation_results = []
        for i in range(num_runs):
            result = self._simulate_single_match(
                home_team_data,
                away_team_data,
                parameters
            )
            simulation_results.append(result)

        # Aggregate results
        aggregated = self._aggregate_results(
            simulation_results,
            home_team_data,
            away_team_data,
            parameters
        )

        logger.info(f"Simulation complete: {aggregated['probabilities']}")
        return aggregated

    def _simulate_single_match(
        self,
        home_team_data: Dict,
        away_team_data: Dict,
        parameters: Dict
    ) -> Dict:
        """
        Simulate a single match with parameters.

        Returns:
            Match result with score and events
        """
        # Calculate adjusted team strengths
        home_strength = self._calculate_adjusted_strength(
            home_team_data,
            parameters,
            is_home=True
        )
        away_strength = self._calculate_adjusted_strength(
            away_team_data,
            parameters,
            is_home=False
        )

        # Calculate outcome probabilities
        outcome_probs = self._calculate_outcome_probabilities(
            home_strength,
            away_strength
        )

        # Determine outcome
        outcome = self._determine_outcome(outcome_probs)

        # Generate scoreline
        home_goals, away_goals = self._generate_scoreline(
            outcome,
            home_team_data,
            away_team_data,
            parameters
        )

        # Generate events
        events = self._generate_events(
            home_team_data,
            away_team_data,
            home_goals,
            away_goals,
            parameters
        )

        return {
            'home_goals': home_goals,
            'away_goals': away_goals,
            'outcome': outcome,
            'events': events
        }

    def _calculate_adjusted_strength(
        self,
        team_data: Dict,
        parameters: Dict,
        is_home: bool
    ) -> float:
        """
        Calculate team strength with parameter adjustments.

        Returns:
            Adjusted strength value (0-100)
        """
        base_rating = team_data.get('overall_rating', 75.0)

        # Apply modifiers
        team_prefix = 'home' if is_home else 'away'
        attack_mod = parameters.get(f'{team_prefix}_attack_modifier', 1.0)
        defense_mod = parameters.get(f'{team_prefix}_defense_modifier', 1.0)
        morale_mod = parameters.get(f'{team_prefix}_morale', 1.0)

        # Calculate adjusted strength
        attack_rating = team_data.get('tactical_profile', {}).get('attacking_efficiency', 75.0)
        defense_rating = team_data.get('tactical_profile', {}).get('defensive_stability', 75.0)

        adjusted_attack = attack_rating * attack_mod
        adjusted_defense = defense_rating * defense_mod

        # Combine with morale
        combined_strength = (
            (adjusted_attack * 0.4 + adjusted_defense * 0.3 + base_rating * 0.3)
            * morale_mod
        )

        # Add home advantage if applicable
        if is_home:
            combined_strength += 4.0

        return max(50.0, min(100.0, combined_strength))

    def _calculate_outcome_probabilities(
        self,
        home_strength: float,
        away_strength: float
    ) -> Dict[str, float]:
        """
        Calculate outcome probabilities from adjusted strengths.

        Returns:
            Dict with home_win, draw, away_win probabilities
        """
        # Calculate strength differential
        diff = (home_strength - away_strength) / 30.0
        diff = max(-1.0, min(1.0, diff))

        # Start with baseline
        base_home = self.baseline.home_win_rate
        base_draw = self.baseline.draw_rate
        base_away = self.baseline.away_win_rate

        # Adjust based on differential
        adjustment_factor = abs(diff) * 0.45
        if abs(diff) > 0.6:
            adjustment_factor = min(0.5, adjustment_factor * 1.2)

        if diff > 0:
            # Home stronger
            home_prob = base_home + (adjustment_factor * (1 - base_home))
            away_prob = base_away * (1 - adjustment_factor)
            draw_prob = 1 - home_prob - away_prob
        elif diff < 0:
            # Away stronger
            away_prob = base_away + (adjustment_factor * (1 - base_away))
            home_prob = base_home * (1 - adjustment_factor)
            draw_prob = 1 - home_prob - away_prob
        else:
            # Even
            home_prob = base_home
            draw_prob = base_draw
            away_prob = base_away

        # Normalize
        total = home_prob + draw_prob + away_prob
        return {
            'home_win': home_prob / total,
            'draw': draw_prob / total,
            'away_win': away_prob / total
        }

    def _determine_outcome(self, outcome_probs: Dict[str, float]) -> str:
        """Determine match outcome based on probabilities."""
        rand = random.random()
        cumulative = 0.0

        for outcome, prob in outcome_probs.items():
            cumulative += prob
            if rand <= cumulative:
                return outcome

        return 'draw'  # Fallback

    def _generate_scoreline(
        self,
        outcome: str,
        home_team_data: Dict,
        away_team_data: Dict,
        parameters: Dict
    ) -> Tuple[int, int]:
        """
        Generate realistic scoreline with parameter modifiers.

        Returns:
            Tuple of (home_goals, away_goals)
        """
        # Get ratings
        home_attack = home_team_data.get('tactical_profile', {}).get('attacking_efficiency', 75.0)
        home_defense = home_team_data.get('tactical_profile', {}).get('defensive_stability', 75.0)
        away_attack = away_team_data.get('tactical_profile', {}).get('attacking_efficiency', 75.0)
        away_defense = away_team_data.get('tactical_profile', {}).get('defensive_stability', 75.0)

        # Apply parameter modifiers
        home_attack *= parameters.get('home_attack_modifier', 1.0)
        away_attack *= parameters.get('away_attack_modifier', 1.0)
        home_defense *= parameters.get('home_defense_modifier', 1.0)
        away_defense *= parameters.get('away_defense_modifier', 1.0)

        # Apply tempo modifier (affects overall scoring)
        tempo_mod = parameters.get('tempo_modifier', 1.0)
        conversion_mod = parameters.get('shot_conversion_modifier', 1.0)

        # Calculate expected goals (calibrated for 2.8 avg)
        home_xg_base = (home_attack / 100.0) * 2.5 * (1 - away_defense / 100.0 * 0.3)
        away_xg_base = (away_attack / 100.0) * 2.3 * (1 - home_defense / 100.0 * 0.3)

        # Apply modifiers
        home_xg_base *= tempo_mod * conversion_mod
        away_xg_base *= tempo_mod * conversion_mod

        # Generate goals based on outcome
        if outcome == 'home_win':
            home_goals = max(1, int(random.gauss(home_xg_base * 1.3, 0.8)))
            away_goals = max(0, int(random.gauss(away_xg_base * 0.8, 0.6)))
            if home_goals <= away_goals:
                home_goals = away_goals + random.randint(1, 2)

        elif outcome == 'away_win':
            home_goals = max(0, int(random.gauss(home_xg_base * 0.8, 0.6)))
            away_goals = max(1, int(random.gauss(away_xg_base * 1.3, 0.8)))
            if away_goals <= home_goals:
                away_goals = home_goals + random.randint(1, 2)

        else:  # draw
            avg_goals = (home_xg_base + away_xg_base) / 2
            goals = max(0, int(random.gauss(avg_goals, 0.5)))
            home_goals = goals
            away_goals = goals

        # Cap at realistic maximum
        home_goals = min(home_goals, 6)
        away_goals = min(away_goals, 6)

        return home_goals, away_goals

    def _generate_events(
        self,
        home_team_data: Dict,
        away_team_data: Dict,
        home_goals: int,
        away_goals: int,
        parameters: Dict
    ) -> Dict:
        """
        Generate match events with parameter influence.

        Returns:
            Dict with event counts
        """
        tempo_mod = parameters.get('tempo_modifier', 1.0)

        # Shots (affected by tempo)
        home_shots = max(home_goals * random.randint(8, 12), int(random.randint(8, 15) * tempo_mod))
        away_shots = max(away_goals * random.randint(8, 12), int(random.randint(8, 15) * tempo_mod))

        # Shots on target
        home_shots_on_target = max(home_goals, int(home_shots * random.uniform(0.3, 0.4)))
        away_shots_on_target = max(away_goals, int(away_shots * random.uniform(0.3, 0.4)))

        # Corners
        home_corners = random.randint(3, 8) + (1 if home_goals > away_goals else 0)
        away_corners = random.randint(3, 8) + (1 if away_goals > home_goals else 0)

        # Fouls (high tempo = more fouls)
        base_fouls = random.randint(8, 14)
        home_fouls = int(base_fouls * tempo_mod) + (1 if home_goals < away_goals else 0)
        away_fouls = int(base_fouls * tempo_mod) + (1 if away_goals < home_goals else 0)

        # Cards
        home_yellows = int(home_fouls * random.uniform(0.10, 0.20))
        away_yellows = int(away_fouls * random.uniform(0.10, 0.20))
        home_reds = 1 if random.random() < 0.05 else 0
        away_reds = 1 if random.random() < 0.05 else 0

        # Possession
        total_goals = home_goals + away_goals
        if total_goals > 0:
            home_possession = 45 + (home_goals - away_goals) * 5 + random.randint(-5, 5)
            home_possession = max(30, min(70, home_possession))
        else:
            home_possession = random.randint(45, 55)

        return {
            'home_shots': home_shots,
            'away_shots': away_shots,
            'home_shots_on_target': home_shots_on_target,
            'away_shots_on_target': away_shots_on_target,
            'home_corners': home_corners,
            'away_corners': away_corners,
            'home_fouls': home_fouls,
            'away_fouls': away_fouls,
            'home_yellow_cards': home_yellows,
            'away_yellow_cards': away_yellows,
            'home_red_cards': home_reds,
            'away_red_cards': away_reds,
            'home_possession': home_possession,
            'away_possession': 100 - home_possession
        }

    def _aggregate_results(
        self,
        simulation_results: List[Dict],
        home_team_data: Dict,
        away_team_data: Dict,
        parameters: Dict
    ) -> Dict:
        """
        Aggregate simulation results.

        Returns:
            Final prediction with probabilities and statistics
        """
        # Count outcomes
        home_wins = sum(1 for r in simulation_results if r['outcome'] == 'home_win')
        draws = sum(1 for r in simulation_results if r['outcome'] == 'draw')
        away_wins = sum(1 for r in simulation_results if r['outcome'] == 'away_win')

        total = len(simulation_results)

        # Calculate probabilities
        home_win_prob = home_wins / total
        draw_prob = draws / total
        away_win_prob = away_wins / total

        # Calculate expected goals
        total_home_goals = sum(r['home_goals'] for r in simulation_results)
        total_away_goals = sum(r['away_goals'] for r in simulation_results)

        expected_home_goals = total_home_goals / total
        expected_away_goals = total_away_goals / total

        # Find most common scoreline
        score_counter = defaultdict(int)
        for r in simulation_results:
            score_counter[(r['home_goals'], r['away_goals'])] += 1

        most_common_score = max(score_counter.items(), key=lambda x: x[1])[0]
        predicted_score = f"{most_common_score[0]}-{most_common_score[1]}"

        # Score distribution (top 10)
        score_distribution = {}
        for score, count in sorted(score_counter.items(), key=lambda x: x[1], reverse=True)[:10]:
            score_key = f"{score[0]}-{score[1]}"
            score_distribution[score_key] = round(count / total, 3)

        # Aggregate events
        avg_events = {}
        if simulation_results:
            event_keys = simulation_results[0]['events'].keys()
            for key in event_keys:
                avg_events[key] = round(
                    sum(r['events'][key] for r in simulation_results) / total,
                    1
                )

        # Calculate confidence
        max_prob = max(home_win_prob, draw_prob, away_win_prob)
        if max_prob > 0.55:
            confidence = 'high'
        elif max_prob > 0.40:
            confidence = 'medium'
        else:
            confidence = 'low'

        return {
            'probabilities': {
                'home_win': round(home_win_prob, 3),
                'draw': round(draw_prob, 3),
                'away_win': round(away_win_prob, 3)
            },
            'predicted_score': predicted_score,
            'expected_goals': {
                'home': round(expected_home_goals, 2),
                'away': round(expected_away_goals, 2)
            },
            'score_distribution': score_distribution,
            'confidence': confidence,
            'events': avg_events,
            'metadata': {
                'num_simulations': total,
                'engine': 'IterativeSimulationEngine',
                'version': '2.0.0',
                'parameters_applied': parameters.get('expected_scenario', 'standard')
            }
        }


def get_iterative_engine() -> IterativeSimulationEngine:
    """
    Get iterative simulation engine instance.

    Returns:
        IterativeSimulationEngine instance
    """
    return IterativeSimulationEngine()
