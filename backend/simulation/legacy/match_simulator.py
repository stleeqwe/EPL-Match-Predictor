"""
Integrated Match Simulator
Combines Statistical Engine + Qwen AI Analyzer for complete match simulation

Phase 1 MVP: Quality-focused match prediction
- Loads team/player data from database
- Uses AI for tactical analysis
- Uses statistical engine for Monte Carlo simulation
- Returns comprehensive prediction with analysis
"""

import logging
from typing import Dict, Optional, Tuple
from datetime import datetime

from simulation.statistical_engine import StatisticalMatchEngine
from simulation.qwen_analyzer import QwenMatchAnalyzer

logger = logging.getLogger(__name__)


class MatchSimulator:
    """
    Integrated match simulator combining AI analysis with statistical simulation.

    Phase 1 MVP Workflow:
    1. Load team data (ratings, tactical profiles)
    2. Run AI analysis (Qwen) -> get probability weights
    3. Run statistical simulation with AI weights
    4. Combine results into comprehensive prediction

    Features:
    - AI-guided statistical simulation
    - Comprehensive match analysis
    - User insight integration (MVP priority)
    - Quality-focused predictions
    """

    def __init__(
        self,
        num_simulations: int = 1000,
        enable_ai_analysis: bool = True
    ):
        """
        Initialize match simulator.

        Args:
            num_simulations: Number of Monte Carlo runs
            enable_ai_analysis: Whether to use AI analysis (can disable for testing)
        """
        self.statistical_engine = StatisticalMatchEngine(num_simulations=num_simulations)
        self.ai_analyzer = QwenMatchAnalyzer() if enable_ai_analysis else None
        self.enable_ai = enable_ai_analysis

        logger.info(f"MatchSimulator initialized: {num_simulations} sims, AI={'enabled' if enable_ai_analysis else 'disabled'}")

    def simulate(
        self,
        home_team_name: str,
        away_team_name: str,
        home_team_data: Dict,
        away_team_data: Dict,
        user_insight: Optional[str] = None,
        additional_context: Optional[Dict] = None
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Simulate a match with AI analysis and statistical modeling.

        Args:
            home_team_name: Home team name
            away_team_name: Away team name
            home_team_data: Home team data
                Format: {
                    'overall_rating': float,
                    'tactical_profile': dict,
                    'recent_form': str (optional),
                    'key_players': list (optional)
                }
            away_team_data: Away team data (same format)
            user_insight: User's match analysis/prediction (high priority in MVP)
            additional_context: Additional context (injuries, weather, etc.)

        Returns:
            Tuple of (success, prediction_dict, error_message)
            prediction_dict format:
            {
                'prediction': {
                    'probabilities': dict,
                    'predicted_score': str,
                    'expected_goals': dict,
                    'confidence': str
                },
                'ai_analysis': dict,
                'match_events': dict,
                'metadata': dict
            }
        """
        logger.info(f"Simulating: {home_team_name} vs {away_team_name}")

        # Ensure team names are in data
        if 'name' not in home_team_data:
            home_team_data['name'] = home_team_name
        if 'name' not in away_team_data:
            away_team_data['name'] = away_team_name

        try:
            # Step 1: AI Analysis (if enabled)
            ai_analysis = None
            ai_weights = None

            if self.enable_ai:
                logger.info("Running AI analysis...")

                # Prepare context for AI
                ai_context = additional_context or {}
                if user_insight:
                    ai_context['user_insights'] = user_insight

                # Run AI analysis
                ai_success, ai_analysis, ai_error = self.ai_analyzer.analyze_match(
                    home_team_data,
                    away_team_data,
                    ai_context
                )

                if not ai_success:
                    logger.warning(f"AI analysis failed: {ai_error}, continuing with statistical only")
                else:
                    ai_weights = ai_analysis['probability_weights']
                    logger.info(f"AI weights: {ai_weights}")

            # Step 2: Statistical Simulation
            logger.info("Running statistical simulation...")
            simulation_result = self.statistical_engine.simulate_match(
                home_team_data,
                away_team_data,
                ai_weights=ai_weights
            )

            # Step 3: Combine Results
            prediction = self._build_prediction(
                home_team_name,
                away_team_name,
                simulation_result,
                ai_analysis,
                user_insight
            )

            logger.info(f"Simulation complete: {prediction['prediction']['predicted_score']}")
            return True, prediction, None

        except Exception as e:
            error_msg = f"Simulation failed: {str(e)}"
            logger.error(error_msg)
            import traceback
            traceback.print_exc()
            return False, None, error_msg

    def _build_prediction(
        self,
        home_team_name: str,
        away_team_name: str,
        simulation_result: Dict,
        ai_analysis: Optional[Dict],
        user_insight: Optional[str]
    ) -> Dict:
        """Build comprehensive prediction result."""

        # Extract simulation data
        probabilities = simulation_result['probabilities']
        predicted_score = simulation_result['predicted_score']
        expected_goals = simulation_result['expected_goals']
        confidence = simulation_result['confidence']
        score_distribution = simulation_result['score_distribution']
        events = simulation_result['events']

        # Build prediction object
        prediction = {
            'match': {
                'home_team': home_team_name,
                'away_team': away_team_name,
                'timestamp': datetime.utcnow().isoformat()
            },
            'prediction': {
                'probabilities': probabilities,
                'predicted_score': predicted_score,
                'expected_goals': expected_goals,
                'confidence': confidence,
                'score_distribution': score_distribution
            },
            'match_events': events,
            'ai_analysis': None,
            'user_insight': user_insight,
            'metadata': {
                'simulation_engine': 'StatisticalMatchEngine + QwenAnalyzer',
                'num_simulations': simulation_result['metadata']['num_simulations'],
                'version': '1.0.0-mvp',
                'ai_enabled': ai_analysis is not None
            }
        }

        # Add AI analysis if available
        if ai_analysis:
            prediction['ai_analysis'] = {
                'key_factors': ai_analysis['key_factors'],
                'tactical_insight': ai_analysis['tactical_insight'],
                'reasoning': ai_analysis['reasoning'],
                'confidence': ai_analysis['confidence'],
                'probability_weights': ai_analysis['probability_weights']
            }

        return prediction

    def quick_predict(
        self,
        home_team_name: str,
        away_team_name: str,
        home_rating: float,
        away_rating: float
    ) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Quick prediction using only overall ratings (for testing/API convenience).

        Args:
            home_team_name: Home team name
            away_team_name: Away team name
            home_rating: Home team overall rating (0-100)
            away_rating: Away team overall rating (0-100)

        Returns:
            Tuple of (success, prediction_dict, error_message)
        """
        # Create minimal team data
        home_data = {
            'name': home_team_name,
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
            'name': away_team_name,
            'overall_rating': away_rating,
            'tactical_profile': {
                'attacking_efficiency': away_rating,
                'defensive_stability': away_rating,
                'tactical_organization': away_rating,
                'physicality_stamina': away_rating,
                'psychological_factors': away_rating
            }
        }

        return self.simulate(
            home_team_name,
            away_team_name,
            home_data,
            away_data
        )


# Global simulator instance
_match_simulator = None


def get_match_simulator(
    num_simulations: int = 1000,
    enable_ai: bool = True
) -> MatchSimulator:
    """Get global match simulator instance (singleton)."""
    global _match_simulator
    if _match_simulator is None:
        _match_simulator = MatchSimulator(
            num_simulations=num_simulations,
            enable_ai_analysis=enable_ai
        )
    return _match_simulator


def reset_match_simulator():
    """Reset global simulator (useful for testing)."""
    global _match_simulator
    _match_simulator = None
