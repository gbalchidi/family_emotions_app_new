"""Domain value objects."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import UUID


class Gender(Enum):
    """Child gender enumeration."""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class EmotionalTone(Enum):
    """Emotional tone of analysis."""

    POSITIVE = "positive"
    NEUTRAL = "neutral"
    CONCERNING = "concerning"
    URGENT = "urgent"


@dataclass(frozen=True)
class ChildAge:
    """Value object representing child's age."""

    years: int
    months: Optional[int] = 0

    def __post_init__(self) -> None:
        """Validate age values."""
        if self.years < 0 or self.years > 18:
            raise ValueError("Child age must be between 0 and 18 years")
        if self.months and (self.months < 0 or self.months > 11):
            raise ValueError("Months must be between 0 and 11")

    @property
    def total_months(self) -> int:
        """Get total age in months."""
        return self.years * 12 + (self.months or 0)

    @property
    def age_group(self) -> str:
        """Get age group classification."""
        if self.years < 3:
            return "toddler"
        elif self.years < 6:
            return "preschooler"
        elif self.years < 12:
            return "school_age"
        else:
            return "teenager"

    def __str__(self) -> str:
        """String representation of age."""
        if self.months:
            return f"{self.years} years {self.months} months"
        return f"{self.years} years"


@dataclass(frozen=True)
class TelegramUser:
    """Value object representing Telegram user data."""

    telegram_id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str]
    language_code: Optional[str] = "ru"

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name


@dataclass(frozen=True)
class AnalysisResult:
    """Value object containing Claude's analysis."""

    hidden_meaning: str
    immediate_actions: list[str]
    long_term_recommendations: list[str]
    what_not_to_do: list[str]
    emotional_tone: EmotionalTone
    confidence_score: float
    analyzed_at: datetime

    def __post_init__(self) -> None:
        """Validate analysis result."""
        if not 0 <= self.confidence_score <= 1:
            raise ValueError("Confidence score must be between 0 and 1")


@dataclass(frozen=True)
class Child:
    """Value object representing a child."""

    id: UUID
    name: str
    birth_date: date
    gender: Gender
    notes: Optional[str] = None

    @property
    def age(self) -> ChildAge:
        """Calculate current age."""
        today = date.today()
        years = today.year - self.birth_date.year
        months = today.month - self.birth_date.month

        if months < 0:
            years -= 1
            months += 12
        elif months == 0 and today.day < self.birth_date.day:
            years -= 1
            months = 11

        return ChildAge(years=years, months=months)