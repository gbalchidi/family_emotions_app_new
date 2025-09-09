"""Analysis service tests."""
from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest

from application.commands import AnalyzeSituationCommand, GetSituationCommand
from application.services.analysis_service import AnalysisService, ClaudeAdapter
from domain.aggregates.situation import Situation
from domain.aggregates.user import User
from domain.exceptions import (
    AnalysisFailedException,
    OnboardingNotCompletedException,
    UserNotFoundException,
)
from domain.repositories.situation import SituationRepository
from domain.repositories.user import UserRepository
from domain.value_objects import EmotionalTone, Gender


class MockClaudeAdapter:
    """Mock Claude adapter for testing."""

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.call_count = 0
        self.last_call_args = None

    async def analyze_situation(
        self,
        situation: str,
        child_age: str,
        child_gender: str,
        context: str | None = None,
    ) -> dict:
        """Mock analyze situation."""
        self.call_count += 1
        self.last_call_args = {
            "situation": situation,
            "child_age": child_age,
            "child_gender": child_gender,
            "context": context,
        }

        if self.should_fail:
            raise Exception("Claude API error")

        return {
            "hidden_meaning": "Ребенок устал и нуждается в отдыхе",
            "immediate_actions": [
                "Дать ребенку отдохнуть 15-20 минут",
                "Предложить перекус",
            ],
            "long_term_recommendations": [
                "Пересмотреть режим дня",
                "Добавить физической активности",
            ],
            "what_not_to_do": [
                "Не повышать голос",
                "Не заставлять силой",
            ],
            "emotional_tone": "concerning",
            "confidence_score": 0.85,
        }


class MockUserRepository:
    """Mock user repository for testing."""

    def __init__(self):
        self.users: dict[UUID, User] = {}

    async def get(self, user_id: UUID) -> User | None:
        """Get user by ID."""
        return self.users.get(user_id)

    def add_user(self, user: User) -> None:
        """Add user for testing."""
        self.users[user.id] = user


class MockSituationRepository:
    """Mock situation repository for testing."""

    def __init__(self):
        self.situations: dict[UUID, Situation] = {}

    async def save(self, situation: Situation) -> None:
        """Save situation."""
        self.situations[situation.id] = situation

    async def get(self, situation_id: UUID) -> Situation | None:
        """Get situation by ID."""
        return self.situations.get(situation_id)

    async def get_user_situations(
        self, user_id: UUID, limit: int = 10, offset: int = 0
    ) -> list[Situation]:
        """Get user situations."""
        user_situations = [
            s for s in self.situations.values() if s.user_id == user_id
        ]
        return user_situations[offset : offset + limit]


