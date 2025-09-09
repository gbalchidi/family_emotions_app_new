"""Database session management."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import settings


class DatabaseSessionManager:
    """Database session manager."""

    def __init__(self, database_url: str) -> None:
        """Initialize database session manager."""
        self.engine: AsyncEngine = create_async_engine(
            database_url,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_pre_ping=True,
            echo=settings.database_echo,
        )
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def close(self) -> None:
        """Close database connections."""
        await self.engine.dispose()

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session."""
        async with self.async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def create_all(self) -> None:
        """Create all tables."""
        from infrastructure.database.models import Base

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_all(self) -> None:
        """Drop all tables."""
        from infrastructure.database.models import Base

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


# Global database session manager
db_manager = DatabaseSessionManager(str(settings.database_url))


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for dependency injection."""
    async with db_manager.session() as session:
        yield session