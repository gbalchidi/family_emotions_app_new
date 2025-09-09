"""Enhanced value objects tests."""
from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import uuid4

import pytest

from domain.value_objects import (
    AnalysisResult,
    Child,
    ChildAge,
    EmotionalTone,
    Gender,
    TelegramUser,
)


class TestChildAge:
    """ChildAge value object tests."""

    def test_valid_age(self) -> None:
        """Test valid age creation."""
        age = ChildAge(years=5, months=6)
        assert age.years == 5
        assert age.months == 6
        assert age.total_months == 66
        assert str(age) == "5 years 6 months"

    def test_age_without_months(self) -> None:
        """Test age without months."""
        age = ChildAge(years=10)
        assert age.years == 10
        assert age.months == 0
        assert age.total_months == 120
        assert str(age) == "10 years"

    def test_age_only_months(self) -> None:
        """Test age with zero years."""
        age = ChildAge(years=0, months=8)
        assert age.years == 0
        assert age.months == 8
        assert age.total_months == 8
        assert str(age) == "0 years 8 months"

    def test_invalid_age(self) -> None:
        """Test invalid age values."""
        # Negative years
        with pytest.raises(ValueError, match="Child age must be between 0 and 18 years"):
            ChildAge(years=-1)

        # Too many years
        with pytest.raises(ValueError, match="Child age must be between 0 and 18 years"):
            ChildAge(years=19)

        # Invalid months
        with pytest.raises(ValueError, match="Months must be between 0 and 11"):
            ChildAge(years=5, months=12)

        with pytest.raises(ValueError, match="Months must be between 0 and 11"):
            ChildAge(years=5, months=-1)

    def test_age_groups(self) -> None:
        """Test age group classification."""
        assert ChildAge(years=0, months=6).age_group == "toddler"
        assert ChildAge(years=1).age_group == "toddler"
        assert ChildAge(years=2, months=11).age_group == "toddler"
        assert ChildAge(years=3).age_group == "preschooler"
        assert ChildAge(years=5).age_group == "preschooler"
        assert ChildAge(years=6).age_group == "school_age"
        assert ChildAge(years=11).age_group == "school_age"
        assert ChildAge(years=12).age_group == "teenager"
        assert ChildAge(years=17).age_group == "teenager"
        assert ChildAge(years=18).age_group == "teenager"

    @pytest.mark.parametrize(
        "years,months,expected_total",
        [
            (0, 0, 0),
            (1, 0, 12),
            (2, 6, 30),
            (5, 11, 71),
            (18, 0, 216),
        ],
    )
    def test_total_months_calculation(self, years: int, months: int, expected_total: int) -> None:
        """Test total months calculation with various inputs."""
        age = ChildAge(years=years, months=months)
        assert age.total_months == expected_total

    def test_age_immutability(self) -> None:
        """Test that ChildAge is immutable."""
        age = ChildAge(years=5, months=6)
        with pytest.raises(AttributeError):
            age.years = 6  # type: ignore
        with pytest.raises(AttributeError):
            age.months = 7  # type: ignore


class TestTelegramUser:
    """TelegramUser value object tests."""

    def test_full_telegram_user(self) -> None:
        """Test telegram user with all fields."""
        user = TelegramUser(
            telegram_id=123456789,
            username="testuser",
            first_name="John",
            last_name="Doe",
            language_code="en",
        )
        
        assert user.telegram_id == 123456789
        assert user.username == "testuser"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.language_code == "en"
        assert user.full_name == "John Doe"

    def test_telegram_user_without_last_name(self) -> None:
        """Test telegram user without last name."""
        user = TelegramUser(
            telegram_id=123456789,
            username="testuser",
            first_name="John",
            last_name=None,
        )
        
        assert user.full_name == "John"
        assert user.language_code == "ru"  # Default

    def test_telegram_user_without_username(self) -> None:
        """Test telegram user without username."""
        user = TelegramUser(
            telegram_id=123456789,
            username=None,
            first_name="John",
            last_name="Doe",
        )
        
        assert user.username is None
        assert user.full_name == "John Doe"

    def test_telegram_user_immutability(self) -> None:
        """Test that TelegramUser is immutable."""
        user = TelegramUser(
            telegram_id=123456789,
            username="testuser",
            first_name="John",
        )
        
        with pytest.raises(AttributeError):
            user.telegram_id = 987654321  # type: ignore
        with pytest.raises(AttributeError):
            user.first_name = "Jane"  # type: ignore


class TestChild:
    """Child value object tests."""

    def test_child_creation(self) -> None:
        """Test child creation with all fields."""
        child_id = uuid4()
        birth_date = date(2018, 5, 15)
        
        child = Child(
            id=child_id,
            name="Alice",
            birth_date=birth_date,
            gender=Gender.FEMALE,
            notes="Test child",
        )
        
        assert child.id == child_id
        assert child.name == "Alice"
        assert child.birth_date == birth_date
        assert child.gender == Gender.FEMALE
        assert child.notes == "Test child"

    def test_child_without_notes(self) -> None:
        """Test child creation without notes."""
        child = Child(
            id=uuid4(),
            name="Bob",
            birth_date=date(2020, 1, 1),
            gender=Gender.MALE,
        )
        
        assert child.notes is None

    def test_child_age_calculation(self) -> None:
        """Test child age calculation."""
        # Create child born exactly 5 years and 6 months ago
        today = date.today()
        birth_year = today.year - 5
        birth_month = today.month - 6
        
        if birth_month <= 0:
            birth_year -= 1
            birth_month += 12
            
        birth_date = date(birth_year, birth_month, today.day)
        
        child = Child(
            id=uuid4(),
            name="TestChild",
            birth_date=birth_date,
            gender=Gender.OTHER,
        )
        
        age = child.age
        assert age.years == 5
        assert age.months == 6

    def test_child_immutability(self) -> None:
        """Test that Child is immutable."""
        child = Child(
            id=uuid4(),
            name="Alice",
            birth_date=date(2018, 5, 15),
            gender=Gender.FEMALE,
        )
        
        with pytest.raises(AttributeError):
            child.name = "Bob"  # type: ignore
        with pytest.raises(AttributeError):
            child.gender = Gender.MALE  # type: ignore


