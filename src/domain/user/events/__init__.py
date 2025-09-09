"""Domain events for User bounded context."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class UserRegistered:
    """Event raised when a new user registers."""
    
    user_id: UUID
    telegram_id: int
    name: str
    timestamp: datetime


@dataclass(frozen=True)
class ChildAdded:
    """Event raised when a child is added to user's family."""
    
    user_id: UUID
    child_id: UUID
    child_name: str
    child_age: int
    child_gender: str
    timestamp: datetime