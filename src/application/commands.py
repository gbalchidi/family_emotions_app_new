"""Application commands."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional
from uuid import UUID

from domain.value_objects import Gender


@dataclass(frozen=True)
class Command:
    """Base command."""

    pass


@dataclass(frozen=True)
class RegisterUserCommand(Command):
    """Register new user command."""

    telegram_id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str] = None
    language_code: Optional[str] = "ru"


@dataclass(frozen=True)
class AddChildCommand(Command):
    """Add child to user command."""

    user_id: UUID
    name: str
    birth_date: date
    gender: Gender
    notes: Optional[str] = None


@dataclass(frozen=True)
class CompleteOnboardingCommand(Command):
    """Complete user onboarding command."""

    user_id: UUID


@dataclass(frozen=True)
class AnalyzeSituationCommand(Command):
    """Analyze situation command."""

    user_id: UUID
    child_id: UUID
    description: str
    context: Optional[str] = None


@dataclass(frozen=True)
class GetUserCommand(Command):
    """Get user by telegram ID command."""

    telegram_id: int


@dataclass(frozen=True)
class GetSituationCommand(Command):
    """Get situation by ID command."""

    situation_id: UUID