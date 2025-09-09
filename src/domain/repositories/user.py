"""User repository interface."""
from __future__ import annotations

from abc import abstractmethod
from typing import Optional
from uuid import UUID

from domain.aggregates.user import User
from domain.repositories.base import Repository


class UserRepository(Repository[User]):
    """User repository interface."""

    @abstractmethod
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        ...

    @abstractmethod
    async def exists_by_telegram_id(self, telegram_id: int) -> bool:
        """Check if user exists by Telegram ID."""
        ...