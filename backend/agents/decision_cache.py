# -*- coding: utf-8 -*-
"""
Decision Cache
Caches recent LLM decisions to avoid repeated API calls

Design:
- 10-second TTL (situations change quickly)
- Hash-based cache key (position, ball location, score, time)
- 50% expected hit rate
- Cuts LLM costs in half

Example:
- First call: "Pass to A?" → LLM call ($0.004)
- 5 seconds later, same situation: "Pass to A?" → Cache hit ($0)
"""

import time
import hashlib
import json
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from collections import OrderedDict

from .actions import Action


@dataclass
class CachedDecision:
    """
    Cached decision with expiration

    Attributes:
        decision: The cached action/decision
        created_at: Timestamp when cached
        expires_at: Timestamp when expires
        hits: Number of cache hits
        metadata: Additional data
    """
    decision: Any
    created_at: float
    expires_at: float
    hits: int = 0
    metadata: Dict = field(default_factory=dict)

    def is_expired(self, current_time: Optional[float] = None) -> bool:
        """Check if cache entry has expired"""
        if current_time is None:
            current_time = time.time()
        return current_time >= self.expires_at

    def record_hit(self):
        """Record a cache hit"""
        self.hits += 1


class DecisionCache:
    """
    Cache for agent decisions to avoid repeat LLM calls

    Cache key: hash(position, ball location, score, time bucket)
    TTL: 10 seconds (configurable)
    Max size: 1000 entries (LRU eviction)
    """

    def __init__(
        self,
        ttl: float = 10.0,
        max_size: int = 1000,
        time_bucket_size: float = 5.0
    ):
        """
        Initialize decision cache

        Args:
            ttl: Time-to-live in seconds (default 10s)
            max_size: Maximum cache entries (default 1000)
            time_bucket_size: Time quantization in seconds (default 5s)
                             Situations within same bucket are considered similar
        """
        self.ttl = ttl
        self.max_size = max_size
        self.time_bucket_size = time_bucket_size

        # Cache storage (ordered for LRU)
        self.cache: OrderedDict[str, CachedDecision] = OrderedDict()

        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0,
            'total_requests': 0
        }

    def get(
        self,
        situation: Dict,
        current_time: Optional[float] = None
    ) -> Optional[Any]:
        """
        Get cached decision for situation

        Args:
            situation: Current situation dictionary
            current_time: Current timestamp (default: time.time())

        Returns:
            Cached decision if found and valid, None otherwise
        """
        if current_time is None:
            current_time = time.time()

        self.stats['total_requests'] += 1

        # Generate cache key
        key = self._hash_situation(situation, current_time)

        # Check if in cache
        if key in self.cache:
            cached = self.cache[key]

            # Check expiration
            if cached.is_expired(current_time):
                # Expired, remove
                del self.cache[key]
                self.stats['expirations'] += 1
                self.stats['misses'] += 1
                return None

            # Valid cache hit
            cached.record_hit()
            self.stats['hits'] += 1

            # Move to end (LRU)
            self.cache.move_to_end(key)

            return cached.decision

        # Cache miss
        self.stats['misses'] += 1
        return None

    def put(
        self,
        situation: Dict,
        decision: Any,
        current_time: Optional[float] = None,
        metadata: Optional[Dict] = None
    ):
        """
        Store decision in cache

        Args:
            situation: Situation dictionary
            decision: Decision to cache
            current_time: Current timestamp (default: time.time())
            metadata: Additional metadata to store
        """
        if current_time is None:
            current_time = time.time()

        # Generate cache key
        key = self._hash_situation(situation, current_time)

        # Create cached entry
        cached_decision = CachedDecision(
            decision=decision,
            created_at=current_time,
            expires_at=current_time + self.ttl,
            metadata=metadata or {}
        )

        # Add to cache
        self.cache[key] = cached_decision

        # Move to end (most recent)
        self.cache.move_to_end(key)

        # Check size limit (LRU eviction)
        if len(self.cache) > self.max_size:
            # Remove oldest entry
            self.cache.popitem(last=False)
            self.stats['evictions'] += 1

    def _hash_situation(
        self,
        situation: Dict,
        current_time: float
    ) -> str:
        """
        Generate cache key from situation

        Quantizes continuous values to create fuzzy matching:
        - Position: rounded to 2m grid
        - Ball position: rounded to 2m grid
        - Time: bucketed to 5s intervals
        - Score: exact match

        Args:
            situation: Situation dictionary
            current_time: Current timestamp

        Returns:
            Cache key (hex hash)
        """
        # Extract key features
        player_pos = situation.get('player_position', [0, 0])
        ball_pos = situation.get('ball_position', [0, 0, 0])
        score = situation.get('score', {'home': 0, 'away': 0})
        decision_type = situation.get('decision_type', 'unknown')

        # Quantize position (2m grid)
        player_x = round(player_pos[0] / 2.0) * 2.0
        player_y = round(player_pos[1] / 2.0) * 2.0

        ball_x = round(ball_pos[0] / 2.0) * 2.0
        ball_y = round(ball_pos[1] / 2.0) * 2.0

        # Quantize time (5s buckets)
        time_bucket = int(current_time / self.time_bucket_size)

        # Build cache key components
        key_components = {
            'px': player_x,
            'py': player_y,
            'bx': ball_x,
            'by': ball_y,
            'score_home': score.get('home', 0),
            'score_away': score.get('away', 0),
            'time_bucket': time_bucket,
            'decision_type': decision_type
        }

        # Add passing options count (if applicable)
        if 'passing_options' in situation:
            key_components['num_options'] = len(situation['passing_options'])

        # Hash components
        key_str = json.dumps(key_components, sort_keys=True)
        key_hash = hashlib.md5(key_str.encode()).hexdigest()

        return key_hash

    def clear_expired(self, current_time: Optional[float] = None):
        """
        Remove all expired entries

        Args:
            current_time: Current timestamp (default: time.time())
        """
        if current_time is None:
            current_time = time.time()

        expired_keys = [
            key for key, cached in self.cache.items()
            if cached.is_expired(current_time)
        ]

        for key in expired_keys:
            del self.cache[key]
            self.stats['expirations'] += 1

    def clear_all(self):
        """Clear entire cache"""
        self.cache.clear()
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0,
            'total_requests': 0
        }

    def get_statistics(self) -> Dict:
        """
        Get cache statistics

        Returns:
            Dictionary with cache performance metrics
        """
        total_requests = self.stats['total_requests']
        hits = self.stats['hits']
        misses = self.stats['misses']

        hit_rate = hits / total_requests if total_requests > 0 else 0.0
        miss_rate = misses / total_requests if total_requests > 0 else 0.0

        return {
            'total_requests': total_requests,
            'hits': hits,
            'misses': misses,
            'hit_rate': round(hit_rate, 3),
            'miss_rate': round(miss_rate, 3),
            'evictions': self.stats['evictions'],
            'expirations': self.stats['expirations'],
            'current_size': len(self.cache),
            'max_size': self.max_size,
            'ttl_seconds': self.ttl
        }

    def get_entry_details(self) -> list:
        """
        Get details of all cached entries (for debugging)

        Returns:
            List of cache entry summaries
        """
        current_time = time.time()

        entries = []
        for key, cached in self.cache.items():
            entries.append({
                'key': key[:8] + '...',  # Abbreviated hash
                'created_at': cached.created_at,
                'expires_at': cached.expires_at,
                'time_remaining': max(0, cached.expires_at - current_time),
                'hits': cached.hits,
                'is_expired': cached.is_expired(current_time),
                'metadata': cached.metadata
            })

        return entries


