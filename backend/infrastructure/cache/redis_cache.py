"""
Redis Cache Service

Provides Redis-based caching with TTL management and cache key strategies.
"""
import json
import pickle
from typing import Optional, Any, Callable, List
from functools import wraps
import redis
from redis import Redis

from config.settings import get_settings


class CacheKeyStrategy:
    """
    Cache key generation strategies

    Provides consistent key generation for different entity types.
    """

    PREFIX = "epl_predictor"

    @classmethod
    def player_key(cls, player_id: int) -> str:
        """Generate cache key for player"""
        return f"{cls.PREFIX}:player:{player_id}"

    @classmethod
    def player_ratings_key(cls, player_id: int) -> str:
        """Generate cache key for player ratings"""
        return f"{cls.PREFIX}:player_ratings:{player_id}"

    @classmethod
    def team_key(cls, team_id: int) -> str:
        """Generate cache key for team"""
        return f"{cls.PREFIX}:team:{team_id}"

    @classmethod
    def team_lineup_key(cls, team_id: int) -> str:
        """Generate cache key for team lineup"""
        return f"{cls.PREFIX}:team_lineup:{team_id}"

    @classmethod
    def team_tactics_key(cls, team_id: int) -> str:
        """Generate cache key for team tactics"""
        return f"{cls.PREFIX}:team_tactics:{team_id}"

    @classmethod
    def match_key(cls, match_id: int) -> str:
        """Generate cache key for match"""
        return f"{cls.PREFIX}:match:{match_id}"

    @classmethod
    def match_prediction_key(cls, match_id: int) -> str:
        """Generate cache key for match prediction"""
        return f"{cls.PREFIX}:match_prediction:{match_id}"

    @classmethod
    def standings_key(cls, season: str = "current") -> str:
        """Generate cache key for league standings"""
        return f"{cls.PREFIX}:standings:{season}"

    @classmethod
    def custom_key(cls, *parts: str) -> str:
        """Generate custom cache key from parts"""
        return f"{cls.PREFIX}:{':'.join(parts)}"


