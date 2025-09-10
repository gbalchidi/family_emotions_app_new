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

    aggregate_id: UUID
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def event_name(self) -> str:
        """Get event name."""
        return self.__class__.__name__


@dataclass(frozen=True)
class UserRegistered(DomainEvent):
    """User registered event."""

    telegram_id: int
    username: Optional[str]
    first_name: str
    language_code: str


@dataclass(frozen=True)
class ChildAdded(DomainEvent):
    """Child added to user event."""

    child_id: UUID
    child_name: str
    birth_date: str
    gender: Gender


@dataclass(frozen=True)
class OnboardingCompleted(DomainEvent):
    """User completed onboarding event."""

    children_count: int


@dataclass(frozen=True)
class SituationAnalyzed(DomainEvent):
    """Situation analyzed event."""

    situation_id: UUID
    child_id: UUID
    situation_text: str
    emotional_tone: EmotionalTone
    confidence_score: float


@dataclass(frozen=True)
class RecommendationViewed(DomainEvent):
    """Recommendation viewed by user event."""

    recommendation_id: UUID
    situation_id: UUID


@dataclass(frozen=True)
class UserDeactivated(DomainEvent):
    """User deactivated event."""

    reason: Optional[str] = None