# =============================================================================
# CACHE DECORATORS
# =============================================================================

def with_cache(cache: DecisionCache):
    """
    Decorator to automatically cache function results

    Usage:
        @with_cache(my_cache)
        def expensive_decision(situation):
            # ... complex logic
            return decision
    """
    def decorator(func):
        def wrapper(situation: Dict, *args, **kwargs):
            # Try cache first
            cached_result = cache.get(situation)
            if cached_result is not None:
                return cached_result

            # Call function
            result = func(situation, *args, **kwargs)

            # Store in cache
            cache.put(situation, result)

            return result

        return wrapper
    return decorator


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_situation_dict(
    player_position: tuple,
    ball_position: tuple,
    score: Dict[str, int],
    decision_type: str,
    **kwargs
) -> Dict:
    """
    Create standardized situation dictionary for caching

    Args:
        player_position: (x, y) tuple
        ball_position: (x, y, h) tuple
        score: Score dictionary
        decision_type: Type of decision
        **kwargs: Additional situation data

    Returns:
        Situation dictionary
    """
    situation = {
        'player_position': list(player_position),
        'ball_position': list(ball_position),
        'score': score,
        'decision_type': decision_type
    }

    # Add additional data
    situation.update(kwargs)

    return situation


# =============================================================================
# EXPORT
# =============================================================================

__all__ = [
    'CachedDecision',
    'DecisionCache',
    'with_cache',
    'create_situation_dict'
]
