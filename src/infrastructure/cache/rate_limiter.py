"""Rate limiter implementation using Redis."""

from datetime import datetime, timedelta
from uuid import UUID

from redis.asyncio import Redis

from src.infrastructure.config.settings import settings


class RedisRateLimiter:
    """Redis-based rate limiter."""
    
    def __init__(self) -> None:
        self._redis = Redis.from_url(settings.redis_url, decode_responses=True)
        self._daily_limit = settings.max_requests_per_user_per_day
        self._hourly_limit = settings.max_requests_per_user_per_hour
    
    async def check_limit(self, user_id: UUID) -> bool:
        """Check if user has reached rate limit."""
        user_id_str = str(user_id)
        now = datetime.utcnow()
        
        # Check daily limit
        daily_key = f"rate_limit:daily:{user_id_str}:{now.date()}"
        daily_count = await self._redis.get(daily_key)
        if daily_count and int(daily_count) >= self._daily_limit:
            return False
        
        # Check hourly limit
        hourly_key = f"rate_limit:hourly:{user_id_str}:{now.strftime('%Y%m%d%H')}"
        hourly_count = await self._redis.get(hourly_key)
        if hourly_count and int(hourly_count) >= self._hourly_limit:
            return False
        
        return True
    
    async def increment_usage(self, user_id: UUID) -> None:
        """Increment usage counter."""
        user_id_str = str(user_id)
        now = datetime.utcnow()
        
        # Increment daily counter
        daily_key = f"rate_limit:daily:{user_id_str}:{now.date()}"
        await self._redis.incr(daily_key)
        await self._redis.expire(daily_key, timedelta(days=1))
        
        # Increment hourly counter
        hourly_key = f"rate_limit:hourly:{user_id_str}:{now.strftime('%Y%m%d%H')}"
        await self._redis.incr(hourly_key)
        await self._redis.expire(hourly_key, timedelta(hours=1))
    
    async def get_remaining_requests(self, user_id: UUID) -> dict:
        """Get remaining requests for user."""
        user_id_str = str(user_id)
        now = datetime.utcnow()
        
        # Get daily usage
        daily_key = f"rate_limit:daily:{user_id_str}:{now.date()}"
        daily_count = await self._redis.get(daily_key)
        daily_used = int(daily_count) if daily_count else 0
        
        # Get hourly usage
        hourly_key = f"rate_limit:hourly:{user_id_str}:{now.strftime('%Y%m%d%H')}"
        hourly_count = await self._redis.get(hourly_key)
        hourly_used = int(hourly_count) if hourly_count else 0
        
        return {
            "daily_remaining": max(0, self._daily_limit - daily_used),
            "hourly_remaining": max(0, self._hourly_limit - hourly_used),
            "daily_limit": self._daily_limit,
            "hourly_limit": self._hourly_limit
        }
    
    async def close(self) -> None:
        """Close Redis connection."""
        await self._redis.close()