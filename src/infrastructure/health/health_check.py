"""Health check utilities."""
from __future__ import annotations

import asyncio
from typing import Dict, Any

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.infrastructure.database.session import db_manager


class HealthChecker:
    """Health check service."""
    
    async def check_database(self) -> Dict[str, Any]:
        """Check database health."""
        try:
            async with db_manager.session() as session:
                result = await session.execute(text("SELECT 1"))
                return {
                    "status": "healthy",
                    "service": "database",
                    "details": {"connected": True}
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "database",
                "error": str(e)
            }
    
    async def check_redis(self) -> Dict[str, Any]:
        """Check Redis health."""
        try:
            redis = Redis.from_url(str(settings.redis_url))
            await redis.ping()
            await redis.close()
            return {
                "status": "healthy",
                "service": "redis",
                "details": {"connected": True}
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "service": "redis",
                "error": str(e)
            }
    
    async def check_all(self) -> Dict[str, Any]:
        """Run all health checks."""
        checks = await asyncio.gather(
            self.check_database(),
            self.check_redis(),
            return_exceptions=True
        )
        
        all_healthy = all(
            check.get("status") == "healthy" 
            for check in checks 
            if isinstance(check, dict)
        )
        
        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "checks": checks
        }