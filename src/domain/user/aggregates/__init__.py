"""User aggregate root and related entities."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from src.domain.user.value_objects import UserName, TelegramId
from src.domain.user.events import UserRegistered, ChildAdded


@dataclass
class Child:
    """Child entity."""
    
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    age: int = 0
    gender: str = "not_specified"  # male, female, not_specified
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Child name cannot be empty")
        if not 0 < self.age <= 18:
            raise ValueError("Child age must be between 1 and 18")
        if self.gender not in ["male", "female", "not_specified"]:
            raise ValueError("Invalid gender value")


@dataclass
class User:
    """User aggregate root."""
    
    id: UUID = field(default_factory=uuid4)
    telegram_id: TelegramId = field(default_factory=lambda: TelegramId(0))
    name: UserName = field(default_factory=lambda: UserName(""))
    children: List[Child] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    _events: List = field(default_factory=list, init=False, repr=False)
    
    @classmethod
    def register(
        cls,
        telegram_id: int,
        name: str,
        child_name: str,
        child_age: int,
        child_gender: str = "not_specified"
    ) -> "User":
        """Register a new user with initial child."""
        user = cls(
            telegram_id=TelegramId(telegram_id),
            name=UserName(name),
            children=[Child(name=child_name, age=child_age, gender=child_gender)]
        )
        user._events.append(
            UserRegistered(
                user_id=user.id,
                telegram_id=telegram_id,
                name=name,
                timestamp=user.created_at
            )
        )
        return user
    
    def add_child(self, name: str, age: int, gender: str = "not_specified") -> Child:
        """Add a new child to the user's family."""
        if len(self.children) >= 10:
            raise ValueError("Maximum number of children (10) reached")
        
        child = Child(name=name, age=age, gender=gender)
        self.children.append(child)
        self.updated_at = datetime.utcnow()
        
        self._events.append(
            ChildAdded(
                user_id=self.id,
                child_id=child.id,
                child_name=name,
                child_age=age,
                child_gender=gender,
                timestamp=datetime.utcnow()
            )
        )
        return child
    
    def get_child_by_id(self, child_id: UUID) -> Optional[Child]:
        """Get child by ID."""
        return next((c for c in self.children if c.id == child_id), None)
    
    def get_events(self) -> List:
        """Get and clear domain events."""
        events = self._events.copy()
        self._events.clear()
        return events