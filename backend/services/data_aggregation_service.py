"""
Data Aggregation Service
AI Match Simulation v3.0

Aggregates data from multiple sources for AI match simulation.
Sources:
- Sharp Vision AI (existing /api/match-predictions)
- FPL API (Fantasy Premier League)
- Football-Data.org API
"""

import requests
from typing import Dict, Optional, Tuple, List
import logging
from datetime import datetime
import os


# Configure logging
logger = logging.getLogger(__name__)


class DataAggregationService:
    """
    Aggregates match data from multiple sources.

    Data hierarchy (as per spec):
    - User custom ratings: 65% weight
    - Sharp Vision AI: 20% weight
    - External APIs: 15% weight
    """

    def __init__(self):
        """Initialize data aggregation service."""
        # API endpoints
        self.sharp_vision_url = os.getenv('SHARP_VISION_URL', 'http://localhost:5001/api/match-predictions')
        self.fpl_api_url = os.getenv('FPL_API_URL', 'https://fantasy.premierleague.com/api')
        self.football_data_url = os.getenv('FOOTBALL_DATA_URL', 'https://api.football-data.org/v4')
        self.football_data_token = os.getenv('FOOTBALL_DATA_TOKEN', '')

        # Cache TTL
        self.cache_ttl = int(os.getenv('DATA_CACHE_TTL', '3600'))

    # ============================================================================
    # MAIN AGGREGATION METHOD
    # ============================================================================

    def aggregate_match_data(self, home_team: str, away_team: str, tier: str, weights: Optional[Dict] = None) -> Dict:
        """
        Aggregate all available data for a match.

        Args:
            home_team: Home team name
            away_team: Away team name
            tier: User subscription tier
            weights: Custom data source weights (optional)
                    Format: {'user_value': 0.65, 'odds': 0.20, 'stats': 0.15}

        Returns:
            Dictionary containing aggregated data
        """
        # Set default weights if not provided
        if weights is None:
            weights = {
                'user_value': 0.65,
                'odds': 0.20,
                'stats': 0.15
            }

        logger.info(f"Aggregating data for {home_team} vs {away_team} (tier={tier}, weights={weights})")

        data = {
            'home_team': home_team,
            'away_team': away_team,
            'tier': tier,
            'weights': weights,
            'timestamp': datetime.utcnow().isoformat()
        }

        # Get Sharp Vision AI predictions (20% weight)
        sharp_data = self._get_sharp_vision_data(home_team, away_team)
        if sharp_data:
            data['sharp_vision'] = sharp_data

        # Get FPL data (part of 15% external)
        fpl_data = self._get_fpl_data(home_team, away_team)
        if fpl_data:
            data['fpl_data'] = fpl_data

        # Get Football-Data standings (part of 15% external)
        # Only for PRO tier to save API calls
        if tier == 'PRO':
            standings_data = self._get_standings_data()
            if standings_data:
                data['standings'] = standings_data

        # Build context for Claude (including weights)
        context = self._build_context_for_claude(data, weights)

        return context

    # ============================================================================
    # SHARP VISION AI
    # ============================================================================

    def _get_sharp_vision_data(self, home_team: str, away_team: str) -> Optional[Dict]:
        """
        Get predictions from Sharp Vision AI endpoint.

        Args:
            home_team: Home team name
            away_team: Away team name

        Returns:
            Sharp Vision prediction data or None
        """
        try:
            # Call existing /api/match-predictions endpoint
            response = requests.get(self.sharp_vision_url, timeout=10)
            response.raise_for_status()

            predictions = response.json().get('predictions', [])

            # Find matching fixture
            for pred in predictions:
                if (pred.get('home_team') == home_team and
                    pred.get('away_team') == away_team):
                    return {
                        'home_win_prob': pred.get('home_win_probability'),
                        'draw_prob': pred.get('draw_probability'),
                        'away_win_prob': pred.get('away_win_probability'),
                        'predicted_score': pred.get('predicted_score'),
                        'confidence': pred.get('confidence'),
                        'sharp_odds': pred.get('odds', {})
                    }

            logger.warning(f"No Sharp Vision data found for {home_team} vs {away_team}")
            return None

        except Exception as e:
            logger.error(f"Error fetching Sharp Vision data: {str(e)}")
            return None

    # ============================================================================
    # FPL API
    # ============================================================================

    def _get_fpl_data(self, home_team: str, away_team: str) -> Optional[Dict]:
        """
        Get team data from FPL API.

        Args:
            home_team: Home team name
            away_team: Away team name

        Returns:
            FPL data or None
        """
        try:
            # Get bootstrap-static data (teams, players, fixtures)
            response = requests.get(f"{self.fpl_api_url}/bootstrap-static/", timeout=10)
            response.raise_for_status()
            data = response.json()

            teams = data.get('teams', [])

            # Map team names to FPL team IDs
            home_team_data = self._find_fpl_team(teams, home_team)
            away_team_data = self._find_fpl_team(teams, away_team)

            if not home_team_data or not away_team_data:
                logger.warning(f"Could not find FPL data for teams")
                return None

            return {
                'home': {
                    'name': home_team_data.get('name'),
                    'strength': home_team_data.get('strength'),
                    'strength_overall_home': home_team_data.get('strength_overall_home'),
                    'strength_attack_home': home_team_data.get('strength_attack_home'),
                    'strength_defence_home': home_team_data.get('strength_defence_home'),
                    'position': home_team_data.get('position'),
                    'played': home_team_data.get('played'),
                    'win': home_team_data.get('win'),
                    'draw': home_team_data.get('draw'),
                    'loss': home_team_data.get('loss'),
                    'points': home_team_data.get('points')
                },
                'away': {
                    'name': away_team_data.get('name'),
                    'strength': away_team_data.get('strength'),
                    'strength_overall_away': away_team_data.get('strength_overall_away'),
                    'strength_attack_away': away_team_data.get('strength_attack_away'),
                    'strength_defence_away': away_team_data.get('strength_defence_away'),
                    'position': away_team_data.get('position'),
                    'played': away_team_data.get('played'),
                    'win': away_team_data.get('win'),
                    'draw': away_team_data.get('draw'),
                    'loss': away_team_data.get('loss'),
                    'points': away_team_data.get('points')
                }
            }

        except Exception as e:
            logger.error(f"Error fetching FPL data: {str(e)}")
            return None

    def _find_fpl_team(self, teams: List[Dict], team_name: str) -> Optional[Dict]:
        """Find FPL team by name (fuzzy matching)."""
        # Normalize team name for matching
        normalized_name = team_name.lower().replace(' ', '')

        for team in teams:
            fpl_name = team.get('name', '').lower().replace(' ', '')
            fpl_short_name = team.get('short_name', '').lower().replace(' ', '')

            if (normalized_name in fpl_name or
                fpl_name in normalized_name or
                normalized_name == fpl_short_name):
                return team

        return None

    # ============================================================================
    # FOOTBALL-DATA.ORG API
    # ============================================================================

    def _get_standings_data(self) -> Optional[Dict]:
        """
        Get Premier League standings from Football-Data.org.

        Returns:
            Standings data or None
        """
        try:
            if not self.football_data_token:
                logger.warning("Football-Data API token not configured")
                return None

            headers = {'X-Auth-Token': self.football_data_token}

            # Premier League competition ID = 2021
            response = requests.get(
                f"{self.football_data_url}/competitions/2021/standings",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()
            standings = data.get('standings', [])

            if not standings:
                return None

            # Get overall standings (type TOTAL)
            for standing_group in standings:
                if standing_group.get('type') == 'TOTAL':
                    table = standing_group.get('table', [])
                    return {
                        'table': [
                            {
                                'position': team.get('position'),
                                'team': team.get('team', {}).get('name'),
                                'played': team.get('playedGames'),
                                'won': team.get('won'),
                                'draw': team.get('draw'),
                                'lost': team.get('lost'),
                                'points': team.get('points'),
                                'goals_for': team.get('goalsFor'),
                                'goals_against': team.get('goalsAgainst'),
                                'goal_difference': team.get('goalDifference'),
                                'form': team.get('form')
                            }
                            for team in table
                        ],
                        'updated': data.get('season', {}).get('currentMatchday')
                    }

            return None

        except Exception as e:
            logger.error(f"Error fetching Football-Data standings: {str(e)}")
            return None

    # ============================================================================
    # CONTEXT BUILDING
    # ============================================================================

    def _build_context_for_claude(self, data: Dict, weights: Dict) -> Dict:
        """
        Build structured context for Claude AI.

        Args:
            data: Raw aggregated data
            weights: Data source weights

        Returns:
            Structured context dictionary
        """
        context = {
            'weights': weights  # Include weights in context
        }

        # Sharp Vision AI data
        if 'sharp_vision' in data:
            sharp = data['sharp_vision']
            context['sharp_odds'] = {
                'home_win': sharp.get('home_win_prob'),
                'draw': sharp.get('draw_prob'),
                'away_win': sharp.get('away_win_prob'),
                'predicted_score': sharp.get('predicted_score'),
                'sharp_confidence': sharp.get('confidence')
            }

        # FPL data - Squad ratings
        if 'fpl_data' in data:
            fpl = data['fpl_data']
            context['squad_ratings'] = {
                'home': {
                    'overall_strength': fpl['home'].get('strength_overall_home'),
                    'attack': fpl['home'].get('strength_attack_home'),
                    'defence': fpl['home'].get('strength_defence_home')
                },
                'away': {
                    'overall_strength': fpl['away'].get('strength_overall_away'),
                    'attack': fpl['away'].get('strength_attack_away'),
                    'defence': fpl['away'].get('strength_defence_away')
                }
            }

            context['recent_form'] = {
                'home': f"{fpl['home'].get('win', 0)}W-{fpl['home'].get('draw', 0)}D-{fpl['home'].get('loss', 0)}L",
                'away': f"{fpl['away'].get('win', 0)}W-{fpl['away'].get('draw', 0)}D-{fpl['away'].get('loss', 0)}L"
            }

            context['league_position'] = {
                'home': f"{fpl['home'].get('position')}th ({fpl['home'].get('points')} pts)",
                'away': f"{fpl['away'].get('position')}th ({fpl['away'].get('points')} pts)"
            }

        # Standings data (PRO only)
        if 'standings' in data:
            standings = data['standings']
            context['detailed_standings'] = standings

        return context


# Global service instance
_data_aggregation_service = None


def get_data_aggregation_service() -> DataAggregationService:
    """Get global data aggregation service instance (singleton)."""
    global _data_aggregation_service
    if _data_aggregation_service is None:
        _data_aggregation_service = DataAggregationService()
    return _data_aggregation_service
