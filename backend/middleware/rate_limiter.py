"""
Rate Limiting Middleware
AI Match Simulation v3.0

Rate limiting for API endpoints based on user tier.
- BASIC: 5 requests/hour for simulation
- PRO: Unlimited
- Supports both Redis and in-memory storage
"""

from functools import wraps
from flask import request, jsonify, g
from datetime import datetime, timedelta
from typing import Dict, Optional
import logging
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    """In-memory rate limiter (fallback when Redis unavailable)"""

    def __init__(self):
        self.storage: Dict[str, Dict] = defaultdict(dict)
        self.lock = threading.Lock()

    def get(self, key: str) -> Optional[int]:
        """Get current count for key"""
        with self.lock:
            data = self.storage.get(key)
            if data and data['expires'] > datetime.utcnow():
                return data['count']
            return None

    def set(self, key: str, count: int, ttl: int):
        """Set count with TTL"""
        with self.lock:
            self.storage[key] = {
                'count': count,
                'expires': datetime.utcnow() + timedelta(seconds=ttl)
            }

    def incr(self, key: str) -> int:
        """Increment counter"""
        with self.lock:
            data = self.storage.get(key)
            if data and data['expires'] > datetime.utcnow():
                data['count'] += 1
                return data['count']
            return 1

    def cleanup(self):
        """Remove expired entries"""
        with self.lock:
            now = datetime.utcnow()
            expired = [k for k, v in self.storage.items() if v['expires'] <= now]
            for k in expired:
                del self.storage[k]


class RateLimiter:
    """Rate limiter with Redis and in-memory fallback"""

    def __init__(self, redis_client=None):
        """
        Initialize rate limiter

        Args:
            redis_client: Redis client (optional)
        """
        self.redis = redis_client
        self.memory_storage = InMemoryRateLimiter()

        # Rate limits configuration
        self.limits = {
            'BASIC': {
                'simulation': {'count': 5, 'window': 3600},  # 5/hour
                'api': {'count': 100, 'window': 3600}  # 100/hour
            },
            'PRO': {
                'simulation': {'count': None, 'window': None},  # Unlimited
                'api': {'count': 1000, 'window': 3600}  # 1000/hour
            }
        }

    def check_limit(
        self,
        user_id: str,
        tier: str,
        endpoint: str
    ) -> Dict:
        """
        Check if request is within rate limit

        Args:
            user_id: User ID
            tier: User tier (BASIC/PRO)
            endpoint: Endpoint name (simulation/api)

        Returns:
            Dict with allowed, remaining, reset_at
        """
        # Get limit config
        limit_config = self.limits.get(tier, {}).get(endpoint)

        # Unlimited for PRO simulation
        if not limit_config or limit_config['count'] is None:
            return {
                'allowed': True,
                'remaining': None,
                'reset_at': None
            }

        # Generate key
        window_key = self._get_window_key(limit_config['window'])
        key = f"rate_limit:{user_id}:{endpoint}:{window_key}"

        # Check using Redis or memory
        if self.redis:
            return self._check_redis(key, limit_config)
        else:
            return self._check_memory(key, limit_config)

    def _check_redis(self, key: str, config: Dict) -> Dict:
        """Check rate limit using Redis"""
        try:
            current = self.redis.get(key)

            if current is None:
                # First request in window
                self.redis.setex(key, config['window'], 1)
                return {
                    'allowed': True,
                    'remaining': config['count'] - 1,
                    'reset_at': self._get_reset_time(config['window'])
                }

            current = int(current)

            if current >= config['count']:
                # Limit exceeded
                return {
                    'allowed': False,
                    'remaining': 0,
                    'reset_at': self._get_reset_time(config['window'])
                }

            # Increment counter
            self.redis.incr(key)

            return {
                'allowed': True,
                'remaining': config['count'] - current - 1,
                'reset_at': self._get_reset_time(config['window'])
            }

        except Exception as e:
            logger.error(f"Redis error, falling back to memory: {e}")
            return self._check_memory(key, config)

    def _check_memory(self, key: str, config: Dict) -> Dict:
        """Check rate limit using in-memory storage"""
        current = self.memory_storage.get(key)

        if current is None:
            # First request in window
            self.memory_storage.set(key, 1, config['window'])
            return {
                'allowed': True,
                'remaining': config['count'] - 1,
                'reset_at': self._get_reset_time(config['window'])
            }

        if current >= config['count']:
            # Limit exceeded
            return {
                'allowed': False,
                'remaining': 0,
                'reset_at': self._get_reset_time(config['window'])
            }

        # Increment counter
        new_count = self.memory_storage.incr(key)

        return {
            'allowed': True,
            'remaining': config['count'] - new_count,
            'reset_at': self._get_reset_time(config['window'])
        }

    def _get_window_key(self, window: int) -> str:
        """Get current time window key"""
        now = datetime.utcnow()
        # Round to window (e.g., hour)
        if window == 3600:  # 1 hour
            return now.strftime('%Y%m%d%H')
        else:
            # For other windows, use timestamp divided by window
            timestamp = int(now.timestamp())
            window_start = timestamp - (timestamp % window)
            return str(window_start)

    def _get_reset_time(self, window: int) -> str:
        """Calculate reset time"""
        now = datetime.utcnow()
        if window == 3600:  # 1 hour
            reset = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        else:
            reset = now + timedelta(seconds=window)
        return reset.isoformat()


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def init_rate_limiter(redis_client=None):
    """Initialize global rate limiter"""
    global _rate_limiter
    _rate_limiter = RateLimiter(redis_client)
    logger.info("Rate limiter initialized")


def get_rate_limiter() -> RateLimiter:
    """Get rate limiter instance"""
    if _rate_limiter is None:
        # Auto-initialize with memory storage
        init_rate_limiter()
    return _rate_limiter


def rate_limit(endpoint: str = 'api'):
    """
    Rate limiting decorator

    Args:
        endpoint: Endpoint type (simulation/api)

    Usage:
        @rate_limit('simulation')
        def my_endpoint():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get user info from g (set by auth middleware)
            user_id = getattr(g, 'user_id', None)
            tier = getattr(g, 'user_tier', 'BASIC')

            if not user_id:
                # No user = no rate limiting (or could enforce stricter limits)
                return f(*args, **kwargs)

            # Check rate limit
            limiter = get_rate_limiter()
            result = limiter.check_limit(user_id, tier, endpoint)

            # Add headers
            response_data = None
            status_code = 200

            if not result['allowed']:
                # Rate limit exceeded
                response_data = {
                    'error': 'Rate limit exceeded',
                    'message': f"{tier} tier allows limited requests per hour",
                    'reset_at': result['reset_at'],
                    'upgrade_url': '/pricing' if tier == 'BASIC' else None
                }
                status_code = 429

                response = jsonify(response_data)
                response.status_code = status_code

                # Add rate limit headers
                if result['remaining'] is not None:
                    response.headers['X-RateLimit-Remaining'] = str(result['remaining'])
                if result['reset_at']:
                    response.headers['X-RateLimit-Reset'] = result['reset_at']

                return response

            # Execute endpoint
            response = f(*args, **kwargs)

            # Add rate limit headers to response
            if hasattr(response, 'headers'):
                if result['remaining'] is not None:
                    response.headers['X-RateLimit-Remaining'] = str(result['remaining'])
                if result['reset_at']:
                    response.headers['X-RateLimit-Reset'] = result['reset_at']

            return response

        return decorated_function
    return decorator
