"""User aggregate tests."""
from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest

from domain.aggregates.user import User
from domain.events import ChildAdded, OnboardingCompleted, UserRegistered
from domain.exceptions import ChildLimitExceededException, DomainException
from domain.value_objects import Gender


class TestUserAggregate:
    """User aggregate test cases."""

    def test_create_user(self) -> None:
        """Test user creation."""
        user = User.create(
            telegram_id=123456,
            username="testuser",
            first_name="John",
            last_name="Doe",
            language_code="en",
        )

        assert user.telegram_user.telegram_id == 123456
        assert user.telegram_user.username == "testuser"
        assert user.telegram_user.first_name == "John"
        assert user.telegram_user.full_name == "John Doe"
        assert not user.onboarding_completed
        assert user.is_active
        assert len(user.children) == 0

        # Check events
        events = user.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], UserRegistered)

    def test_add_child(self) -> None:
        """Test adding child to user."""
        user = User.create(
            telegram_id=123456,
            username="testuser",
            first_name="John",
        )
        user.collect_events()  # Clear creation events

        child = user.add_child(
            name="Alice",
            birth_date=date(2018, 5, 15),
            gender=Gender.FEMALE,
            notes="Test notes",
        )

        assert child.name == "Alice"
        assert child.gender == Gender.FEMALE
        assert len(user.children) == 1
        assert user.children[0] == child

        # Check events
        events = user.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], ChildAdded)

    def test_cannot_add_too_many_children(self) -> None:
        """Test that user cannot add more than max children."""
        user = User.create(
            telegram_id=123456,
            username="testuser",
            first_name="John",
        )

        # Add max children
        for i in range(User.MAX_CHILDREN):
            user.add_child(
                name=f"Child{i}",
                birth_date=date(2018, 1, 1),
                gender=Gender.MALE,
            )

        # Try to add one more
        with pytest.raises(ChildLimitExceededException):
            user.add_child(
                name="ExtraChild",
                birth_date=date(2018, 1, 1),
                gender=Gender.MALE,
            )

    def test_complete_onboarding(self) -> None:
        """Test completing onboarding."""
        user = User.create(
            telegram_id=123456,
            username="testuser",
            first_name="John",
        )

        # Cannot complete without children
        with pytest.raises(DomainException):
            user.complete_onboarding()

        # Add child and complete
        user.add_child(
            name="Alice",
            birth_date=date(2018, 5, 15),
            gender=Gender.FEMALE,
        )
        user.collect_events()  # Clear previous events

        user.complete_onboarding()
        assert user.onboarding_completed

        # Check events
        events = user.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], OnboardingCompleted)

        # Cannot complete twice
        with pytest.raises(DomainException):
            user.complete_onboarding()

    def test_get_child(self) -> None:
        """Test getting child by ID."""
        user = User.create(
            telegram_id=123456,
            username="testuser",
            first_name="John",
        )

        child = user.add_child(
            name="Alice",
            birth_date=date(2018, 5, 15),
            gender=Gender.FEMALE,
        )

        found_child = user.get_child(child.id)
        assert found_child == child

        # Non-existent child
        assert user.get_child(uuid4()) is None

    def test_deactivate_and_activate_user(self) -> None:
        """Test user deactivation and activation."""
        user = User.create(
            telegram_id=123456,
            username="testuser",
            first_name="John",
        )

        assert user.is_active

        user.deactivate()
        assert not user.is_active

        # Cannot add child to inactive user
        with pytest.raises(DomainException):
            user.add_child(
                name="Alice",
                birth_date=date(2018, 5, 15),
                gender=Gender.FEMALE,
            )

        user.activate()
        assert user.is_active