"""
Phase 3 Unit Tests - Redis Cache Service
Tests Redis caching functionality
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.infrastructure.cache.redis_cache import (
    RedisCache,
    CacheKeyStrategy,
    cached,
    invalidate_cache
)


class TestCacheKeyStrategy:
    """Test cache key generation strategies"""

    def test_player_key(self):
        """Test player cache key generation"""
        key = CacheKeyStrategy.player_key(123)
        assert key == "epl_predictor:player:123"

    def test_player_ratings_key(self):
        """Test player ratings cache key"""
        key = CacheKeyStrategy.player_ratings_key(456)
        assert key == "epl_predictor:player_ratings:456"

    def test_team_key(self):
        """Test team cache key"""
        key = CacheKeyStrategy.team_key(10)
        assert key == "epl_predictor:team:10"

    def test_team_lineup_key(self):
        """Test team lineup cache key"""
        key = CacheKeyStrategy.team_lineup_key(10)
        assert key == "epl_predictor:team_lineup:10"

    def test_match_key(self):
        """Test match cache key"""
        key = CacheKeyStrategy.match_key(100)
        assert key == "epl_predictor:match:100"

    def test_standings_key(self):
        """Test standings cache key"""
        key = CacheKeyStrategy.standings_key("2024")
        assert key == "epl_predictor:standings:2024"

    def test_custom_key(self):
        """Test custom cache key generation"""
        key = CacheKeyStrategy.custom_key("custom", "part1", "part2")
        assert key == "epl_predictor:custom:part1:part2"


class TestRedisCache:
    """Test Redis cache service"""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        return Mock()

    @pytest.fixture
    def cache(self, mock_redis):
        """Create cache instance with mock Redis"""
        with patch('backend.infrastructure.cache.redis_cache.get_settings') as mock_settings:
            settings = Mock()
            settings.cache.enabled = True
            settings.cache.default_ttl = 3600
            mock_settings.return_value = settings

            cache = RedisCache(redis_client=mock_redis)
            cache._settings.cache.enabled = True
            return cache

    def test_cache_enabled_property(self, cache):
        """Test cache enabled property"""
        assert cache.enabled is True

    def test_get_json_value(self, cache, mock_redis):
        """Test getting JSON value from cache"""
        import json

        test_data = {"name": "Test Player", "rating": 4.5}
        mock_redis.get.return_value = json.dumps(test_data).encode('utf-8')

        result = cache.get("test_key", deserializer='json')

        assert result == test_data
        mock_redis.get.assert_called_once_with("test_key")

    def test_get_nonexistent_key(self, cache, mock_redis):
        """Test getting non-existent key returns None"""
        mock_redis.get.return_value = None

        result = cache.get("nonexistent_key")

        assert result is None

    def test_set_json_value(self, cache, mock_redis):
        """Test setting JSON value in cache"""
        import json

        test_data = {"name": "Test Player"}

        result = cache.set("test_key", test_data, ttl=1800, serializer='json')

        assert result is True
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "test_key"
        assert call_args[0][1] == 1800
        assert json.loads(call_args[0][2]) == test_data

    def test_set_with_default_ttl(self, cache, mock_redis):
        """Test setting value with default TTL"""
        cache.set("test_key", "value")

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 3600  # default TTL

    def test_delete_key(self, cache, mock_redis):
        """Test deleting cache key"""
        result = cache.delete("test_key")

        assert result is True
        mock_redis.delete.assert_called_once_with("test_key")

    def test_delete_pattern(self, cache, mock_redis):
        """Test deleting keys by pattern"""
        mock_redis.keys.return_value = ["key1", "key2", "key3"]
        mock_redis.delete.return_value = 3

        result = cache.delete_pattern("test:*")

        assert result == 3
        mock_redis.keys.assert_called_once_with("test:*")
        mock_redis.delete.assert_called_once_with("key1", "key2", "key3")

    def test_exists(self, cache, mock_redis):
        """Test checking if key exists"""
        mock_redis.exists.return_value = 1

        result = cache.exists("test_key")

        assert result is True
        mock_redis.exists.assert_called_once_with("test_key")

    def test_expire(self, cache, mock_redis):
        """Test setting expiration time"""
        mock_redis.expire.return_value = 1

        result = cache.expire("test_key", 3600)

        assert result is True
        mock_redis.expire.assert_called_once_with("test_key", 3600)

    def test_ttl(self, cache, mock_redis):
        """Test getting remaining TTL"""
        mock_redis.ttl.return_value = 1800

        result = cache.ttl("test_key")

        assert result == 1800
        mock_redis.ttl.assert_called_once_with("test_key")

    def test_get_many(self, cache, mock_redis):
        """Test getting multiple values"""
        import json

        keys = ["key1", "key2", "key3"]
        values = [
            json.dumps({"id": 1}).encode('utf-8'),
            json.dumps({"id": 2}).encode('utf-8'),
            None
        ]
        mock_redis.mget.return_value = values

        result = cache.get_many(keys, deserializer='json')

        assert len(result) == 2
        assert result["key1"]["id"] == 1
        assert result["key2"]["id"] == 2
        assert "key3" not in result

    def test_set_many(self, cache, mock_redis):
        """Test setting multiple values"""
        mapping = {
            "key1": {"id": 1},
            "key2": {"id": 2}
        }

        mock_pipeline = MagicMock()
        mock_redis.pipeline.return_value = mock_pipeline

        result = cache.set_many(mapping, ttl=1800, serializer='json')

        assert result is True
        mock_redis.pipeline.assert_called_once()
        mock_pipeline.execute.assert_called_once()

    def test_flush_all(self, cache, mock_redis):
        """Test flushing all keys"""
        result = cache.flush_all()

        assert result is True
        mock_redis.flushdb.assert_called_once()

    def test_cache_disabled(self):
        """Test operations when cache is disabled"""
        with patch('backend.infrastructure.cache.redis_cache.get_settings') as mock_settings:
            settings = Mock()
            settings.cache.enabled = False
            mock_settings.return_value = settings

            mock_redis = Mock()
            cache = RedisCache(redis_client=mock_redis)
            cache._settings.cache.enabled = False

            # All operations should return None/False when disabled
            assert cache.get("key") is None
            assert cache.set("key", "value") is False
            assert cache.delete("key") is False
            assert cache.exists("key") is False


class TestCachedDecorator:
    """Test @cached decorator"""

    @pytest.fixture
    def mock_cache(self):
        """Mock cache for decorator tests"""
        with patch('backend.infrastructure.cache.redis_cache.RedisCache') as MockCache:
            cache_instance = Mock()
            cache_instance.enabled = True
            MockCache.return_value = cache_instance
            yield cache_instance

    def test_cached_decorator_cache_hit(self, mock_cache):
        """Test decorator returns cached value on cache hit"""
        mock_cache.get.return_value = "cached_result"

        @cached(key_func=lambda x: f"test:{x}")
        def expensive_function(arg):
            return f"computed_{arg}"

        result = expensive_function("test")

        assert result == "cached_result"
        mock_cache.get.assert_called_once()

    def test_cached_decorator_cache_miss(self, mock_cache):
        """Test decorator computes and caches on cache miss"""
        mock_cache.get.return_value = None

        @cached(key_func=lambda x: f"test:{x}")
        def expensive_function(arg):
            return f"computed_{arg}"

        result = expensive_function("test")

        assert result == "computed_test"
        mock_cache.set.assert_called_once()

    def test_cached_decorator_disabled(self):
        """Test decorator bypasses cache when disabled"""
        with patch('backend.infrastructure.cache.redis_cache.RedisCache') as MockCache:
            cache_instance = Mock()
            cache_instance.enabled = False
            MockCache.return_value = cache_instance

            call_count = 0

            @cached(key_func=lambda x: f"test:{x}")
            def expensive_function(arg):
                nonlocal call_count
                call_count += 1
                return f"computed_{arg}"

            result1 = expensive_function("test")
            result2 = expensive_function("test")

            # Should call function twice (no caching)
            assert call_count == 2


class TestInvalidateCacheDecorator:
    """Test @invalidate_cache decorator"""

    @pytest.fixture
    def mock_cache(self):
        """Mock cache for decorator tests"""
        with patch('backend.infrastructure.cache.redis_cache.RedisCache') as MockCache:
            cache_instance = Mock()
            MockCache.return_value = cache_instance
            yield cache_instance

    def test_invalidate_single_key(self, mock_cache):
        """Test invalidating single cache key"""
        @invalidate_cache('test_key')
        def update_function():
            return "updated"

        result = update_function()

        assert result == "updated"
        mock_cache.delete.assert_called_once_with('test_key')

    def test_invalidate_multiple_keys(self, mock_cache):
        """Test invalidating multiple cache keys"""
        @invalidate_cache('key1', 'key2', 'key3')
        def update_function():
            return "updated"

        result = update_function()

        assert result == "updated"
        assert mock_cache.delete.call_count == 3

    def test_invalidate_pattern(self, mock_cache):
        """Test invalidating keys by pattern"""
        @invalidate_cache('player:*')
        def update_function():
            return "updated"

        result = update_function()

        assert result == "updated"
        mock_cache.delete_pattern.assert_called_once_with('player:*')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
