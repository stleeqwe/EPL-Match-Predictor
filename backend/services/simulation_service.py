"""
Match Simulation Service
AI Match Simulation v3.0

Main orchestrator for AI-powered match predictions with caching and tier-based features.
"""

import redis
import json
from typing import Dict, Optional, Tuple
import logging
from datetime import datetime, timedelta
import hashlib

from ai.claude_client import get_claude_client
from services.data_aggregation_service import get_data_aggregation_service


# Configure logging
logger = logging.getLogger(__name__)


class SimulationService:
    """
    Main simulation service orchestrating all AI match prediction components.

    Features:
    - Data aggregation from multiple sources
    - Tier-based Claude AI analysis
    - Redis caching (1 hour TTL)
    - Usage tracking
    """

    def __init__(self):
        """Initialize simulation service."""
        self.claude_client = get_claude_client()
        self.data_service = get_data_aggregation_service()

        # Initialize Redis cache
        try:
            import os
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_available = True
            logger.info("Redis cache initialized")
        except Exception as e:
            logger.warning(f"Redis not available, using memory cache: {str(e)}")
            self.redis_client = None
            self.redis_available = False
            self._memory_cache = {}

        self.cache_ttl = 3600  # 1 hour

    # ==========================================================================
    # MAIN SIMULATION METHOD
    # ==========================================================================

    def simulate_match(self, home_team: str, away_team: str, user_id: str, tier: str,
                      weights: Optional[Dict] = None) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Simulate a match using AI.

        Args:
            home_team: Home team name
            away_team: Away team name
            user_id: User ID for tracking
            tier: User subscription tier
            weights: Custom data source weights (optional)
                    Format: {'user_value': 0.65, 'odds': 0.20, 'stats': 0.15}

        Returns:
            Tuple of (success, result_dict, error_message)
        """
        logger.info(f"Simulating {home_team} vs {away_team} for user {user_id} (tier={tier}, weights={weights})")

        # Check cache (include weights in cache key)
        cache_key = self._generate_cache_key(home_team, away_team, tier, weights)
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            logger.info(f"Cache hit for {home_team} vs {away_team}")
            cached_result['from_cache'] = True
            return True, cached_result, None

        # Aggregate data (pass weights)
        try:
            data_context = self.data_service.aggregate_match_data(home_team, away_team, tier, weights)
        except Exception as e:
            error_msg = f"Data aggregation failed: {str(e)}"
            logger.error(error_msg)
            return False, None, error_msg

        # Run AI simulation
        success, prediction, usage_data, error = self.claude_client.simulate_match(
            home_team=home_team,
            away_team=away_team,
            tier=tier,
            data_context=data_context
        )

        if not success:
            logger.error(f"AI simulation failed: {error}")
            return False, None, error

        # Build result (include weights used)
        result = {
            'home_team': home_team,
            'away_team': away_team,
            'prediction': prediction.get('prediction', {}),
            'analysis': prediction.get('analysis', {}),
            'summary': prediction.get('summary', ''),
            'recommendation': prediction.get('recommendation') if tier == 'PRO' else None,
            'tier': tier,
            'weights_used': weights if weights else {'user_value': 0.65, 'odds': 0.20, 'stats': 0.15},
            'usage': usage_data,
            'from_cache': False,
            'timestamp': datetime.utcnow().isoformat()
        }

        # Cache result
        self._save_to_cache(cache_key, result)

        logger.info(f"Simulation complete (tokens={usage_data['total_tokens']}, cost=${usage_data['cost_usd']:.6f})")
        return True, result, None

    # ==========================================================================
    # CACHING
    # ==========================================================================

    def _generate_cache_key(self, home_team: str, away_team: str, tier: str,
                           weights: Optional[Dict] = None) -> str:
        """Generate cache key for match simulation (including weights)."""
        # Include weights in cache key so different weight configs have different caches
        weights_str = ""
        if weights:
            weights_str = f":{weights.get('user_value', 0.65)}:{weights.get('odds', 0.20)}:{weights.get('stats', 0.15)}"
        key_string = f"simulation:{home_team}:{away_team}:{tier}{weights_str}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_from_cache(self, key: str) -> Optional[Dict]:
        """Get simulation result from cache."""
        try:
            if self.redis_available:
                cached = self.redis_client.get(key)
                if cached:
                    return json.loads(cached)
            else:
                # Memory cache
                if key in self._memory_cache:
                    cached_data, expires_at = self._memory_cache[key]
                    if datetime.utcnow() < expires_at:
                        return cached_data
                    else:
                        del self._memory_cache[key]
            return None
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None

    def _save_to_cache(self, key: str, data: Dict):
        """Save simulation result to cache."""
        try:
            if self.redis_available:
                self.redis_client.setex(key, self.cache_ttl, json.dumps(data))
            else:
                # Memory cache
                expires_at = datetime.utcnow() + timedelta(seconds=self.cache_ttl)
                self._memory_cache[key] = (data, expires_at)
        except Exception as e:
            logger.error(f"Cache save error: {str(e)}")


# Global service instance
_simulation_service = None


def get_simulation_service() -> SimulationService:
    """Get global simulation service instance (singleton)."""
    global _simulation_service
    if _simulation_service is None:
        _simulation_service = SimulationService()
    return _simulation_service