class TestAnalysisService:
    """Analysis service test cases."""

    def setup_method(self) -> None:
        """Set up test dependencies."""
        self.user_repository = MockUserRepository()
        self.situation_repository = MockSituationRepository()
        self.claude_adapter = MockClaudeAdapter()
        self.analysis_service = AnalysisService(
            self.user_repository,
            self.situation_repository,
            self.claude_adapter,
        )

    async def test_analyze_situation_success(self) -> None:
        """Test successful situation analysis."""
        # Create and add user with child
        user = User.create(
            telegram_id=123456789,
            username="testuser",
            first_name="John",
        )
        child = user.add_child(
            name="Alice",
            birth_date=date(2018, 5, 15),
            gender=Gender.FEMALE,
        )
        user.complete_onboarding()
        self.user_repository.add_user(user)

        # Analyze situation
        command = AnalyzeSituationCommand(
            user_id=user.id,
            child_id=child.id,
            description="Ребенок не хочет делать уроки и капризничает",
            context="Это происходит каждый день после школы",
        )

        result = await self.analysis_service.analyze_situation(command)

        # Check result
        assert result.user_id == user.id
        assert result.child_id == child.id
        assert result.child_name == "Alice"
        assert result.description == command.description
        assert result.context == command.context
        assert result.is_analyzed

        # Check analysis result
        assert result.analysis_result is not None
        assert result.analysis_result.hidden_meaning == "Ребенок устал и нуждается в отдыхе"
        assert len(result.analysis_result.immediate_actions) == 2
        assert len(result.analysis_result.long_term_recommendations) == 2
        assert len(result.analysis_result.what_not_to_do) == 2
        assert result.analysis_result.emotional_tone == EmotionalTone.CONCERNING
        assert result.analysis_result.confidence_score == 0.85

        # Check Claude adapter was called correctly
        assert self.claude_adapter.call_count == 1
        assert self.claude_adapter.last_call_args["situation"] == command.description
        assert self.claude_adapter.last_call_args["context"] == command.context
        assert "5 years" in self.claude_adapter.last_call_args["child_age"]
        assert self.claude_adapter.last_call_args["child_gender"] == "female"

        # Check situation was saved
        saved_situations = list(self.situation_repository.situations.values())
        assert len(saved_situations) == 1
        assert saved_situations[0].is_analyzed

    async def test_analyze_situation_user_not_found(self) -> None:
        """Test analyzing situation when user doesn't exist."""
        command = AnalyzeSituationCommand(
            user_id=uuid4(),
            child_id=uuid4(),
            description="Test situation",
        )

        with pytest.raises(UserNotFoundException):
            await self.analysis_service.analyze_situation(command)

    async def test_analyze_situation_onboarding_not_completed(self) -> None:
        """Test analyzing situation when onboarding is not completed."""
        # Create user without completing onboarding
        user = User.create(
            telegram_id=123456789,
            username="testuser",
            first_name="John",
        )
        child = user.add_child(
            name="Alice",
            birth_date=date(2018, 5, 15),
            gender=Gender.FEMALE,
        )
        # Note: not calling user.complete_onboarding()
        self.user_repository.add_user(user)

        command = AnalyzeSituationCommand(
            user_id=user.id,
            child_id=child.id,
            description="Test situation",
        )

        with pytest.raises(OnboardingNotCompletedException):
            await self.analysis_service.analyze_situation(command)

    async def test_analyze_situation_child_not_found(self) -> None:
        """Test analyzing situation when child doesn't exist."""
        # Create user with completed onboarding
        user = User.create(
            telegram_id=123456789,
            username="testuser",
            first_name="John",
        )
        user.add_child(
            name="Alice",
            birth_date=date(2018, 5, 15),
            gender=Gender.FEMALE,
        )
        user.complete_onboarding()
        self.user_repository.add_user(user)

        # Try to analyze with non-existent child
        command = AnalyzeSituationCommand(
            user_id=user.id,
            child_id=uuid4(),  # Non-existent child
            description="Test situation",
        )

        with pytest.raises(UserNotFoundException, match="Child .* not found"):
            await self.analysis_service.analyze_situation(command)

    async def test_analyze_situation_claude_failure(self) -> None:
        """Test analyzing situation when Claude fails."""
        # Set up Claude to fail
        self.claude_adapter = MockClaudeAdapter(should_fail=True)
        self.analysis_service = AnalysisService(
            self.user_repository,
            self.situation_repository,
            self.claude_adapter,
        )

        # Create user with child
        user = User.create(
            telegram_id=123456789,
            username="testuser",
            first_name="John",
        )
        child = user.add_child(
            name="Alice",
            birth_date=date(2018, 5, 15),
            gender=Gender.FEMALE,
        )
        user.complete_onboarding()
        self.user_repository.add_user(user)

        command = AnalyzeSituationCommand(
            user_id=user.id,
            child_id=child.id,
            description="Test situation",
        )

        with pytest.raises(AnalysisFailedException):
            await self.analysis_service.analyze_situation(command)

    async def test_get_situation_success(self) -> None:
        """Test successful situation retrieval."""
        # Create and save user with child
        user = User.create(
            telegram_id=123456789,
            username="testuser",
            first_name="John",
        )
        child = user.add_child(
            name="Alice",
            birth_date=date(2018, 5, 15),
            gender=Gender.FEMALE,
        )
        self.user_repository.add_user(user)

        # Create and save situation
        situation = Situation.create(
            user_id=user.id,
            child_id=child.id,
            description="Test situation description that is long enough",
        )
        situation.apply_analysis(
            hidden_meaning="Test meaning",
            immediate_actions=["Action 1"],
            long_term_recommendations=["Rec 1"],
            what_not_to_do=["Don't 1"],
            emotional_tone=EmotionalTone.NEUTRAL,
            confidence_score=0.8,
        )
        await self.situation_repository.save(situation)

        # Get situation
        command = GetSituationCommand(situation_id=situation.id)
        result = await self.analysis_service.get_situation(command)

        # Check result
        assert result is not None
        assert result.id == situation.id
        assert result.user_id == user.id
        assert result.child_id == child.id
        assert result.child_name == "Alice"
        assert result.description == situation.description
        assert result.is_analyzed

    async def test_get_situation_not_found(self) -> None:
        """Test getting situation that doesn't exist."""
        command = GetSituationCommand(situation_id=uuid4())
        result = await self.analysis_service.get_situation(command)
        assert result is None

    async def test_get_situation_user_not_found(self) -> None:
        """Test getting situation when user doesn't exist."""
        # Create situation with non-existent user
        situation = Situation.create(
            user_id=uuid4(),
            child_id=uuid4(),
            description="Test situation description that is long enough",
        )
        await self.situation_repository.save(situation)

        command = GetSituationCommand(situation_id=situation.id)
        result = await self.analysis_service.get_situation(command)
        assert result is None

    async def test_get_user_situations_success(self) -> None:
        """Test getting user's situations."""
        # Create user with child
        user = User.create(
            telegram_id=123456789,
            username="testuser",
            first_name="John",
        )
        child = user.add_child(
            name="Alice",
            birth_date=date(2018, 5, 15),
            gender=Gender.FEMALE,
        )
        self.user_repository.add_user(user)

        # Create multiple situations
        situation1 = Situation.create(
            user_id=user.id,
            child_id=child.id,
            description="First situation description that is long enough",
        )
        situation2 = Situation.create(
            user_id=user.id,
            child_id=child.id,
            description="Second situation description that is long enough",
        )
        await self.situation_repository.save(situation1)
        await self.situation_repository.save(situation2)

        # Get user situations
        result = await self.analysis_service.get_user_situations(user.id)

        # Check result
        assert len(result) == 2
        assert all(s.user_id == user.id for s in result)
        assert all(s.child_name == "Alice" for s in result)

    async def test_get_user_situations_with_pagination(self) -> None:
        """Test getting user's situations with pagination."""
        # Create user with child
        user = User.create(
            telegram_id=123456789,
            username="testuser",
            first_name="John",
        )
        child = user.add_child(
            name="Alice",
            birth_date=date(2018, 5, 15),
            gender=Gender.FEMALE,
        )
        self.user_repository.add_user(user)

        # Create multiple situations
        for i in range(5):
            situation = Situation.create(
                user_id=user.id,
                child_id=child.id,
                description=f"Situation {i} description that is long enough",
            )
            await self.situation_repository.save(situation)

        # Get first page
        result1 = await self.analysis_service.get_user_situations(
            user.id, limit=3, offset=0
        )
        assert len(result1) == 3

        # Get second page
        result2 = await self.analysis_service.get_user_situations(
            user.id, limit=3, offset=3
        )
        assert len(result2) == 2

    async def test_get_user_situations_user_not_found(self) -> None:
        """Test getting situations for non-existent user."""
        result = await self.analysis_service.get_user_situations(uuid4())
        assert result == []

    async def test_dto_conversion_with_child_name_unknown(self) -> None:
        """Test DTO conversion when child is not found."""
        # Create user
        user = User.create(
            telegram_id=123456789,
            username="testuser",
            first_name="John",
        )
        self.user_repository.add_user(user)

        # Create situation with non-existent child
        situation = Situation.create(
            user_id=user.id,
            child_id=uuid4(),  # Non-existent child
            description="Test situation description that is long enough",
        )
        await self.situation_repository.save(situation)

        # Get situation - should show "Unknown" child name
        command = GetSituationCommand(situation_id=situation.id)
        result = await self.analysis_service.get_situation(command)

        assert result is not None
        assert result.child_name == "Unknown"

    async def test_analyze_situation_without_context(self) -> None:
        """Test analyzing situation without context."""
        # Create user with child
        user = User.create(
            telegram_id=123456789,
            username="testuser",
            first_name="John",
        )
        child = user.add_child(
            name="Alice",
            birth_date=date(2018, 5, 15),
            gender=Gender.FEMALE,
        )
        user.complete_onboarding()
        self.user_repository.add_user(user)

        # Analyze situation without context
        command = AnalyzeSituationCommand(
            user_id=user.id,
            child_id=child.id,
            description="Ребенок не хочет делать уроки",
            context=None,
        )

        result = await self.analysis_service.analyze_situation(command)

        # Check result
        assert result.context is None
        assert result.is_analyzed

        # Check Claude was called with None context
        assert self.claude_adapter.last_call_args["context"] is None

    @pytest.mark.parametrize(
        "emotional_tone_str,expected_tone",
        [
            ("positive", EmotionalTone.POSITIVE),
            ("neutral", EmotionalTone.NEUTRAL),
            ("concerning", EmotionalTone.CONCERNING),
            ("urgent", EmotionalTone.URGENT),
        ],
    )
    async def test_analyze_situation_various_emotional_tones(
        self, emotional_tone_str: str, expected_tone: EmotionalTone
    ) -> None:
        """Test analyzing situation with various emotional tones."""
        # Set up Claude to return specific emotional tone
        self.claude_adapter = MockClaudeAdapter()
        original_analyze = self.claude_adapter.analyze_situation

        async def mock_analyze(*args, **kwargs):
            result = await original_analyze(*args, **kwargs)
            result["emotional_tone"] = emotional_tone_str
            return result

        self.claude_adapter.analyze_situation = mock_analyze

        self.analysis_service = AnalysisService(
            self.user_repository,
            self.situation_repository,
            self.claude_adapter,
        )

        # Create user with child
        user = User.create(
            telegram_id=123456789,
            username="testuser",
            first_name="John",
        )
        child = user.add_child(
            name="Alice",
            birth_date=date(2018, 5, 15),
            gender=Gender.FEMALE,
        )
        user.complete_onboarding()
        self.user_repository.add_user(user)

        command = AnalyzeSituationCommand(
            user_id=user.id,
            child_id=child.id,
            description="Test situation",
        )

        result = await self.analysis_service.analyze_situation(command)

        assert result.analysis_result is not None
        assert result.analysis_result.emotional_tone == expected_tone


