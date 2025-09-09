"""Situation aggregate tests."""
from __future__ import annotations

from uuid import uuid4

import pytest

from domain.aggregates.situation import Situation
from domain.events import SituationAnalyzed
from domain.exceptions import InvalidSituationException
from domain.value_objects import EmotionalTone


class TestSituationAggregate:
    """Situation aggregate test cases."""

    def test_create_situation(self) -> None:
        """Test situation creation."""
        user_id = uuid4()
        child_id = uuid4()

        situation = Situation.create(
            user_id=user_id,
            child_id=child_id,
            description="Ребенок не хочет делать уроки и плачет",
            context="Это происходит каждый день",
        )

        assert situation.user_id == user_id
        assert situation.child_id == child_id
        assert situation.description == "Ребенок не хочет делать уроки и плачет"
        assert situation.context == "Это происходит каждый день"
        assert not situation.is_analyzed
        assert situation.analysis_result is None

    def test_create_situation_validation(self) -> None:
        """Test situation creation validation."""
        user_id = uuid4()
        child_id = uuid4()

        # Too short description
        with pytest.raises(InvalidSituationException):
            Situation.create(
                user_id=user_id,
                child_id=child_id,
                description="Short",
            )

        # Too long description
        with pytest.raises(InvalidSituationException):
            Situation.create(
                user_id=user_id,
                child_id=child_id,
                description="x" * 2001,
            )

    def test_apply_analysis(self) -> None:
        """Test applying analysis to situation."""
        situation = Situation.create(
            user_id=uuid4(),
            child_id=uuid4(),
            description="Ребенок не хочет делать уроки",
        )

        situation.apply_analysis(
            hidden_meaning="Ребенок устал и нуждается в отдыхе",
            immediate_actions=["Дать отдохнуть", "Поговорить о чувствах"],
            long_term_recommendations=["Пересмотреть режим дня"],
            what_not_to_do=["Не кричать", "Не наказывать"],
            emotional_tone=EmotionalTone.CONCERNING,
            confidence_score=0.85,
        )

        assert situation.is_analyzed
        assert situation.analysis_result is not None
        assert situation.analysis_result.hidden_meaning == "Ребенок устал и нуждается в отдыхе"
        assert len(situation.analysis_result.immediate_actions) == 2
        assert situation.analysis_result.emotional_tone == EmotionalTone.CONCERNING
        assert situation.analysis_result.confidence_score == 0.85

        # Check events
        events = situation.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], SituationAnalyzed)
        assert events[0].emotional_tone == EmotionalTone.CONCERNING

    def test_cannot_analyze_twice(self) -> None:
        """Test that situation cannot be analyzed twice."""
        situation = Situation.create(
            user_id=uuid4(),
            child_id=uuid4(),
            description="Ребенок не хочет делать уроки",
        )

        situation.apply_analysis(
            hidden_meaning="Test",
            immediate_actions=["Action"],
            long_term_recommendations=["Recommendation"],
            what_not_to_do=["Don't"],
            emotional_tone=EmotionalTone.NEUTRAL,
        )

        # Try to analyze again
        with pytest.raises(InvalidSituationException):
            situation.apply_analysis(
                hidden_meaning="Another analysis",
                immediate_actions=["Another action"],
                long_term_recommendations=["Another recommendation"],
                what_not_to_do=["Another don't"],
                emotional_tone=EmotionalTone.POSITIVE,
            )