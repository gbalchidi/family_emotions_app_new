"""Application DTOs."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from domain.value_objects import EmotionalTone, Gender


@dataclass(frozen=True)
class ChildDTO:
    """Child DTO."""

    id: UUID
    name: str
    birth_date: date
    gender: Gender
    age_years: int
    age_months: int
    age_group: str
    notes: Optional[str] = None


@dataclass(frozen=True)
class UserDTO:
    """User DTO."""

    id: UUID
    telegram_id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str]
    full_name: str
    children: list[ChildDTO]
    onboarding_completed: bool
    created_at: datetime
    is_active: bool


@dataclass(frozen=True)
class AnalysisResultDTO:
    """Analysis result DTO."""

    hidden_meaning: str
    immediate_actions: list[str]
    long_term_recommendations: list[str]
    what_not_to_do: list[str]
    emotional_tone: EmotionalTone
    confidence_score: float
    analyzed_at: datetime


@dataclass(frozen=True)
class SituationDTO:
    """Situation DTO."""

    id: UUID
    user_id: UUID
    child_id: UUID
    child_name: str
    description: str
    context: Optional[str]
    analysis_result: Optional[AnalysisResultDTO]
    created_at: datetime
    analyzed_at: Optional[datetime]
    is_analyzed: bool


@dataclass(frozen=True)
class OnboardingStatusDTO:
    """Onboarding status DTO."""

    completed: bool
    current_step: str
    children_added: int
    needs_child: bool