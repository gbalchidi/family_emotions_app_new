"""Domain events tests."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from domain.events import (
    ChildAdded,
    DomainEvent,
    OnboardingCompleted,
    RecommendationViewed,
    SituationAnalyzed,
    UserDeactivated,
    UserRegistered,
)
from domain.value_objects import EmotionalTone, Gender


class TestDomainEvent:
    """Base domain event tests."""

    def test_domain_event_creation(self) -> None:
        """Test domain event creation with default values."""
        aggregate_id = uuid4()
        event = DomainEvent(aggregate_id=aggregate_id)
        
        assert event.aggregate_id == aggregate_id
        assert isinstance(event.event_id, UUID)
        assert isinstance(event.occurred_at, datetime)
        assert event.occurred_at.tzinfo == timezone.utc
        assert event.event_name == "DomainEvent"

    def test_domain_event_custom_values(self) -> None:
        """Test domain event creation with custom values."""
        event_id = uuid4()
        aggregate_id = uuid4()
        occurred_at = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        event = DomainEvent(
            event_id=event_id,
            occurred_at=occurred_at,
            aggregate_id=aggregate_id,
        )
        
        assert event.event_id == event_id
        assert event.occurred_at == occurred_at
        assert event.aggregate_id == aggregate_id

    def test_domain_event_immutable(self) -> None:
        """Test that domain event is immutable."""
        event = DomainEvent()
        
        with pytest.raises(AttributeError):
            event.event_id = uuid4()  # type: ignore
        with pytest.raises(AttributeError):
            event.occurred_at = datetime.now(timezone.utc)  # type: ignore

    def test_event_name_property(self) -> None:
        """Test event name property returns class name."""
        event = DomainEvent()
        assert event.event_name == "DomainEvent"


class TestUserRegistered:
    """UserRegistered event tests."""

    def test_user_registered_creation(self) -> None:
        """Test UserRegistered event creation."""
        aggregate_id = uuid4()
        event = UserRegistered(
            aggregate_id=aggregate_id,
            telegram_id=123456789,
            username="testuser",
            first_name="John",
            language_code="en",
        )
        
        assert event.aggregate_id == aggregate_id
        assert event.telegram_id == 123456789
        assert event.username == "testuser"
        assert event.first_name == "John"
        assert event.language_code == "en"
        assert event.event_name == "UserRegistered"

    def test_user_registered_without_username(self) -> None:
        """Test UserRegistered event without username."""
        event = UserRegistered(
            aggregate_id=uuid4(),
            telegram_id=123456789,
            username=None,
            first_name="John",
            language_code="ru",
        )
        
        assert event.username is None
        assert event.language_code == "ru"

    def test_user_registered_immutable(self) -> None:
        """Test that UserRegistered event is immutable."""
        event = UserRegistered(
            aggregate_id=uuid4(),
            telegram_id=123456789,
            username="testuser",
            first_name="John",
            language_code="en",
        )
        
        with pytest.raises(AttributeError):
            event.telegram_id = 987654321  # type: ignore
        with pytest.raises(AttributeError):
            event.first_name = "Jane"  # type: ignore


class TestChildAdded:
    """ChildAdded event tests."""

    def test_child_added_creation(self) -> None:
        """Test ChildAdded event creation."""
        aggregate_id = uuid4()
        child_id = uuid4()
        
        event = ChildAdded(
            aggregate_id=aggregate_id,
            child_id=child_id,
            child_name="Alice",
            birth_date="2018-05-15",
            gender=Gender.FEMALE,
        )
        
        assert event.aggregate_id == aggregate_id
        assert event.child_id == child_id
        assert event.child_name == "Alice"
        assert event.birth_date == "2018-05-15"
        assert event.gender == Gender.FEMALE
        assert event.event_name == "ChildAdded"

    def test_child_added_all_genders(self) -> None:
        """Test ChildAdded event with all gender types."""
        for gender in Gender:
            event = ChildAdded(
                aggregate_id=uuid4(),
                child_id=uuid4(),
                child_name="TestChild",
                birth_date="2020-01-01",
                gender=gender,
            )
            assert event.gender == gender

    def test_child_added_immutable(self) -> None:
        """Test that ChildAdded event is immutable."""
        event = ChildAdded(
            aggregate_id=uuid4(),
            child_id=uuid4(),
            child_name="Alice",
            birth_date="2018-05-15",
            gender=Gender.FEMALE,
        )
        
        with pytest.raises(AttributeError):
            event.child_name = "Bob"  # type: ignore
        with pytest.raises(AttributeError):
            event.gender = Gender.MALE  # type: ignore


class TestOnboardingCompleted:
    """OnboardingCompleted event tests."""

    def test_onboarding_completed_creation(self) -> None:
        """Test OnboardingCompleted event creation."""
        aggregate_id = uuid4()
        event = OnboardingCompleted(
            aggregate_id=aggregate_id,
            children_count=2,
        )
        
        assert event.aggregate_id == aggregate_id
        assert event.children_count == 2
        assert event.event_name == "OnboardingCompleted"

    @pytest.mark.parametrize("children_count", [1, 2, 5, 10])
    def test_onboarding_completed_various_counts(self, children_count: int) -> None:
        """Test OnboardingCompleted event with various children counts."""
        event = OnboardingCompleted(
            aggregate_id=uuid4(),
            children_count=children_count,
        )
        assert event.children_count == children_count

    def test_onboarding_completed_immutable(self) -> None:
        """Test that OnboardingCompleted event is immutable."""
        event = OnboardingCompleted(
            aggregate_id=uuid4(),
            children_count=2,
        )
        
        with pytest.raises(AttributeError):
            event.children_count = 3  # type: ignore


class TestSituationAnalyzed:
    """SituationAnalyzed event tests."""

    def test_situation_analyzed_creation(self) -> None:
        """Test SituationAnalyzed event creation."""
        aggregate_id = uuid4()
        situation_id = uuid4()
        child_id = uuid4()
        
        event = SituationAnalyzed(
            aggregate_id=aggregate_id,
            situation_id=situation_id,
            child_id=child_id,
            situation_text="Test situation description",
            emotional_tone=EmotionalTone.CONCERNING,
            confidence_score=0.85,
        )
        
        assert event.aggregate_id == aggregate_id
        assert event.situation_id == situation_id
        assert event.child_id == child_id
        assert event.situation_text == "Test situation description"
        assert event.emotional_tone == EmotionalTone.CONCERNING
        assert event.confidence_score == 0.85
        assert event.event_name == "SituationAnalyzed"

    @pytest.mark.parametrize(
        "emotional_tone",
        [EmotionalTone.POSITIVE, EmotionalTone.NEUTRAL, EmotionalTone.CONCERNING, EmotionalTone.URGENT],
    )
    def test_situation_analyzed_all_emotional_tones(self, emotional_tone: EmotionalTone) -> None:
        """Test SituationAnalyzed event with all emotional tones."""
        event = SituationAnalyzed(
            aggregate_id=uuid4(),
            situation_id=uuid4(),
            child_id=uuid4(),
            situation_text="Test situation",
            emotional_tone=emotional_tone,
            confidence_score=0.8,
        )
        assert event.emotional_tone == emotional_tone

    @pytest.mark.parametrize("confidence_score", [0.0, 0.5, 0.85, 1.0])
    def test_situation_analyzed_various_confidence_scores(self, confidence_score: float) -> None:
        """Test SituationAnalyzed event with various confidence scores."""
        event = SituationAnalyzed(
            aggregate_id=uuid4(),
            situation_id=uuid4(),
            child_id=uuid4(),
            situation_text="Test situation",
            emotional_tone=EmotionalTone.NEUTRAL,
            confidence_score=confidence_score,
        )
        assert event.confidence_score == confidence_score

    def test_situation_analyzed_immutable(self) -> None:
        """Test that SituationAnalyzed event is immutable."""
        event = SituationAnalyzed(
            aggregate_id=uuid4(),
            situation_id=uuid4(),
            child_id=uuid4(),
            situation_text="Test situation",
            emotional_tone=EmotionalTone.CONCERNING,
            confidence_score=0.85,
        )
        
        with pytest.raises(AttributeError):
            event.situation_text = "Modified text"  # type: ignore
        with pytest.raises(AttributeError):
            event.confidence_score = 0.9  # type: ignore


class TestRecommendationViewed:
    """RecommendationViewed event tests."""

    def test_recommendation_viewed_creation(self) -> None:
        """Test RecommendationViewed event creation."""
        aggregate_id = uuid4()
        recommendation_id = uuid4()
        situation_id = uuid4()
        
        event = RecommendationViewed(
            aggregate_id=aggregate_id,
            recommendation_id=recommendation_id,
            situation_id=situation_id,
        )
        
        assert event.aggregate_id == aggregate_id
        assert event.recommendation_id == recommendation_id
        assert event.situation_id == situation_id
        assert event.event_name == "RecommendationViewed"

    def test_recommendation_viewed_immutable(self) -> None:
        """Test that RecommendationViewed event is immutable."""
        event = RecommendationViewed(
            aggregate_id=uuid4(),
            recommendation_id=uuid4(),
            situation_id=uuid4(),
        )
        
        with pytest.raises(AttributeError):
            event.recommendation_id = uuid4()  # type: ignore
        with pytest.raises(AttributeError):
            event.situation_id = uuid4()  # type: ignore


class TestUserDeactivated:
    """UserDeactivated event tests."""

    def test_user_deactivated_creation(self) -> None:
        """Test UserDeactivated event creation."""
        aggregate_id = uuid4()
        event = UserDeactivated(
            aggregate_id=aggregate_id,
            reason="User requested account deletion",
        )
        
        assert event.aggregate_id == aggregate_id
        assert event.reason == "User requested account deletion"
        assert event.event_name == "UserDeactivated"

    def test_user_deactivated_without_reason(self) -> None:
        """Test UserDeactivated event without reason."""
        event = UserDeactivated(
            aggregate_id=uuid4(),
        )
        
        assert event.reason is None

    def test_user_deactivated_immutable(self) -> None:
        """Test that UserDeactivated event is immutable."""
        event = UserDeactivated(
            aggregate_id=uuid4(),
            reason="Test reason",
        )
        
        with pytest.raises(AttributeError):
            event.reason = "Modified reason"  # type: ignore


class TestEventEquality:
    """Test event equality and hashing."""

    def test_events_with_same_data_are_equal(self) -> None:
        """Test that events with same data are equal."""
        aggregate_id = uuid4()
        event_id = uuid4()
        occurred_at = datetime.now(timezone.utc)
        
        event1 = UserRegistered(
            event_id=event_id,
            occurred_at=occurred_at,
            aggregate_id=aggregate_id,
            telegram_id=123456789,
            username="testuser",
            first_name="John",
            language_code="en",
        )
        
        event2 = UserRegistered(
            event_id=event_id,
            occurred_at=occurred_at,
            aggregate_id=aggregate_id,
            telegram_id=123456789,
            username="testuser",
            first_name="John",
            language_code="en",
        )
        
        assert event1 == event2
        assert hash(event1) == hash(event2)

    def test_events_with_different_data_are_not_equal(self) -> None:
        """Test that events with different data are not equal."""
        event1 = UserRegistered(
            aggregate_id=uuid4(),
            telegram_id=123456789,
            username="testuser",
            first_name="John",
            language_code="en",
        )
        
        event2 = UserRegistered(
            aggregate_id=uuid4(),
            telegram_id=987654321,  # Different telegram_id
            username="testuser",
            first_name="John",
            language_code="en",
        )
        
        assert event1 != event2

    def test_different_event_types_are_not_equal(self) -> None:
        """Test that different event types are not equal."""
        aggregate_id = uuid4()
        
        user_event = UserRegistered(
            aggregate_id=aggregate_id,
            telegram_id=123456789,
            username="testuser",
            first_name="John",
            language_code="en",
        )
        
        onboarding_event = OnboardingCompleted(
            aggregate_id=aggregate_id,
            children_count=1,
        )
        
        assert user_event != onboarding_event