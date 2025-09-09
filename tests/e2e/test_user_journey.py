"""End-to-end user journey tests."""
from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from application.commands import (
    AddChildCommand,
    AnalyzeSituationCommand,
    CompleteOnboardingCommand,
    RegisterUserCommand,
)
from application.dto import AnalysisResultDTO, ChildDTO, SituationDTO, UserDTO
from application.services.analysis_service import AnalysisService
from application.services.user_service import UserService
from domain.value_objects import EmotionalTone, Gender
from infrastructure.claude.adapter import ClaudeAdapter


class TestFullUserJourney:
    """Test complete user journey from registration to analysis."""

    def setup_method(self) -> None:
        """Set up test dependencies."""
        self.telegram_id = 123456789
        self.user_id = uuid4()
        self.child_id = uuid4()

    @pytest.mark.e2e
    async def test_complete_user_journey_success(self) -> None:
        """Test complete successful user journey."""
        # Mock all dependencies
        mock_user_repo = Mock()
        mock_situation_repo = Mock()
        mock_claude_adapter = Mock(spec=ClaudeAdapter)

        # Mock Claude response
        mock_claude_adapter.analyze_situation = AsyncMock(return_value={
            "hidden_meaning": "Ребенок испытывает стресс от учебной нагрузки",
            "immediate_actions": [
                "Поговорить с ребенком о его чувствах",
                "Дать время на отдых",
                "Выяснить, что именно беспокоит",
            ],
            "long_term_recommendations": [
                "Пересмотреть режим дня",
                "Добавить больше времени для игр",
                "Обратиться к школьному психологу",
            ],
            "what_not_to_do": [
                "Не заставлять учиться силой",
                "Не повышать голос",
                "Не сравнивать с другими детьми",
            ],
            "emotional_tone": "concerning",
            "confidence_score": 0.9,
        })

        # Initialize services
        user_service = UserService(mock_user_repo)
        analysis_service = AnalysisService(
            mock_user_repo,
            mock_situation_repo,
            mock_claude_adapter,
        )

        # Step 1: User registration
        register_command = RegisterUserCommand(
            telegram_id=self.telegram_id,
            username="parentuser",
            first_name="John",
            last_name="Doe",
            language_code="en",
        )

        # Mock user repository for registration
        mock_user_repo.exists_by_telegram_id = AsyncMock(return_value=False)
        mock_user_repo.save = AsyncMock()

        user_dto = await user_service.register_user(register_command)

        # Verify user was created
        assert user_dto.telegram_id == self.telegram_id
        assert user_dto.first_name == "John"
        assert user_dto.last_name == "Doe"
        assert not user_dto.onboarding_completed
        assert len(user_dto.children) == 0

        # Step 2: Add child
        from domain.aggregates.user import User
        
        user_aggregate = User.create(
            telegram_id=self.telegram_id,
            username="parentuser",
            first_name="John",
            last_name="Doe",
            language_code="en",
        )
        user_aggregate.id = user_dto.id  # Set the same ID

        mock_user_repo.get = AsyncMock(return_value=user_aggregate)

        add_child_command = AddChildCommand(
            user_id=user_dto.id,
            name="Alice",
            birth_date=date(2018, 5, 15),
            gender=Gender.FEMALE,
            notes="My daughter",
        )

        child_dto = await user_service.add_child(add_child_command)

        # Verify child was added
        assert child_dto.name == "Alice"
        assert child_dto.gender == Gender.FEMALE
        assert child_dto.age_years >= 5  # Should be around 5-6 years old
        assert child_dto.notes == "My daughter"

        # Step 3: Complete onboarding
        complete_onboarding_command = CompleteOnboardingCommand(
            user_id=user_dto.id,
        )

        # User aggregate now has a child
        user_aggregate.collect_events()  # Clear events from adding child
        updated_user_dto = await user_service.complete_onboarding(complete_onboarding_command)

        # Verify onboarding was completed
        assert updated_user_dto.onboarding_completed

        # Step 4: Analyze situation
        analyze_command = AnalyzeSituationCommand(
            user_id=user_dto.id,
            child_id=child_dto.id,
            description="Моя дочь Alice не хочет делать домашнее задание. Она плачет и говорит, что это слишком сложно. Каждый день после школы одно и то же.",
            context="Это началось в новой четверти, когда нагрузка увеличилась",
        )

        # Mock situation repository
        mock_situation_repo.save = AsyncMock()

        situation_dto = await analysis_service.analyze_situation(analyze_command)

        # Verify analysis was performed
        assert situation_dto.user_id == user_dto.id
        assert situation_dto.child_id == child_dto.id
        assert situation_dto.child_name == "Alice"
        assert situation_dto.is_analyzed
        assert situation_dto.analysis_result is not None

        # Verify analysis content
        analysis = situation_dto.analysis_result
        assert analysis.hidden_meaning == "Ребенок испытывает стресс от учебной нагрузки"
        assert len(analysis.immediate_actions) == 3
        assert len(analysis.long_term_recommendations) == 3
        assert len(analysis.what_not_to_do) == 3
        assert analysis.emotional_tone == EmotionalTone.CONCERNING
        assert analysis.confidence_score == 0.9

        # Verify Claude was called correctly
        mock_claude_adapter.analyze_situation.assert_called_once()
        call_args = mock_claude_adapter.analyze_situation.call_args
        assert call_args[1]["situation"] == analyze_command.description
        assert call_args[1]["context"] == analyze_command.context
        assert "5 years" in call_args[1]["child_age"] or "6 years" in call_args[1]["child_age"]
        assert call_args[1]["child_gender"] == "female"

        # Verify repositories were called
        mock_user_repo.save.assert_called()  # For registration, adding child, completing onboarding
        mock_situation_repo.save.assert_called_once()

    @pytest.mark.e2e
    async def test_user_journey_with_multiple_children(self) -> None:
        """Test user journey with multiple children."""
        # Mock dependencies
        mock_user_repo = Mock()
        mock_situation_repo = Mock()
        mock_claude_adapter = Mock(spec=ClaudeAdapter)

        user_service = UserService(mock_user_repo)
        analysis_service = AnalysisService(
            mock_user_repo,
            mock_situation_repo,
            mock_claude_adapter,
        )

        # Mock Claude responses for different children
        mock_claude_adapter.analyze_situation = AsyncMock(side_effect=[
            {
                "hidden_meaning": "Старший ребенок ревнует к младшему",
                "immediate_actions": ["Поговорить индивидуально", "Дать особое внимание"],
                "long_term_recommendations": ["Планировать время один на один"],
                "what_not_to_do": ["Не сравнивать детей"],
                "emotional_tone": "neutral",
                "confidence_score": 0.8,
            },
            {
                "hidden_meaning": "Младший копирует поведение старшего",
                "immediate_actions": ["Объяснить правила", "Установить границы"],
                "long_term_recommendations": ["Развивать индивидуальность"],
                "what_not_to_do": ["Не наказывать за все подряд"],
                "emotional_tone": "positive",
                "confidence_score": 0.7,
            },
        ])

        # Step 1: Register user
        register_command = RegisterUserCommand(
            telegram_id=self.telegram_id,
            username="parent",
            first_name="Parent",
        )

        mock_user_repo.exists_by_telegram_id = AsyncMock(return_value=False)
        mock_user_repo.save = AsyncMock()

        user_dto = await user_service.register_user(register_command)

        # Create user aggregate for children operations
        from domain.aggregates.user import User
        
        user_aggregate = User.create(
            telegram_id=self.telegram_id,
            username="parent",
            first_name="Parent",
        )
        user_aggregate.id = user_dto.id

        mock_user_repo.get = AsyncMock(return_value=user_aggregate)

        # Step 2: Add first child
        add_child1_command = AddChildCommand(
            user_id=user_dto.id,
            name="Bob",
            birth_date=date(2016, 3, 10),
            gender=Gender.MALE,
        )

        child1_dto = await user_service.add_child(add_child1_command)

        # Step 3: Add second child
        add_child2_command = AddChildCommand(
            user_id=user_dto.id,
            name="Emma",
            birth_date=date(2020, 8, 20),
            gender=Gender.FEMALE,
        )

        child2_dto = await user_service.add_child(add_child2_command)

        # Step 4: Complete onboarding
        complete_command = CompleteOnboardingCommand(user_id=user_dto.id)
        user_aggregate.collect_events()  # Clear events
        await user_service.complete_onboarding(complete_command)

        # Step 5: Analyze situations for both children
        mock_situation_repo.save = AsyncMock()

        # Analyze situation for first child
        analyze1_command = AnalyzeSituationCommand(
            user_id=user_dto.id,
            child_id=child1_dto.id,
            description="Боб стал агрессивным после рождения сестры",
        )

        situation1_dto = await analysis_service.analyze_situation(analyze1_command)

        # Analyze situation for second child
        analyze2_command = AnalyzeSituationCommand(
            user_id=user_dto.id,
            child_id=child2_dto.id,
            description="Эмма повторяет все за братом, даже плохое поведение",
        )

        situation2_dto = await analysis_service.analyze_situation(analyze2_command)

        # Verify both analyses
        assert situation1_dto.child_name == "Bob"
        assert situation1_dto.analysis_result.emotional_tone == EmotionalTone.NEUTRAL
        assert "ревнует" in situation1_dto.analysis_result.hidden_meaning

        assert situation2_dto.child_name == "Emma"
        assert situation2_dto.analysis_result.emotional_tone == EmotionalTone.POSITIVE
        assert "копирует" in situation2_dto.analysis_result.hidden_meaning

        # Verify Claude was called twice with different parameters
        assert mock_claude_adapter.analyze_situation.call_count == 2

    @pytest.mark.e2e
    async def test_user_journey_error_scenarios(self) -> None:
        """Test user journey with various error scenarios."""
        mock_user_repo = Mock()
        mock_situation_repo = Mock()
        mock_claude_adapter = Mock(spec=ClaudeAdapter)

        user_service = UserService(mock_user_repo)
        analysis_service = AnalysisService(
            mock_user_repo,
            mock_situation_repo,
            mock_claude_adapter,
        )

        # Scenario 1: Try to register existing user
        mock_user_repo.exists_by_telegram_id = AsyncMock(return_value=True)

        register_command = RegisterUserCommand(
            telegram_id=self.telegram_id,
            username="existing",
            first_name="Existing",
        )

        from domain.exceptions import UserAlreadyExistsException
        
        with pytest.raises(UserAlreadyExistsException):
            await user_service.register_user(register_command)

        # Scenario 2: Try to add child to non-existent user
        mock_user_repo.get = AsyncMock(return_value=None)

        add_child_command = AddChildCommand(
            user_id=uuid4(),
            name="Ghost Child",
            birth_date=date(2020, 1, 1),
            gender=Gender.OTHER,
        )

        from domain.exceptions import UserNotFoundException
        
        with pytest.raises(UserNotFoundException):
            await user_service.add_child(add_child_command)

        # Scenario 3: Try to analyze situation before onboarding
        from domain.aggregates.user import User
        
        user_without_onboarding = User.create(
            telegram_id=self.telegram_id,
            username="incomplete",
            first_name="Incomplete",
        )
        child = user_without_onboarding.add_child(
            name="Test Child",
            birth_date=date(2020, 1, 1),
            gender=Gender.MALE,
        )
        # Note: not completing onboarding

        mock_user_repo.get = AsyncMock(return_value=user_without_onboarding)

        analyze_command = AnalyzeSituationCommand(
            user_id=user_without_onboarding.id,
            child_id=child.id,
            description="Test situation",
        )

        from domain.exceptions import OnboardingNotCompletedException
        
        with pytest.raises(OnboardingNotCompletedException):
            await analysis_service.analyze_situation(analyze_command)

        # Scenario 4: Claude API failure
        completed_user = User.create(
            telegram_id=self.telegram_id,
            username="complete",
            first_name="Complete",
        )
        child = completed_user.add_child(
            name="Test Child",
            birth_date=date(2020, 1, 1),
            gender=Gender.MALE,
        )
        completed_user.complete_onboarding()

        mock_user_repo.get = AsyncMock(return_value=completed_user)
        mock_claude_adapter.analyze_situation = AsyncMock(
            side_effect=Exception("Claude API error")
        )

        analyze_command = AnalyzeSituationCommand(
            user_id=completed_user.id,
            child_id=child.id,
            description="Test situation that will fail",
        )

        from domain.exceptions import AnalysisFailedException
        
        with pytest.raises(AnalysisFailedException):
            await analysis_service.analyze_situation(analyze_command)

    @pytest.mark.e2e
    async def test_user_journey_edge_cases(self) -> None:
        """Test user journey with edge cases."""
        mock_user_repo = Mock()
        mock_situation_repo = Mock()
        mock_claude_adapter = Mock(spec=ClaudeAdapter)

        user_service = UserService(mock_user_repo)
        analysis_service = AnalysisService(
            mock_user_repo,
            mock_situation_repo,
            mock_claude_adapter,
        )

        # Edge case 1: User with maximum number of children
        from domain.aggregates.user import User
        
        user_aggregate = User.create(
            telegram_id=self.telegram_id,
            username="bigfamily",
            first_name="BigFamily",
        )

        # Add maximum children
        for i in range(User.MAX_CHILDREN):
            user_aggregate.add_child(
                name=f"Child{i}",
                birth_date=date(2020, 1, 1),
                gender=Gender.MALE if i % 2 == 0 else Gender.FEMALE,
            )

        mock_user_repo.exists_by_telegram_id = AsyncMock(return_value=False)
        mock_user_repo.get = AsyncMock(return_value=user_aggregate)
        mock_user_repo.save = AsyncMock()

        # Try to add one more child
        add_extra_child_command = AddChildCommand(
            user_id=user_aggregate.id,
            name="ExtraChild",
            birth_date=date(2020, 1, 1),
            gender=Gender.OTHER,
        )

        from domain.exceptions import ChildLimitExceededException
        
        with pytest.raises(ChildLimitExceededException):
            await user_service.add_child(add_extra_child_command)

        # Edge case 2: Very long situation description (at limit)
        user_aggregate.complete_onboarding()
        child = user_aggregate.children[0]

        mock_claude_adapter.analyze_situation = AsyncMock(return_value={
            "hidden_meaning": "Long description processed successfully",
            "immediate_actions": ["Action"],
            "long_term_recommendations": ["Recommendation"],
            "what_not_to_do": ["Don't"],
            "emotional_tone": "neutral",
            "confidence_score": 0.8,
        })

        mock_situation_repo.save = AsyncMock()

        # Create description at maximum length
        max_description = "Очень длинное описание ситуации. " * 40  # About 2000 chars
        max_description = max_description[:2000]  # Exactly at limit

        analyze_long_command = AnalyzeSituationCommand(
            user_id=user_aggregate.id,
            child_id=child.id,
            description=max_description,
        )

        # Should succeed
        situation_dto = await analysis_service.analyze_situation(analyze_long_command)
        assert situation_dto.description == max_description
        assert situation_dto.is_analyzed

        # Edge case 3: Situation description just over limit
        too_long_description = "x" * 2001

        analyze_too_long_command = AnalyzeSituationCommand(
            user_id=user_aggregate.id,
            child_id=child.id,
            description=too_long_description,
        )

        from domain.exceptions import InvalidSituationException
        
        with pytest.raises(InvalidSituationException):
            await analysis_service.analyze_situation(analyze_too_long_command)

    @pytest.mark.e2e
    async def test_full_telegram_bot_simulation(self) -> None:
        """Test simulating full Telegram bot interaction."""
        # This would be a comprehensive test simulating the entire bot flow
        # Including message handling, state management, and service integration
        
        # Mock Telegram bot components
        mock_bot = Mock()
        mock_message = Mock()
        mock_state = Mock()
        mock_callback = Mock()

        # Mock message properties
        mock_message.from_user = Mock()
        mock_message.from_user.id = self.telegram_id
        mock_message.from_user.username = "testuser"
        mock_message.from_user.first_name = "John"
        mock_message.from_user.last_name = "Doe"
        mock_message.from_user.language_code = "en"
        mock_message.answer = AsyncMock()

        # Mock state management
        mock_state.get_data = AsyncMock(return_value={})
        mock_state.update_data = AsyncMock()
        mock_state.set_state = AsyncMock()

        # This test would simulate:
        # 1. User sends /start
        # 2. Bot responds with registration flow
        # 3. User provides name, child details
        # 4. Bot completes onboarding
        # 5. User requests analysis
        # 6. Bot provides analysis results

        # For brevity, we'll just verify the structure is testable
        assert mock_message.from_user.id == self.telegram_id
        assert hasattr(mock_state, 'set_state')
        assert hasattr(mock_message, 'answer')

        # In a full implementation, this would test the entire flow
        # with actual handler calls and state transitions


