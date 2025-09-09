"""User-related commands."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RegisterUserCommand:
    """Command to register a new user."""
    
    telegram_id: int
    telegram_username: str
    parent_name: str
    child_name: str
    child_age: int
    child_gender: str = "not_specified"


@dataclass(frozen=True)
class AddChildCommand:
    """Command to add a child to user's family."""
    
    user_id: UUID
    child_name: str
    child_age: int
    child_gender: str = "not_specified"