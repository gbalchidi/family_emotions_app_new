"""Situation repository interface."""
from __future__ import annotations

from abc import abstractmethod
from typing import Optional
from uuid import UUID

from domain.aggregates.situation import Situation
from domain.repositories.base import Repository


class SituationRepository(Repository[Situation]):
    """Situation repository interface."""

    @abstractmethod
    async def get_user_situations(
        self,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0,
    ) -> list[Situation]:
        """Get user's situations."""
        ...

    @abstractmethod
    async def get_child_situations(
        self,
        child_id: UUID,
        limit: int = 10,
        offset: int = 0,
    ) -> list[Situation]:
        """Get child's situations."""
        ...

    @abstractmethod
    async def count_user_situations(self, user_id: UUID) -> int:
        """Count user's situations."""
        ...