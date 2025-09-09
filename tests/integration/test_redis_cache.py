"""Integration tests for Redis cache and rate limiter."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from redis.asyncio import Redis

from infrastructure.cache.rate_limiter import RedisRateLimiter


class MockRedis:
    """Mock Redis client for testing."""

    def __init__(self):
        self.data = {}
        self.expires = {}

    async def get(self, key: str) -> str | None:
        """Get value from mock Redis."""
        if key in self.expires and datetime.utcnow() > self.expires[key]:
            del self.data[key]
            del self.expires[key]
            return None
        return self.data.get(key)

    async def incr(self, key: str) -> int:
        """Increment value in mock Redis."""
        current = int(self.data.get(key, 0))
        new_value = current + 1
        self.data[key] = str(new_value)
        return new_value

    async def expire(self, key: str, ttl: timedelta) -> None:
        """Set expiration for key in mock Redis."""
        self.expires[key] = datetime.utcnow() + ttl

    async def close(self) -> None:
        """Close mock Redis connection."""
        pass

    def clear(self) -> None:
        """Clear all data (for testing)."""
        self.data.clear()
        self.expires.clear()


class TestRedisRateLimiter:
    """Redis rate limiter tests."""

    def setup_method(self) -> None:
        """Set up test dependencies."""
        self.mock_redis = MockRedis()
        self.user_id = uuid4()

    @patch("infrastructure.cache.rate_limiter.settings")
    @patch("infrastructure.cache.rate_limiter.Redis.from_url")
    def test_rate_limiter_initialization(self, mock_redis_from_url, mock_settings) -> None:
        """Test rate limiter initialization."""
        mock_settings.redis_url = "redis://localhost:6379"
        mock_settings.max_requests_per_user_per_day = 100
        mock_settings.max_requests_per_user_per_hour = 10
        mock_redis_from_url.return_value = self.mock_redis

        rate_limiter = RedisRateLimiter()

        assert rate_limiter._daily_limit == 100
        assert rate_limiter._hourly_limit == 10
        mock_redis_from_url.assert_called_once_with("redis://localhost:6379", decode_responses=True)

    @patch("infrastructure.cache.rate_limiter.settings")
    @patch("infrastructure.cache.rate_limiter.Redis.from_url")
    async def test_check_limit_new_user(self, mock_redis_from_url, mock_settings) -> None:
        """Test checking limit for new user (should pass)."""
        mock_settings.redis_url = "redis://localhost:6379"
        mock_settings.max_requests_per_user_per_day = 100
        mock_settings.max_requests_per_user_per_hour = 10
        mock_redis_from_url.return_value = self.mock_redis

        rate_limiter = RedisRateLimiter()

        # New user should pass rate limit check
        result = await rate_limiter.check_limit(self.user_id)
        assert result is True

    @patch("infrastructure.cache.rate_limiter.settings")
    @patch("infrastructure.cache.rate_limiter.Redis.from_url")
    async def test_check_limit_within_limits(self, mock_redis_from_url, mock_settings) -> None:
        """Test checking limit for user within limits."""
        mock_settings.redis_url = "redis://localhost:6379"
        mock_settings.max_requests_per_user_per_day = 100
        mock_settings.max_requests_per_user_per_hour = 10
        mock_redis_from_url.return_value = self.mock_redis

        rate_limiter = RedisRateLimiter()

        # Simulate some usage
        user_id_str = str(self.user_id)
        now = datetime.utcnow()
        daily_key = f"rate_limit:daily:{user_id_str}:{now.date()}"
        hourly_key = f"rate_limit:hourly:{user_id_str}:{now.strftime('%Y%m%d%H')}"
        
        self.mock_redis.data[daily_key] = "5"
        self.mock_redis.data[hourly_key] = "3"

        # Should still pass
        result = await rate_limiter.check_limit(self.user_id)
        assert result is True

    @patch("infrastructure.cache.rate_limiter.settings")
    @patch("infrastructure.cache.rate_limiter.Redis.from_url")
    async def test_check_limit_daily_limit_exceeded(self, mock_redis_from_url, mock_settings) -> None:
        """Test checking limit when daily limit is exceeded."""
        mock_settings.redis_url = "redis://localhost:6379"
        mock_settings.max_requests_per_user_per_day = 10
        mock_settings.max_requests_per_user_per_hour = 5
        mock_redis_from_url.return_value = self.mock_redis

        rate_limiter = RedisRateLimiter()

        # Simulate daily limit exceeded
        user_id_str = str(self.user_id)
        now = datetime.utcnow()
        daily_key = f"rate_limit:daily:{user_id_str}:{now.date()}"
        hourly_key = f"rate_limit:hourly:{user_id_str}:{now.strftime('%Y%m%d%H')}"
        
        self.mock_redis.data[daily_key] = "10"  # At limit
        self.mock_redis.data[hourly_key] = "2"

        # Should fail
        result = await rate_limiter.check_limit(self.user_id)
        assert result is False

    @patch("infrastructure.cache.rate_limiter.settings")
    @patch("infrastructure.cache.rate_limiter.Redis.from_url")
    async def test_check_limit_hourly_limit_exceeded(self, mock_redis_from_url, mock_settings) -> None:
        """Test checking limit when hourly limit is exceeded."""
        mock_settings.redis_url = "redis://localhost:6379"
        mock_settings.max_requests_per_user_per_day = 100
        mock_settings.max_requests_per_user_per_hour = 5
        mock_redis_from_url.return_value = self.mock_redis

        rate_limiter = RedisRateLimiter()

        # Simulate hourly limit exceeded
        user_id_str = str(self.user_id)
        now = datetime.utcnow()
        daily_key = f"rate_limit:daily:{user_id_str}:{now.date()}"
        hourly_key = f"rate_limit:hourly:{user_id_str}:{now.strftime('%Y%m%d%H')}"
        
        self.mock_redis.data[daily_key] = "20"
        self.mock_redis.data[hourly_key] = "5"  # At limit

        # Should fail
        result = await rate_limiter.check_limit(self.user_id)
        assert result is False

    @patch("infrastructure.cache.rate_limiter.settings")
    @patch("infrastructure.cache.rate_limiter.Redis.from_url")
    async def test_increment_usage(self, mock_redis_from_url, mock_settings) -> None:
        """Test incrementing usage counters."""
        mock_settings.redis_url = "redis://localhost:6379"
        mock_settings.max_requests_per_user_per_day = 100
        mock_settings.max_requests_per_user_per_hour = 10
        mock_redis_from_url.return_value = self.mock_redis

        rate_limiter = RedisRateLimiter()

        # Increment usage
        await rate_limiter.increment_usage(self.user_id)

        # Check that counters were incremented
        user_id_str = str(self.user_id)
        now = datetime.utcnow()
        daily_key = f"rate_limit:daily:{user_id_str}:{now.date()}"
        hourly_key = f"rate_limit:hourly:{user_id_str}:{now.strftime('%Y%m%d%H')}"

        assert self.mock_redis.data[daily_key] == "1"
        assert self.mock_redis.data[hourly_key] == "1"

        # Check that expiration was set
        assert daily_key in self.mock_redis.expires
        assert hourly_key in self.mock_redis.expires

    @patch("infrastructure.cache.rate_limiter.settings")
    @patch("infrastructure.cache.rate_limiter.Redis.from_url")
    async def test_increment_usage_multiple_times(self, mock_redis_from_url, mock_settings) -> None:
        """Test incrementing usage multiple times."""
        mock_settings.redis_url = "redis://localhost:6379"
        mock_settings.max_requests_per_user_per_day = 100
        mock_settings.max_requests_per_user_per_hour = 10
        mock_redis_from_url.return_value = self.mock_redis

        rate_limiter = RedisRateLimiter()

        # Increment usage multiple times
        for _ in range(5):
            await rate_limiter.increment_usage(self.user_id)

        # Check final counter values
        user_id_str = str(self.user_id)
        now = datetime.utcnow()
        daily_key = f"rate_limit:daily:{user_id_str}:{now.date()}"
        hourly_key = f"rate_limit:hourly:{user_id_str}:{now.strftime('%Y%m%d%H')}"

        assert self.mock_redis.data[daily_key] == "5"
        assert self.mock_redis.data[hourly_key] == "5"

    @patch("infrastructure.cache.rate_limiter.settings")
    @patch("infrastructure.cache.rate_limiter.Redis.from_url")
    async def test_get_remaining_requests_new_user(self, mock_redis_from_url, mock_settings) -> None:
        """Test getting remaining requests for new user."""
        mock_settings.redis_url = "redis://localhost:6379"
        mock_settings.max_requests_per_user_per_day = 100
        mock_settings.max_requests_per_user_per_hour = 10
        mock_redis_from_url.return_value = self.mock_redis

        rate_limiter = RedisRateLimiter()

        result = await rate_limiter.get_remaining_requests(self.user_id)

        assert result["daily_remaining"] == 100
        assert result["hourly_remaining"] == 10
        assert result["daily_limit"] == 100
        assert result["hourly_limit"] == 10

    @patch("infrastructure.cache.rate_limiter.settings")
    @patch("infrastructure.cache.rate_limiter.Redis.from_url")
    async def test_get_remaining_requests_with_usage(self, mock_redis_from_url, mock_settings) -> None:
        """Test getting remaining requests after some usage."""
        mock_settings.redis_url = "redis://localhost:6379"
        mock_settings.max_requests_per_user_per_day = 100
        mock_settings.max_requests_per_user_per_hour = 10
        mock_redis_from_url.return_value = self.mock_redis

        rate_limiter = RedisRateLimiter()

        # Simulate some usage
        user_id_str = str(self.user_id)
        now = datetime.utcnow()
        daily_key = f"rate_limit:daily:{user_id_str}:{now.date()}"
        hourly_key = f"rate_limit:hourly:{user_id_str}:{now.strftime('%Y%m%d%H')}"
        
        self.mock_redis.data[daily_key] = "25"
        self.mock_redis.data[hourly_key] = "7"

        result = await rate_limiter.get_remaining_requests(self.user_id)

        assert result["daily_remaining"] == 75
        assert result["hourly_remaining"] == 3
        assert result["daily_limit"] == 100
        assert result["hourly_limit"] == 10

    @patch("infrastructure.cache.rate_limiter.settings")
    @patch("infrastructure.cache.rate_limiter.Redis.from_url")
    async def test_get_remaining_requests_limit_exceeded(self, mock_redis_from_url, mock_settings) -> None:
        """Test getting remaining requests when limits are exceeded."""
        mock_settings.redis_url = "redis://localhost:6379"
        mock_settings.max_requests_per_user_per_day = 100
        mock_settings.max_requests_per_user_per_hour = 10
        mock_redis_from_url.return_value = self.mock_redis

        rate_limiter = RedisRateLimiter()

        # Simulate limits exceeded
        user_id_str = str(self.user_id)
        now = datetime.utcnow()
        daily_key = f"rate_limit:daily:{user_id_str}:{now.date()}"
        hourly_key = f"rate_limit:hourly:{user_id_str}:{now.strftime('%Y%m%d%H')}"
        
        self.mock_redis.data[daily_key] = "150"  # Over daily limit
        self.mock_redis.data[hourly_key] = "15"  # Over hourly limit

        result = await rate_limiter.get_remaining_requests(self.user_id)

        assert result["daily_remaining"] == 0  # Should not go negative
        assert result["hourly_remaining"] == 0  # Should not go negative
        assert result["daily_limit"] == 100
        assert result["hourly_limit"] == 10

    @patch("infrastructure.cache.rate_limiter.settings")
    @patch("infrastructure.cache.rate_limiter.Redis.from_url")
    async def test_close_connection(self, mock_redis_from_url, mock_settings) -> None:
        """Test closing Redis connection."""
        mock_settings.redis_url = "redis://localhost:6379"
        mock_settings.max_requests_per_user_per_day = 100
        mock_settings.max_requests_per_user_per_hour = 10
        mock_redis_from_url.return_value = self.mock_redis

        rate_limiter = RedisRateLimiter()

        # Should not raise an exception
        await rate_limiter.close()

    @patch("infrastructure.cache.rate_limiter.settings")
    @patch("infrastructure.cache.rate_limiter.Redis.from_url")
    async def test_key_format_consistency(self, mock_redis_from_url, mock_settings) -> None:
        """Test that rate limiter uses consistent key formats."""
        mock_settings.redis_url = "redis://localhost:6379"
        mock_settings.max_requests_per_user_per_day = 100
        mock_settings.max_requests_per_user_per_hour = 10
        mock_redis_from_url.return_value = self.mock_redis

        rate_limiter = RedisRateLimiter()

        # Use a fixed datetime for consistent testing
        fixed_datetime = datetime(2024, 1, 15, 14, 30, 0)
        
        with patch("infrastructure.cache.rate_limiter.datetime") as mock_datetime:
            mock_datetime.utcnow.return_value = fixed_datetime
            mock_datetime.date = datetime.date

            await rate_limiter.increment_usage(self.user_id)
            
            # Check that expected keys were created
            user_id_str = str(self.user_id)
            expected_daily_key = f"rate_limit:daily:{user_id_str}:2024-01-15"
            expected_hourly_key = f"rate_limit:hourly:{user_id_str}:20240115014"

            assert expected_daily_key in self.mock_redis.data
            assert expected_hourly_key in self.mock_redis.data

    @patch("infrastructure.cache.rate_limiter.settings")
    @patch("infrastructure.cache.rate_limiter.Redis.from_url")
    async def test_multiple_users_isolation(self, mock_redis_from_url, mock_settings) -> None:
        """Test that different users have isolated rate limits."""
        mock_settings.redis_url = "redis://localhost:6379"
        mock_settings.max_requests_per_user_per_day = 10
        mock_settings.max_requests_per_user_per_hour = 5
        mock_redis_from_url.return_value = self.mock_redis

        rate_limiter = RedisRateLimiter()

        user1 = uuid4()
        user2 = uuid4()

        # User 1 reaches limit
        for _ in range(10):
            await rate_limiter.increment_usage(user1)

        # User 2 should still be within limits
        assert await rate_limiter.check_limit(user1) is False
        assert await rate_limiter.check_limit(user2) is True

        # User 2 should have full quota available
        remaining = await rate_limiter.get_remaining_requests(user2)
        assert remaining["daily_remaining"] == 10
        assert remaining["hourly_remaining"] == 5


class TestRedisIntegrationWithRealRedis:
    """Integration tests with real Redis (if available)."""

    @pytest.mark.integration
    @pytest.mark.skip(reason="Requires Redis server")
    async def test_with_real_redis(self) -> None:
        """Test rate limiter with real Redis instance."""
        # This test would require a real Redis instance
        # Skip by default, can be enabled for integration testing
        
        rate_limiter = RedisRateLimiter()
        user_id = uuid4()

        try:
            # Test basic functionality
            assert await rate_limiter.check_limit(user_id) is True
            
            await rate_limiter.increment_usage(user_id)
            remaining = await rate_limiter.get_remaining_requests(user_id)
            
            assert remaining["daily_remaining"] < remaining["daily_limit"]
            assert remaining["hourly_remaining"] < remaining["hourly_limit"]
            
        finally:
            await rate_limiter.close()

    @pytest.mark.integration
    async def test_redis_connection_failure_handling(self) -> None:
        """Test handling of Redis connection failures."""
        with patch("infrastructure.cache.rate_limiter.Redis.from_url") as mock_redis_from_url:
            # Mock Redis to raise connection errors
            mock_redis = Mock()
            mock_redis.get = AsyncMock(side_effect=ConnectionError("Redis unavailable"))
            mock_redis.incr = AsyncMock(side_effect=ConnectionError("Redis unavailable"))
            mock_redis_from_url.return_value = mock_redis
            
            with patch("infrastructure.cache.rate_limiter.settings") as mock_settings:
                mock_settings.redis_url = "redis://localhost:6379"
                mock_settings.max_requests_per_user_per_day = 100
                mock_settings.max_requests_per_user_per_hour = 10

                rate_limiter = RedisRateLimiter()

                # Should raise ConnectionError when Redis is unavailable
                with pytest.raises(ConnectionError):
                    await rate_limiter.check_limit(uuid4())

                with pytest.raises(ConnectionError):
                    await rate_limiter.increment_usage(uuid4())