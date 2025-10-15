"""
Statistical Match Engine
EPL-calibrated Monte Carlo simulation engine

Phase 1 MVP: Focus on result quality, not performance
- Uses EPL baseline statistics (2.8 goals/game average)
- Event-based probability calculations
- Monte Carlo simulation (1000 runs)
- Integrates AI probability weights
"""

import random
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


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
    common_scores = {
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

    # Event probabilities per match
    avg_corners_per_team: float = 5.5
    avg_fouls_per_team: float = 11.0
    avg_yellow_cards_per_team: float = 1.8
    avg_red_cards_per_match: float = 0.15


class StatisticalMatchEngine:
    """
    Statistical match simulation engine using Monte Carlo methods.

    Features:
    - EPL-calibrated baseline statistics
    - Team strength differential modeling
    - AI probability weight integration
    - Event-based simulation
    - Realistic outcome distributions
    """

    def __init__(self, num_simulations: int = 1000):
        """
        Initialize statistical engine.

        Args:
            num_simulations: Number of Monte Carlo runs (default 1000 for MVP)
        """
        self.num_simulations = num_simulations
        self.baseline = EPLBaseline()
        logger.info(f"StatisticalMatchEngine initialized: {num_simulations} simulations per match")

    def simulate_match(
        self,
        home_team_data: Dict,
        away_team_data: Dict,
        ai_weights: Optional[Dict] = None
    ) -> Dict:
        """
        Simulate a match using Monte Carlo method.

        Args:
            home_team_data: Home team stats and ratings
                Format: {
                    'name': str,
                    'overall_rating': float (0-100),
                    'tactical_profile': {
                        'attacking_efficiency': float (0-100),
                        'defensive_stability': float (0-100),
                        'tactical_organization': float (0-100),
                        ...
                    },
                    'squad_quality': float (0-100)
                }
            away_team_data: Away team stats (same format)
            ai_weights: Optional AI-generated probability adjustments
                Format: {
                    'home_win_boost': float (0-1),
                    'draw_boost': float (0-1),
                    'away_win_boost': float (0-1)
                }

        Returns:
            Dictionary with simulation results:
            {
                'probabilities': {
                    'home_win': float,
                    'draw': float,
                    'away_win': float
                },
                'predicted_score': str,
                'expected_goals': {
                    'home': float,
                    'away': float
                },
                'score_distribution': dict,
                'confidence': str,
                'events': dict
            }
        """
        logger.info(f"Simulating {home_team_data['name']} vs {away_team_data['name']}")

        # Calculate team strength differential
        strength_diff = self._calculate_strength_differential(home_team_data, away_team_data)

        # Adjust base probabilities using team strength
        base_probs = self._calculate_base_probabilities(strength_diff)

        # Apply AI weights if provided
        if ai_weights:
            base_probs = self._apply_ai_weights(base_probs, ai_weights)

        # Run Monte Carlo simulations
        simulation_results = self._run_simulations(
            home_team_data,
            away_team_data,
            base_probs
        )

        # Aggregate results
        result = self._aggregate_results(simulation_results, home_team_data, away_team_data)

        logger.info(f"Simulation complete: {result['probabilities']}")
        return result

    def _calculate_strength_differential(
        self,
        home_team_data: Dict,
        away_team_data: Dict
    ) -> float:
        """
        Calculate relative strength difference between teams.

        Returns:
            Float between -1 and 1 (positive = home advantage)
        """
        # Get overall ratings
        home_rating = home_team_data.get('overall_rating', 75.0)
        away_rating = away_team_data.get('overall_rating', 75.0)

        # Calculate raw differential (scale: 0-100)
        raw_diff = home_rating - away_rating

        # Add home advantage (EPL home teams typically +3-5 rating points)
        home_advantage = 4.0
        adjusted_diff = raw_diff + home_advantage

        # Normalize to -1 to 1 range (assuming max diff is ~30 rating points)
        normalized_diff = adjusted_diff / 30.0
        normalized_diff = max(-1.0, min(1.0, normalized_diff))

        logger.debug(f"Strength differential: {normalized_diff:.3f} (home: {home_rating}, away: {away_rating})")
        return normalized_diff

    def _calculate_base_probabilities(self, strength_diff: float) -> Dict[str, float]:
        """
        Calculate base outcome probabilities from strength differential.

        Args:
            strength_diff: Normalized strength difference (-1 to 1)

        Returns:
            Dict with home_win, draw, away_win probabilities
        """
        # Start with EPL baseline
        base_home = self.baseline.home_win_rate
        base_draw = self.baseline.draw_rate
        base_away = self.baseline.away_win_rate

        # Adjust based on strength differential
        # Positive diff = home stronger, negative = away stronger
        # Use non-linear scaling for large differences (squared for stronger teams)
        adjustment_factor = abs(strength_diff) * 0.45  # Max 45% shift
        if abs(strength_diff) > 0.6:
            adjustment_factor = min(0.5, adjustment_factor * 1.2)  # Boost for very strong teams

        if strength_diff > 0:
            # Home team stronger
            home_prob = base_home + (adjustment_factor * (1 - base_home))
            away_prob = base_away * (1 - adjustment_factor)
            draw_prob = 1 - home_prob - away_prob
        elif strength_diff < 0:
            # Away team stronger
            away_prob = base_away + (adjustment_factor * (1 - base_away))
            home_prob = base_home * (1 - adjustment_factor)
            draw_prob = 1 - home_prob - away_prob
        else:
            # Even teams
            home_prob = base_home
            draw_prob = base_draw
            away_prob = base_away

        # Ensure probabilities sum to 1.0
        total = home_prob + draw_prob + away_prob
        home_prob /= total
        draw_prob /= total
        away_prob /= total

        return {
            'home_win': home_prob,
            'draw': draw_prob,
            'away_win': away_prob
        }

    def _apply_ai_weights(
        self,
        base_probs: Dict[str, float],
        ai_weights: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Apply AI-generated probability adjustments to base probabilities.

        Args:
            base_probs: Base probabilities from statistical model
            ai_weights: AI adjustments (boost factors 0-1)

        Returns:
            Adjusted probabilities
        """
        # Apply multiplicative boosts
        home_boost = ai_weights.get('home_win_boost', 1.0)
        draw_boost = ai_weights.get('draw_boost', 1.0)
        away_boost = ai_weights.get('away_win_boost', 1.0)

        adjusted_home = base_probs['home_win'] * home_boost
        adjusted_draw = base_probs['draw'] * draw_boost
        adjusted_away = base_probs['away_win'] * away_boost

        # Normalize to sum to 1.0
        total = adjusted_home + adjusted_draw + adjusted_away

        return {
            'home_win': adjusted_home / total,
            'draw': adjusted_draw / total,
            'away_win': adjusted_away / total
        }

    def _run_simulations(
        self,
        home_team_data: Dict,
        away_team_data: Dict,
        outcome_probs: Dict[str, float]
    ) -> List[Dict]:
        """
        Run Monte Carlo simulations.

        Returns:
            List of simulation results
        """
        results = []

        for i in range(self.num_simulations):
            sim_result = self._simulate_single_match(
                home_team_data,
                away_team_data,
                outcome_probs
            )
            results.append(sim_result)

        return results

    def _simulate_single_match(
        self,
        home_team_data: Dict,
        away_team_data: Dict,
        outcome_probs: Dict[str, float]
    ) -> Dict:
        """
        Simulate a single match iteration.

        Returns:
            Dict with match outcome: {
                'home_goals': int,
                'away_goals': int,
                'outcome': str ('home_win'|'draw'|'away_win'),
                'events': dict
            }
        """
        # Determine match outcome based on probabilities
        rand = random.random()
        cumulative = 0.0
        outcome = None

        for outcome_type, prob in outcome_probs.items():
            cumulative += prob
            if rand <= cumulative:
                outcome = outcome_type
                break

        if outcome is None:
            outcome = 'draw'  # Fallback

        # Generate realistic scoreline based on outcome
        home_goals, away_goals = self._generate_scoreline(
            outcome,
            home_team_data,
            away_team_data
        )

        # Generate match events
        events = self._generate_events(home_team_data, away_team_data, home_goals, away_goals)

        return {
            'home_goals': home_goals,
            'away_goals': away_goals,
            'outcome': outcome,
            'events': events
        }

    def _generate_scoreline(
        self,
        outcome: str,
        home_team_data: Dict,
        away_team_data: Dict
    ) -> Tuple[int, int]:
        """
        Generate realistic scoreline based on outcome and team strengths.

        Returns:
            Tuple of (home_goals, away_goals)
        """
        # Get attacking/defensive ratings
        home_attack = home_team_data.get('tactical_profile', {}).get('attacking_efficiency', 75.0)
        home_defense = home_team_data.get('tactical_profile', {}).get('defensive_stability', 75.0)
        away_attack = away_team_data.get('tactical_profile', {}).get('attacking_efficiency', 75.0)
        away_defense = away_team_data.get('tactical_profile', {}).get('defensive_stability', 75.0)

        # Calculate expected goals based on attack vs defense
        # EPL average is 2.8 goals/match (1.4 per team)
        # FIX: 목표 평균 득점 2.8을 만들기 위한 캘리브레이션
        # 역산: 평균 팀 능력치 75일 때 각 팀이 1.4골씩 넣어야 함
        # home_xg = 0.75 * base * (1 - 0.75 * def_factor)
        # 1.4 = 0.75 * base * (1 - 0.75 * 0.3) = 0.75 * base * 0.775
        # base = 1.4 / (0.75 * 0.775) = 2.41
        home_xg_base = (home_attack / 100.0) * 2.5 * (1 - away_defense / 100.0 * 0.3)
        away_xg_base = (away_attack / 100.0) * 2.3 * (1 - home_defense / 100.0 * 0.3)

        # Add randomness using Poisson-like distribution
        if outcome == 'home_win':
            home_goals = max(1, int(random.gauss(home_xg_base * 1.3, 0.8)))
            away_goals = max(0, int(random.gauss(away_xg_base * 0.8, 0.6)))
            # Ensure home actually wins
            if home_goals <= away_goals:
                home_goals = away_goals + random.randint(1, 2)

        elif outcome == 'away_win':
            home_goals = max(0, int(random.gauss(home_xg_base * 0.8, 0.6)))
            away_goals = max(1, int(random.gauss(away_xg_base * 1.3, 0.8)))
            # Ensure away actually wins
            if away_goals <= home_goals:
                away_goals = home_goals + random.randint(1, 2)

        else:  # draw
            # Similar goals for both teams
            avg_goals = (home_xg_base + away_xg_base) / 2
            goals = max(0, int(random.gauss(avg_goals, 0.5)))
            home_goals = goals
            away_goals = goals

        # Cap at realistic maximum (very rare to see 7+ goals)
        home_goals = min(home_goals, 6)
        away_goals = min(away_goals, 6)

        return home_goals, away_goals

    def _generate_events(
        self,
        home_team_data: Dict,
        away_team_data: Dict,
        home_goals: int,
        away_goals: int
    ) -> Dict:
        """
        Generate match events (shots, corners, fouls, cards).

        Returns:
            Dict with event counts
        """
        # Calculate shots based on goals (typically 10-15 shots per goal)
        home_shots = max(home_goals * random.randint(8, 12), random.randint(8, 15))
        away_shots = max(away_goals * random.randint(8, 12), random.randint(8, 15))

        # Shots on target (typically 30-40% of total shots)
        home_shots_on_target = max(home_goals, int(home_shots * random.uniform(0.3, 0.4)))
        away_shots_on_target = max(away_goals, int(away_shots * random.uniform(0.3, 0.4)))

        # Corners - attacking teams get more
        home_corners = random.randint(3, 8) + (1 if home_goals > away_goals else 0)
        away_corners = random.randint(3, 8) + (1 if away_goals > home_goals else 0)

        # Fouls - losing teams tend to commit more
        home_fouls = random.randint(8, 14) + (1 if home_goals < away_goals else 0)
        away_fouls = random.randint(8, 14) + (1 if away_goals < home_goals else 0)

        # Cards - based on fouls
        home_yellows = int(home_fouls * random.uniform(0.10, 0.20))
        away_yellows = int(away_fouls * random.uniform(0.10, 0.20))
        home_reds = 1 if random.random() < 0.05 else 0
        away_reds = 1 if random.random() < 0.05 else 0

        # Possession - typically correlates with goals
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
        away_team_data: Dict
    ) -> Dict:
        """
        Aggregate Monte Carlo simulation results.

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

        # Get score distribution (top 10)
        score_distribution = {}
        for score, count in sorted(score_counter.items(), key=lambda x: x[1], reverse=True)[:10]:
            score_key = f"{score[0]}-{score[1]}"
            score_distribution[score_key] = round(count / total, 3)

        # Aggregate events
        avg_events = {}
        event_keys = simulation_results[0]['events'].keys()
        for key in event_keys:
            avg_events[key] = round(
                sum(r['events'][key] for r in simulation_results) / total,
                1
            )

        # Calculate confidence based on probability spread
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
                'num_simulations': self.num_simulations,
                'engine': 'StatisticalMatchEngine',
                'version': '1.0.0-mvp'
            }
        }

    def validate_against_baseline(self, num_validation_matches: int = 100) -> Dict:
        """
        Validate engine against EPL baseline statistics.

        Runs simulations of evenly-matched teams and checks if results
        match EPL averages (for quality assurance).

        Args:
            num_validation_matches: Number of test matches to simulate

        Returns:
            Validation report with quality metrics
        """
        logger.info(f"Running validation: {num_validation_matches} test matches")

        # Create evenly matched team data
        balanced_team = {
            'name': 'Test Team',
            'overall_rating': 75.0,
            'tactical_profile': {
                'attacking_efficiency': 75.0,
                'defensive_stability': 75.0,
                'tactical_organization': 75.0,
                'physicality_stamina': 75.0,
                'psychological_factors': 75.0
            },
            'squad_quality': 75.0
        }

        validation_results = []
        for _ in range(num_validation_matches):
            result = self.simulate_match(balanced_team, balanced_team)
            validation_results.append(result)

        # Aggregate validation metrics
        avg_total_goals = sum(
            r['expected_goals']['home'] + r['expected_goals']['away']
            for r in validation_results
        ) / num_validation_matches

        avg_home_win_prob = sum(r['probabilities']['home_win'] for r in validation_results) / num_validation_matches
        avg_draw_prob = sum(r['probabilities']['draw'] for r in validation_results) / num_validation_matches
        avg_away_win_prob = sum(r['probabilities']['away_win'] for r in validation_results) / num_validation_matches

        # Compare to baseline
        goals_deviation = abs(avg_total_goals - self.baseline.avg_goals_per_match)
        home_prob_deviation = abs(avg_home_win_prob - self.baseline.home_win_rate)

        quality_score = 100 - (goals_deviation / self.baseline.avg_goals_per_match * 50) - (home_prob_deviation * 100)
        quality_score = max(0, min(100, quality_score))

        return {
            'validation_matches': num_validation_matches,
            'metrics': {
                'avg_total_goals': round(avg_total_goals, 2),
                'baseline_goals': self.baseline.avg_goals_per_match,
                'goals_deviation': round(goals_deviation, 2),
                'avg_home_win_prob': round(avg_home_win_prob, 3),
                'baseline_home_win': self.baseline.home_win_rate,
                'avg_draw_prob': round(avg_draw_prob, 3),
                'baseline_draw': self.baseline.draw_rate,
                'avg_away_win_prob': round(avg_away_win_prob, 3),
                'baseline_away_win': self.baseline.away_win_rate
            },
            'quality_score': round(quality_score, 1),
            'status': 'PASS' if quality_score > 70 else 'FAIL',
            'notes': 'Engine calibrated to EPL 2023/24 season statistics'
        }
