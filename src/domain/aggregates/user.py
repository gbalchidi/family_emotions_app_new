"""User aggregate."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from domain.domain_events import ChildAdded, DomainEvent, OnboardingCompleted, UserRegistered
from domain.exceptions import ChildLimitExceededException, DomainException
from domain.value_objects import Child, Gender, TelegramUser


@dataclass
class User:
    """User aggregate root."""

    id: UUID
    telegram_user: TelegramUser
    children: list[Child] = field(default_factory=list)
    onboarding_completed: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    _events: list[DomainEvent] = field(default_factory=list, init=False)

    MAX_CHILDREN = 10

    @classmethod
    def create(
        cls,
        telegram_id: int,
        username: Optional[str],
        first_name: str,
        last_name: Optional[str] = None,
        language_code: Optional[str] = "ru",
    ) -> User:
        """Create new user aggregate."""
        user_id = uuid4()
        telegram_user = TelegramUser(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
        )

        user = cls(
            id=user_id,
            telegram_user=telegram_user,
        )

        user._add_event(
            UserRegistered(
                aggregate_id=user_id,
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                language_code=language_code or "ru",
            )
        )

        return user

    def add_child(
        self,
        name: str,
        birth_date: date,
        gender: Gender,
        notes: Optional[str] = None,
    ) -> Child:
        """Add child to user."""
        if len(self.children) >= self.MAX_CHILDREN:
            raise ChildLimitExceededException(self.MAX_CHILDREN)

        if not self.is_active:
            raise DomainException("Cannot add child to inactive user")

        child_id = uuid4()
        child = Child(
            id=child_id,
            name=name,
            birth_date=birth_date,
            gender=gender,
            notes=notes,
        )

        self.children.append(child)
        self.updated_at = datetime.now(timezone.utc)

        self._add_event(
            ChildAdded(
                aggregate_id=self.id,
                child_id=child_id,
                child_name=name,
                birth_date=birth_date.isoformat(),
                gender=gender,
            )
        )

        return child

    def remove_child(self, child_id: UUID) -> None:
        """Remove child from user."""
        self.children = [c for c in self.children if c.id != child_id]
        self.updated_at = datetime.now(timezone.utc)

    def complete_onboarding(self) -> None:
        """Mark onboarding as completed."""
        if self.onboarding_completed:
            raise DomainException("Onboarding already completed")

        if not self.children:
            raise DomainException("Add at least one child to complete onboarding")

        self.onboarding_completed = True
        self.updated_at = datetime.now(timezone.utc)

        self._add_event(
            OnboardingCompleted(
                aggregate_id=self.id,
                children_count=len(self.children),
            )
        )

    def get_child(self, child_id: UUID) -> Optional[Child]:
        """Get child by ID."""
        return next((c for c in self.children if c.id == child_id), None)

    def deactivate(self) -> None:
        """Deactivate user."""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

    def activate(self) -> None:
        """Activate user."""
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)

    def _add_event(self, event: DomainEvent) -> None:
        """Add domain event."""
        self._events.append(event)

    def collect_events(self) -> list[DomainEvent]:
        """Collect and clear events."""
        events = self._events.copy()
        self._events.clear()
        return events