class TestAnalysisServiceWithMocks:
    """Test AnalysisService with mock dependencies to verify interactions."""

    def setup_method(self) -> None:
        """Set up test dependencies with mocks."""
        self.mock_user_repository = Mock(spec=UserRepository)
        self.mock_situation_repository = Mock(spec=SituationRepository)
        self.mock_claude_adapter = Mock(spec=ClaudeAdapter)
        
        self.analysis_service = AnalysisService(
            self.mock_user_repository,
            self.mock_situation_repository,
            self.mock_claude_adapter,
        )

    async def test_analyze_situation_repository_interactions(self) -> None:
        """Test that analyze_situation calls repositories correctly."""
        # Create test user with child
        user = User.create(
            telegram_id=123456789,
            username="testuser",
            first_name="John",
        )
        child = user.add_child(
            name="Alice",
            birth_date=date(2018, 5, 15),
            gender=Gender.FEMALE,
        )
        user.complete_onboarding()

        # Setup mocks
        self.mock_user_repository.get = AsyncMock(return_value=user)
        self.mock_situation_repository.save = AsyncMock()
        self.mock_claude_adapter.analyze_situation = AsyncMock(
            return_value={
                "hidden_meaning": "Test meaning",
                "immediate_actions": ["Action"],
                "long_term_recommendations": ["Rec"],
                "what_not_to_do": ["Don't"],
                "emotional_tone": "neutral",
                "confidence_score": 0.8,
            }
        )

        command = AnalyzeSituationCommand(
            user_id=user.id,
            child_id=child.id,
            description="Test situation",
        )

        await self.analysis_service.analyze_situation(command)

        # Verify repository calls
        self.mock_user_repository.get.assert_called_once_with(user.id)
        self.mock_situation_repository.save.assert_called_once()
        
        # Verify Claude was called
        self.mock_claude_adapter.analyze_situation.assert_called_once()

        # Verify situation passed to save is analyzed
        saved_situation = self.mock_situation_repository.save.call_args[0][0]
        assert saved_situation.is_analyzed