class TestAnalysisResult:
    """AnalysisResult value object tests."""

    def test_valid_analysis_result(self) -> None:
        """Test valid analysis result creation."""
        analyzed_at = datetime.now(timezone.utc)
        result = AnalysisResult(
            hidden_meaning="Test meaning",
            immediate_actions=["Action 1", "Action 2"],
            long_term_recommendations=["Recommendation 1"],
            what_not_to_do=["Don't do this"],
            emotional_tone=EmotionalTone.POSITIVE,
            confidence_score=0.9,
            analyzed_at=analyzed_at,
        )

        assert result.hidden_meaning == "Test meaning"
        assert len(result.immediate_actions) == 2
        assert result.emotional_tone == EmotionalTone.POSITIVE
        assert result.confidence_score == 0.9
        assert result.analyzed_at == analyzed_at

    def test_empty_lists_allowed(self) -> None:
        """Test that empty lists are allowed in analysis result."""
        result = AnalysisResult(
            hidden_meaning="Test meaning",
            immediate_actions=[],
            long_term_recommendations=[],
            what_not_to_do=[],
            emotional_tone=EmotionalTone.NEUTRAL,
            confidence_score=0.5,
            analyzed_at=datetime.now(timezone.utc),
        )
        
        assert len(result.immediate_actions) == 0
        assert len(result.long_term_recommendations) == 0
        assert len(result.what_not_to_do) == 0

    @pytest.mark.parametrize(
        "confidence_score,should_raise",
        [
            (0.0, False),
            (0.5, False),
            (1.0, False),
            (-0.1, True),
            (1.1, True),
            (1.5, True),
        ],
    )
    def test_confidence_score_validation(self, confidence_score: float, should_raise: bool) -> None:
        """Test confidence score validation."""
        if should_raise:
            with pytest.raises(ValueError, match="Confidence score must be between 0 and 1"):
                AnalysisResult(
                    hidden_meaning="Test",
                    immediate_actions=["Action"],
                    long_term_recommendations=["Rec"],
                    what_not_to_do=["Don't"],
                    emotional_tone=EmotionalTone.NEUTRAL,
                    confidence_score=confidence_score,
                    analyzed_at=datetime.now(timezone.utc),
                )
        else:
            # Should not raise
            result = AnalysisResult(
                hidden_meaning="Test",
                immediate_actions=["Action"],
                long_term_recommendations=["Rec"],
                what_not_to_do=["Don't"],
                emotional_tone=EmotionalTone.NEUTRAL,
                confidence_score=confidence_score,
                analyzed_at=datetime.now(timezone.utc),
            )
            assert result.confidence_score == confidence_score

    def test_analysis_result_immutability(self) -> None:
        """Test that AnalysisResult is immutable."""
        result = AnalysisResult(
            hidden_meaning="Test meaning",
            immediate_actions=["Action 1"],
            long_term_recommendations=["Rec 1"],
            what_not_to_do=["Don't 1"],
            emotional_tone=EmotionalTone.POSITIVE,
            confidence_score=0.9,
            analyzed_at=datetime.now(timezone.utc),
        )
        
        with pytest.raises(AttributeError):
            result.confidence_score = 0.5  # type: ignore
        with pytest.raises(AttributeError):
            result.emotional_tone = EmotionalTone.NEUTRAL  # type: ignore


class TestEnums:
    """Test enum value objects."""

    def test_gender_enum(self) -> None:
        """Test Gender enum values."""
        assert Gender.MALE.value == "male"
        assert Gender.FEMALE.value == "female"
        assert Gender.OTHER.value == "other"
        
        # Test all enum members
        expected_values = {"male", "female", "other"}
        actual_values = {gender.value for gender in Gender}
        assert actual_values == expected_values

    def test_emotional_tone_enum(self) -> None:
        """Test EmotionalTone enum values."""
        assert EmotionalTone.POSITIVE.value == "positive"
        assert EmotionalTone.NEUTRAL.value == "neutral"
        assert EmotionalTone.CONCERNING.value == "concerning"
        assert EmotionalTone.URGENT.value == "urgent"
        
        # Test all enum members
        expected_values = {"positive", "neutral", "concerning", "urgent"}
        actual_values = {tone.value for tone in EmotionalTone}
        assert actual_values == expected_values

    def test_enum_string_representation(self) -> None:
        """Test enum string representations."""
        assert str(Gender.MALE) == "Gender.MALE"
        assert str(EmotionalTone.POSITIVE) == "EmotionalTone.POSITIVE"
        
        # Test representation
        assert repr(Gender.FEMALE) == "<Gender.FEMALE: 'female'>"
        assert repr(EmotionalTone.URGENT) == "<EmotionalTone.URGENT: 'urgent'>"