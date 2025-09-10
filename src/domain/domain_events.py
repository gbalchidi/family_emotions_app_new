"""Domain events."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from domain.value_objects import EmotionalTone, Gender


@dataclass(frozen=True)
class DomainEvent:
    """Base domain event."""

    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    aggregate_id: UUID = field(default=UUID(int=0))

    @property
    def event_name(self) -> str:
        """Get event name."""
        return self.__class__.__name__


@dataclass(frozen=True)
class UserRegistered(DomainEvent):
    """User registered event."""

    telegram_id: int
    username: Optional[str] = None
    first_name: str = ""
    language_code: str = "en"


@dataclass(frozen=True)
class ChildAdded(DomainEvent):
    """Child added to user event."""

    child_id: UUID = field(default_factory=uuid4)
    child_name: str = ""
    birth_date: str = ""
    gender: Gender = Gender.OTHER


@dataclass(frozen=True)
class OnboardingCompleted(DomainEvent):
    """User completed onboarding event."""

    children_count: int = 0


@dataclass(frozen=True)
class SituationAnalyzed(DomainEvent):
    """Situation analyzed event."""

    situation_id: UUID = field(default_factory=uuid4)
    child_id: UUID = field(default_factory=uuid4)
    situation_text: str = ""
    emotional_tone: Optional[EmotionalTone] = None
    confidence_score: float = 0.0


@dataclass(frozen=True)
class RecommendationViewed(DomainEvent):
    """Recommendation viewed by user event."""

    recommendation_id: UUID = field(default_factory=uuid4)
    situation_id: UUID = field(default_factory=uuid4)


@dataclass(frozen=True)
class UserDeactivated(DomainEvent):
    """User deactivated event."""

    reason: Optional[str] = None