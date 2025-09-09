"""Situation aggregate."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from domain.events import DomainEvent, SituationAnalyzed
from domain.exceptions import InvalidSituationException
from domain.value_objects import AnalysisResult, EmotionalTone


@dataclass
class Situation:
    """Situation aggregate for analysis."""

    id: UUID
    user_id: UUID
    child_id: UUID
    description: str
    context: Optional[str] = None
    analysis_result: Optional[AnalysisResult] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    analyzed_at: Optional[datetime] = None
    _events: list[DomainEvent] = field(default_factory=list, init=False)

    MIN_DESCRIPTION_LENGTH = 10
    MAX_DESCRIPTION_LENGTH = 2000

    @classmethod
    def create(
        cls,
        user_id: UUID,
        child_id: UUID,
        description: str,
        context: Optional[str] = None,
    ) -> Situation:
        """Create new situation for analysis."""
        if len(description) < cls.MIN_DESCRIPTION_LENGTH:
            raise InvalidSituationException(
                f"Description must be at least {cls.MIN_DESCRIPTION_LENGTH} characters"
            )

        if len(description) > cls.MAX_DESCRIPTION_LENGTH:
            raise InvalidSituationException(
                f"Description must not exceed {cls.MAX_DESCRIPTION_LENGTH} characters"
            )

        return cls(
            id=uuid4(),
            user_id=user_id,
            child_id=child_id,
            description=description.strip(),
            context=context,
        )

    def apply_analysis(
        self,
        hidden_meaning: str,
        immediate_actions: list[str],
        long_term_recommendations: list[str],
        what_not_to_do: list[str],
        emotional_tone: EmotionalTone,
        confidence_score: float = 0.8,
    ) -> None:
        """Apply analysis result to situation."""
        if self.analysis_result:
            raise InvalidSituationException("Situation already analyzed")

        self.analysis_result = AnalysisResult(
            hidden_meaning=hidden_meaning,
            immediate_actions=immediate_actions,
            long_term_recommendations=long_term_recommendations,
            what_not_to_do=what_not_to_do,
            emotional_tone=emotional_tone,
            confidence_score=confidence_score,
            analyzed_at=datetime.now(timezone.utc),
        )

        self.analyzed_at = datetime.now(timezone.utc)

        self._add_event(
            SituationAnalyzed(
                aggregate_id=self.id,
                situation_id=self.id,
                child_id=self.child_id,
                situation_text=self.description,
                emotional_tone=emotional_tone,
                confidence_score=confidence_score,
            )
        )

    @property
    def is_analyzed(self) -> bool:
        """Check if situation has been analyzed."""
        return self.analysis_result is not None

    def _add_event(self, event: DomainEvent) -> None:
        """Add domain event."""
        self._events.append(event)

    def collect_events(self) -> list[DomainEvent]:
        """Collect and clear events."""
        events = self._events.copy()
        self._events.clear()
        return events