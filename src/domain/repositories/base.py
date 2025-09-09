"""Base repository interfaces."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, Optional, TypeVar
from uuid import UUID

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    """Base repository interface."""

    @abstractmethod
    async def save(self, entity: T) -> None:
        """Save entity."""
        ...

    @abstractmethod
    async def get(self, entity_id: UUID) -> Optional[T]:
        """Get entity by ID."""
        ...

    @abstractmethod
    async def delete(self, entity_id: UUID) -> None:
        """Delete entity by ID."""
        ...