class RedisCache:
    """
    Redis cache service with TTL management

    Provides high-level caching operations with automatic serialization.
    """

    def __init__(self, redis_client: Optional[Redis] = None):
        """
        Initialize Redis cache

        Args:
            redis_client: Optional Redis client. If not provided, creates from settings.
        """
        if redis_client:
            self._redis = redis_client
        else:
            settings = get_settings()
            self._redis = redis.from_url(
                settings.redis.url,
                decode_responses=False  # We'll handle encoding/decoding
            )

        self._settings = get_settings()

    @property
    def enabled(self) -> bool:
        """Check if caching is enabled"""
        return self._settings.cache.enabled

    def get(self, key: str, deserializer: str = 'json') -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key
            deserializer: Deserialization method ('json' or 'pickle')

        Returns:
            Cached value or None if not found
        """
        if not self.enabled:
            return None

        try:
            value = self._redis.get(key)
            if value is None:
                return None

            if deserializer == 'json':
                return json.loads(value)
            elif deserializer == 'pickle':
                return pickle.loads(value)
            else:
                return value.decode('utf-8')

        except Exception as e:
            print(f"Cache get error for key {key}: {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        serializer: str = 'json'
    ) -> bool:
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds. If None, uses default TTL.
            serializer: Serialization method ('json' or 'pickle')

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            if serializer == 'json':
                serialized = json.dumps(value)
            elif serializer == 'pickle':
                serialized = pickle.dumps(value)
            else:
                serialized = str(value)

            if ttl is None:
                ttl = self._settings.cache.default_ttl

            self._redis.setex(key, ttl, serialized)
            return True

        except Exception as e:
            print(f"Cache set error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete key from cache

        Args:
            key: Cache key

        Returns:
            True if deleted, False otherwise
        """
        if not self.enabled:
            return False

        try:
            self._redis.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error for key {key}: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern

        Args:
            pattern: Key pattern (e.g., "player:*")

        Returns:
            Number of keys deleted
        """
        if not self.enabled:
            return 0

        try:
            keys = self._redis.keys(pattern)
            if keys:
                return self._redis.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache delete pattern error for {pattern}: {e}")
            return 0

    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache

        Args:
            key: Cache key

        Returns:
            True if exists, False otherwise
        """
        if not self.enabled:
            return False

        try:
            return bool(self._redis.exists(key))
        except Exception as e:
            print(f"Cache exists error for key {key}: {e}")
            return False

    def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration time for key

        Args:
            key: Cache key
            ttl: Time to live in seconds

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            return bool(self._redis.expire(key, ttl))
        except Exception as e:
            print(f"Cache expire error for key {key}: {e}")
            return False

    def ttl(self, key: str) -> int:
        """
        Get remaining TTL for key

        Args:
            key: Cache key

        Returns:
            Remaining TTL in seconds, -1 if no expiration, -2 if key doesn't exist
        """
        if not self.enabled:
            return -2

        try:
            return self._redis.ttl(key)
        except Exception as e:
            print(f"Cache TTL error for key {key}: {e}")
            return -2

    def flush_all(self) -> bool:
        """
        Flush all keys from cache

        Use with caution!

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            self._redis.flushdb()
            return True
        except Exception as e:
            print(f"Cache flush error: {e}")
            return False

    def get_many(self, keys: List[str], deserializer: str = 'json') -> dict:
        """
        Get multiple values from cache

        Args:
            keys: List of cache keys
            deserializer: Deserialization method

        Returns:
            Dictionary mapping keys to values
        """
        if not self.enabled or not keys:
            return {}

        try:
            values = self._redis.mget(keys)
            result = {}

            for key, value in zip(keys, values):
                if value is not None:
                    if deserializer == 'json':
                        result[key] = json.loads(value)
                    elif deserializer == 'pickle':
                        result[key] = pickle.loads(value)
                    else:
                        result[key] = value.decode('utf-8')

            return result

        except Exception as e:
            print(f"Cache get_many error: {e}")
            return {}

    def set_many(
        self,
        mapping: dict,
        ttl: Optional[int] = None,
        serializer: str = 'json'
    ) -> bool:
        """
        Set multiple values in cache

        Args:
            mapping: Dictionary mapping keys to values
            ttl: Time to live in seconds
            serializer: Serialization method

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not mapping:
            return False

        try:
            pipe = self._redis.pipeline()

            for key, value in mapping.items():
                if serializer == 'json':
                    serialized = json.dumps(value)
                elif serializer == 'pickle':
                    serialized = pickle.dumps(value)
                else:
                    serialized = str(value)

                if ttl is None:
                    ttl = self._settings.cache.default_ttl

                pipe.setex(key, ttl, serialized)

            pipe.execute()
            return True

        except Exception as e:
            print(f"Cache set_many error: {e}")
            return False


def cached(
    key_func: Callable,
    ttl: Optional[int] = None,
    serializer: str = 'pickle'
):
    """
    Decorator to cache function results

    Args:
        key_func: Function to generate cache key from function arguments
        ttl: Time to live in seconds
        serializer: Serialization method ('json' or 'pickle')

    Example:
        >>> @cached(
        ...     key_func=lambda player_id: CacheKeyStrategy.player_key(player_id),
        ...     ttl=3600
        ... )
        >>> def get_player(player_id: int):
        ...     return db.query(Player).get(player_id)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = RedisCache()

            if not cache.enabled:
                return func(*args, **kwargs)

            # Generate cache key
            cache_key = key_func(*args, **kwargs)

            # Try to get from cache
            cached_value = cache.get(cache_key, deserializer=serializer)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = func(*args, **kwargs)

            # Store in cache
            cache.set(cache_key, result, ttl=ttl, serializer=serializer)

            return result

        return wrapper
    return decorator


def invalidate_cache(*keys: str):
    """
    Decorator to invalidate cache keys after function execution

    Args:
        *keys: Cache keys or patterns to invalidate

    Example:
        >>> @invalidate_cache('player:*', 'team:1')
        >>> def update_player(player_id: int, data: dict):
        ...     # Update player in database
        ...     pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # Invalidate cache after successful execution
            cache = RedisCache()
            for key in keys:
                if '*' in key:
                    cache.delete_pattern(key)
                else:
                    cache.delete(key)

            return result

        return wrapper
    return decorator
