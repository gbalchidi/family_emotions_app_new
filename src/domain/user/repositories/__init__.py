"""Repository interfaces for User bounded context."""

from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from src.domain.user.aggregates import User


class UserRepository(ABC):
    """User repository interface (port)."""
    
    @abstractmethod
    async def save(self, user: User) -> None:
        """Save user aggregate."""
        pass
    
    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        pass
    
    @abstractmethod
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        pass
    
    @abstractmethod
    async def exists_by_telegram_id(self, telegram_id: int) -> bool:
        """Check if user exists by Telegram ID."""
        pass