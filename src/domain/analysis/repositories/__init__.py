"""Repository interfaces for Analysis bounded context."""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.analysis.aggregates import Analysis


class AnalysisRepository(ABC):
    """Analysis repository interface (port)."""
    
    @abstractmethod
    async def save(self, analysis: Analysis) -> None:
        """Save analysis aggregate."""
        pass
    
    @abstractmethod
    async def get_by_id(self, analysis_id: UUID) -> Optional[Analysis]:
        """Get analysis by ID."""
        pass
    
    @abstractmethod
    async def get_user_analyses(
        self,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0
    ) -> List[Analysis]:
        """Get user's analyses with pagination."""
        pass
    
    @abstractmethod
    async def count_user_analyses_today(self, user_id: UUID) -> int:
        """Count user's analyses created today."""
        pass