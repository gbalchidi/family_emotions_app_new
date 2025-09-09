"""Domain events for Analysis bounded context."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class AnalysisRequested:
    """Event raised when analysis is requested."""
    
    analysis_id: UUID
    user_id: UUID
    child_id: UUID
    situation: str
    timestamp: datetime


@dataclass(frozen=True)
class AnalysisCompleted:
    """Event raised when analysis is completed."""
    
    analysis_id: UUID
    user_id: UUID
    timestamp: datetime
    confidence_score: float