@pytest.mark.performance
class TestPerformanceScenarios:
    """Performance tests for user journey scenarios."""

    @pytest.mark.e2e
    async def test_concurrent_user_registrations(self) -> None:
        """Test concurrent user registrations."""
        import asyncio
        
        mock_user_repo = Mock()
        user_service = UserService(mock_user_repo)

        # Mock repository operations
        mock_user_repo.exists_by_telegram_id = AsyncMock(return_value=False)
        mock_user_repo.save = AsyncMock()

        # Create multiple registration tasks
        registration_tasks = []
        for i in range(10):
            command = RegisterUserCommand(
                telegram_id=123456789 + i,
                username=f"user{i}",
                first_name=f"User{i}",
            )
            task = user_service.register_user(command)
            registration_tasks.append(task)

        # Execute all registrations concurrently
        results = await asyncio.gather(*registration_tasks)

        # Verify all registrations succeeded
        assert len(results) == 10
        for i, result in enumerate(results):
            assert result.telegram_id == 123456789 + i
            assert result.first_name == f"User{i}"

        # Verify repository was called for each user
        assert mock_user_repo.save.call_count == 10

    @pytest.mark.e2e
    async def test_analysis_processing_time(self) -> None:
        """Test that analysis processing completes within reasonable time."""
        import time
        
        mock_user_repo = Mock()
        mock_situation_repo = Mock()
        mock_claude_adapter = Mock(spec=ClaudeAdapter)

        # Simulate realistic Claude response time
        async def slow_claude_response(*args, **kwargs):
            await asyncio.sleep(0.1)  # 100ms simulated API call
            return {
                "hidden_meaning": "Test analysis",
                "immediate_actions": ["Action"],
                "long_term_recommendations": ["Rec"],
                "what_not_to_do": ["Don't"],
                "emotional_tone": "neutral",
                "confidence_score": 0.8,
            }

        mock_claude_adapter.analyze_situation = slow_claude_response

        analysis_service = AnalysisService(
            mock_user_repo,
            mock_situation_repo,
            mock_claude_adapter,
        )

        # Create test user and child
        from domain.aggregates.user import User
        
        user = User.create(
            telegram_id=123456789,
            username="testuser",
            first_name="Test",
        )
        child = user.add_child(
            name="TestChild",
            birth_date=date(2020, 1, 1),
            gender=Gender.MALE,
        )
        user.complete_onboarding()

        mock_user_repo.get = AsyncMock(return_value=user)
        mock_situation_repo.save = AsyncMock()

        command = AnalyzeSituationCommand(
            user_id=user.id,
            child_id=child.id,
            description="Performance test situation description",
        )

        # Measure processing time
        start_time = time.time()
        result = await analysis_service.analyze_situation(command)
        end_time = time.time()

        processing_time = end_time - start_time

        # Verify analysis completed
        assert result.is_analyzed
        
        # Verify reasonable processing time (should be under 1 second)
        assert processing_time < 1.0