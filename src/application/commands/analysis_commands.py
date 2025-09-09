"""Analysis-related commands."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RequestAnalysisCommand:
    """Command to request situation analysis."""
    
    user_id: UUID
    child_id: UUID
    situation_description: str
    child_age: int
    child_gender: str