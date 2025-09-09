"""Domain exceptions."""
from __future__ import annotations

from typing import Optional


class DomainException(Exception):
    """Base domain exception."""

    def __init__(self, message: str, code: Optional[str] = None) -> None:
        """Initialize domain exception."""
        super().__init__(message)
        self.code = code or self.__class__.__name__


class UserNotFoundException(DomainException):
    """User not found exception."""

    def __init__(self, user_id: str) -> None:
        """Initialize exception."""
        super().__init__(f"User {user_id} not found", "USER_NOT_FOUND")


class UserAlreadyExistsException(DomainException):
    """User already exists exception."""

    def __init__(self, telegram_id: int) -> None:
        """Initialize exception."""
        super().__init__(
            f"User with telegram_id {telegram_id} already exists",
            "USER_ALREADY_EXISTS",
        )


class ChildLimitExceededException(DomainException):
    """Too many children added exception."""

    def __init__(self, limit: int = 10) -> None:
        """Initialize exception."""
        super().__init__(
            f"Cannot add more than {limit} children",
            "CHILD_LIMIT_EXCEEDED",
        )


class InvalidSituationException(DomainException):
    """Invalid situation for analysis."""

    def __init__(self, reason: str) -> None:
        """Initialize exception."""
        super().__init__(f"Invalid situation: {reason}", "INVALID_SITUATION")


class AnalysisFailedException(DomainException):
    """Analysis failed exception."""

    def __init__(self, reason: str) -> None:
        """Initialize exception."""
        super().__init__(f"Analysis failed: {reason}", "ANALYSIS_FAILED")


class OnboardingNotCompletedException(DomainException):
    """User hasn't completed onboarding."""

    def __init__(self) -> None:
        """Initialize exception."""
        super().__init__(
            "Please complete onboarding first",
            "ONBOARDING_NOT_COMPLETED",
        )