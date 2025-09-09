"""Value objects tests."""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from domain.value_objects import AnalysisResult, ChildAge, EmotionalTone, Gender


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

    def test_invalid_age(self) -> None:
        """Test invalid age values."""
        # Negative years
        with pytest.raises(ValueError):
            ChildAge(years=-1)

        # Too many years
        with pytest.raises(ValueError):
            ChildAge(years=19)

        # Invalid months
        with pytest.raises(ValueError):
            ChildAge(years=5, months=12)

        with pytest.raises(ValueError):
            ChildAge(years=5, months=-1)

    def test_age_groups(self) -> None:
        """Test age group classification."""
        assert ChildAge(years=1).age_group == "toddler"
        assert ChildAge(years=2, months=11).age_group == "toddler"
        assert ChildAge(years=3).age_group == "preschooler"
        assert ChildAge(years=5).age_group == "preschooler"
        assert ChildAge(years=6).age_group == "school_age"
        assert ChildAge(years=11).age_group == "school_age"
        assert ChildAge(years=12).age_group == "teenager"
        assert ChildAge(years=17).age_group == "teenager"


class TestAnalysisResult:
    """AnalysisResult value object tests."""

    def test_valid_analysis_result(self) -> None:
        """Test valid analysis result creation."""
        result = AnalysisResult(
            hidden_meaning="Test meaning",
            immediate_actions=["Action 1", "Action 2"],
            long_term_recommendations=["Recommendation 1"],
            what_not_to_do=["Don't do this"],
            emotional_tone=EmotionalTone.POSITIVE,
            confidence_score=0.9,
            analyzed_at=datetime.now(timezone.utc),
        )

        assert result.hidden_meaning == "Test meaning"
        assert len(result.immediate_actions) == 2
        assert result.emotional_tone == EmotionalTone.POSITIVE
        assert result.confidence_score == 0.9

    def test_invalid_confidence_score(self) -> None:
        """Test invalid confidence score."""
        with pytest.raises(ValueError):
            AnalysisResult(
                hidden_meaning="Test",
                immediate_actions=["Action"],
                long_term_recommendations=["Rec"],
                what_not_to_do=["Don't"],
                emotional_tone=EmotionalTone.NEUTRAL,
                confidence_score=1.5,  # Invalid: > 1
                analyzed_at=datetime.now(timezone.utc),
            )

        with pytest.raises(ValueError):
            AnalysisResult(
                hidden_meaning="Test",
                immediate_actions=["Action"],
                long_term_recommendations=["Rec"],
                what_not_to_do=["Don't"],
                emotional_tone=EmotionalTone.NEUTRAL,
                confidence_score=-0.1,  # Invalid: < 0
                analyzed_at=datetime.now(timezone.utc),
            )