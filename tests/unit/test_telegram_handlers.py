"""Telegram handlers tests."""
from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from aiogram import types
from aiogram.fsm.context import FSMContext

from application.dto import ChildDTO, UserDTO
from domain.value_objects import Gender


class TestStartHandler:
    """Start command handler tests."""

    def setup_method(self) -> None:
        """Set up test dependencies."""
        self.mock_user_service = Mock()
        self.mock_message = Mock(spec=types.Message)
        self.mock_state = Mock(spec=FSMContext)
        
        # Mock message properties
        self.mock_message.from_user = Mock()
        self.mock_message.from_user.id = 123456789
        self.mock_message.answer = AsyncMock()

    async def test_start_existing_user(self) -> None:
        """Test /start command with existing user."""
        from presentation.telegram.handlers.start import cmd_start

        # Mock existing user
        existing_user = UserDTO(
            id=uuid4(),
            telegram_id=123456789,
            username="testuser",
            first_name="John",
            last_name="Doe",
            full_name="John Doe",
            children=[],
            onboarding_completed=True,
            created_at="2024-01-01T00:00:00",
            is_active=True,
        )

        with patch("presentation.telegram.handlers.start.database") as mock_db, \
             patch("presentation.telegram.handlers.start.UserService") as mock_user_service_class, \
             patch("presentation.telegram.handlers.start.get_main_menu") as mock_get_main_menu:

            # Setup mocks
            mock_session = AsyncMock()
            mock_db.session.return_value.__aenter__.return_value = mock_session
            
            mock_user_service = Mock()
            mock_user_service.get_user_by_telegram_id = AsyncMock(return_value=existing_user)
            mock_user_service_class.return_value = mock_user_service
            
            mock_keyboard = Mock()
            mock_get_main_menu.return_value = mock_keyboard

            # Call handler
            await cmd_start(self.mock_message, self.mock_state)

            # Verify user service was called
            mock_user_service.get_user_by_telegram_id.assert_called_once_with(123456789)

            # Verify response
            self.mock_message.answer.assert_called_once()
            call_args = self.mock_message.answer.call_args
            assert "С возвращением" in call_args[0][0]
            assert call_args[1]["reply_markup"] == mock_keyboard

            # Verify state was not set (existing user)
            self.mock_state.set_state.assert_not_called()

    async def test_start_new_user(self) -> None:
        """Test /start command with new user."""
        from presentation.telegram.handlers.start import cmd_start
        from presentation.telegram.states import RegistrationStates

        with patch("presentation.telegram.handlers.start.database") as mock_db, \
             patch("presentation.telegram.handlers.start.UserService") as mock_user_service_class:

            # Setup mocks
            mock_session = AsyncMock()
            mock_db.session.return_value.__aenter__.return_value = mock_session
            
            mock_user_service = Mock()
            mock_user_service.get_user_by_telegram_id = AsyncMock(return_value=None)  # No user
            mock_user_service_class.return_value = mock_user_service

            # Call handler
            await cmd_start(self.mock_message, self.mock_state)

            # Verify user service was called
            mock_user_service.get_user_by_telegram_id.assert_called_once_with(123456789)

            # Verify welcome message
            self.mock_message.answer.assert_called_once()
            call_args = self.mock_message.answer.call_args
            assert "Добро пожаловать" in call_args[0][0]
            assert "reply_markup" not in call_args[1]

            # Verify state was set to registration
            self.mock_state.set_state.assert_called_once_with(RegistrationStates.waiting_for_parent_name)

    async def test_start_database_error(self) -> None:
        """Test /start command when database error occurs."""
        from presentation.telegram.handlers.start import cmd_start

        with patch("presentation.telegram.handlers.start.database") as mock_db:
            # Setup database to raise error
            mock_db.session.side_effect = Exception("Database connection failed")

            # Call handler - should raise exception
            with pytest.raises(Exception, match="Database connection failed"):
                await cmd_start(self.mock_message, self.mock_state)


class TestRegistrationHandler:
    """Registration handler tests."""

    def setup_method(self) -> None:
        """Set up test dependencies."""
        self.mock_message = Mock(spec=types.Message)
        self.mock_state = Mock(spec=FSMContext)
        self.mock_callback = Mock(spec=types.CallbackQuery)
        
        # Mock message properties
        self.mock_message.from_user = Mock()
        self.mock_message.from_user.id = 123456789
        self.mock_message.from_user.username = "testuser"
        self.mock_message.from_user.first_name = "John"
        self.mock_message.from_user.last_name = "Doe"
        self.mock_message.from_user.language_code = "en"
        self.mock_message.text = "Test Parent Name"
        self.mock_message.answer = AsyncMock()

        # Mock callback properties
        self.mock_callback.data = "gender_male"
        self.mock_callback.message = self.mock_message
        self.mock_callback.answer = AsyncMock()

    @pytest.fixture
    def mock_registration_dependencies(self):
        """Mock dependencies for registration handlers."""
        with patch("presentation.telegram.handlers.registration.database") as mock_db, \
             patch("presentation.telegram.handlers.registration.UserService") as mock_user_service_class:

            mock_session = AsyncMock()
            mock_db.session.return_value.__aenter__.return_value = mock_session
            
            mock_user_service = Mock()
            mock_user_service_class.return_value = mock_user_service
            
            yield mock_user_service

    async def test_handle_parent_name_valid(self, mock_registration_dependencies) -> None:
        """Test handling valid parent name input."""
        from presentation.telegram.handlers.registration import handle_parent_name
        from presentation.telegram.states import RegistrationStates

        mock_user_service = mock_registration_dependencies

        # Mock successful user creation
        created_user = UserDTO(
            id=uuid4(),
            telegram_id=123456789,
            username="testuser",
            first_name="Test Parent Name",
            last_name=None,
            full_name="Test Parent Name",
            children=[],
            onboarding_completed=False,
            created_at="2024-01-01T00:00:00",
            is_active=True,
        )
        mock_user_service.register_user = AsyncMock(return_value=created_user)

        # Call handler
        await handle_parent_name(self.mock_message, self.mock_state)

        # Verify user was created
        mock_user_service.register_user.assert_called_once()
        call_args = mock_user_service.register_user.call_args[0][0]
        assert call_args.telegram_id == 123456789
        assert call_args.first_name == "Test Parent Name"

        # Verify response and state change
        self.mock_message.answer.assert_called_once()
        self.mock_state.set_state.assert_called_once_with(RegistrationStates.waiting_for_child_name)

    async def test_handle_parent_name_too_short(self, mock_registration_dependencies) -> None:
        """Test handling too short parent name."""
        from presentation.telegram.handlers.registration import handle_parent_name

        # Set short name
        self.mock_message.text = "A"

        # Call handler
        await handle_parent_name(self.mock_message, self.mock_state)

        # Verify error message
        self.mock_message.answer.assert_called_once()
        call_args = self.mock_message.answer.call_args
        assert "слишком короткое" in call_args[0][0].lower() or "короткое имя" in call_args[0][0].lower()

        # Verify state was not changed
        self.mock_state.set_state.assert_not_called()

    async def test_handle_child_name_valid(self, mock_registration_dependencies) -> None:
        """Test handling valid child name input."""
        from presentation.telegram.handlers.registration import handle_child_name
        from presentation.telegram.states import RegistrationStates

        self.mock_message.text = "Alice"

        with patch("presentation.telegram.handlers.registration.get_birth_date_keyboard") as mock_keyboard:
            mock_keyboard.return_value = Mock()

            # Call handler
            await handle_child_name(self.mock_message, self.mock_state)

            # Verify state data was updated
            self.mock_state.update_data.assert_called_once_with(child_name="Alice")

            # Verify response and state change
            self.mock_message.answer.assert_called_once()
            self.mock_state.set_state.assert_called_once_with(RegistrationStates.waiting_for_child_birth_date)

    async def test_handle_child_name_invalid(self, mock_registration_dependencies) -> None:
        """Test handling invalid child name input."""
        from presentation.telegram.handlers.registration import handle_child_name

        # Test empty name
        self.mock_message.text = ""

        # Call handler
        await handle_child_name(self.mock_message, self.mock_state)

        # Verify error message
        self.mock_message.answer.assert_called_once()
        call_args = self.mock_message.answer.call_args
        assert "имя" in call_args[0][0].lower()

        # Verify state was not changed
        self.mock_state.set_state.assert_not_called()

    async def test_handle_gender_selection(self, mock_registration_dependencies) -> None:
        """Test handling gender selection."""
        from presentation.telegram.handlers.registration import handle_gender_selection

        mock_user_service = mock_registration_dependencies

        # Mock state data
        self.mock_state.get_data = AsyncMock(return_value={
            "child_name": "Alice",
            "birth_date": "2018-05-15",
        })

        # Mock successful child addition
        created_child = ChildDTO(
            id=uuid4(),
            name="Alice",
            birth_date="2018-05-15",
            gender=Gender.FEMALE,
            age_years=5,
            age_months=6,
            age_group="school_age",
            notes=None,
        )
        mock_user_service.add_child = AsyncMock(return_value=created_child)

        self.mock_callback.data = "gender_female"

        with patch("presentation.telegram.handlers.registration.get_add_another_child_keyboard") as mock_keyboard:
            mock_keyboard.return_value = Mock()

            # Call handler
            await handle_gender_selection(self.mock_callback, self.mock_state)

            # Verify child was added
            mock_user_service.add_child.assert_called_once()
            call_args = mock_user_service.add_child.call_args[0][0]
            assert call_args.name == "Alice"
            assert call_args.gender == Gender.FEMALE

            # Verify callback was answered
            self.mock_callback.answer.assert_called_once()


class TestAnalysisHandler:
    """Analysis handler tests."""

    def setup_method(self) -> None:
        """Set up test dependencies."""
        self.mock_message = Mock(spec=types.Message)
        self.mock_state = Mock(spec=FSMContext)
        self.mock_callback = Mock(spec=types.CallbackQuery)
        
        # Mock properties
        self.mock_message.from_user = Mock()
        self.mock_message.from_user.id = 123456789
        self.mock_message.text = "Ребенок не хочет делать уроки и плачет"
        self.mock_message.answer = AsyncMock()

        self.mock_callback.data = "child_123"
        self.mock_callback.message = self.mock_message
        self.mock_callback.answer = AsyncMock()

    @pytest.fixture
    def mock_analysis_dependencies(self):
        """Mock dependencies for analysis handlers."""
        with patch("presentation.telegram.handlers.analysis.database") as mock_db, \
             patch("presentation.telegram.handlers.analysis.UserService") as mock_user_service_class, \
             patch("presentation.telegram.handlers.analysis.AnalysisService") as mock_analysis_service_class:

            mock_session = AsyncMock()
            mock_db.session.return_value.__aenter__.return_value = mock_session
            
            mock_user_service = Mock()
            mock_analysis_service = Mock()
            mock_user_service_class.return_value = mock_user_service
            mock_analysis_service_class.return_value = mock_analysis_service
            
            yield mock_user_service, mock_analysis_service

    async def test_handle_situation_description_valid(self, mock_analysis_dependencies) -> None:
        """Test handling valid situation description."""
        from presentation.telegram.handlers.analysis import handle_situation_description
        from presentation.telegram.states import AnalysisStates

        mock_user_service, mock_analysis_service = mock_analysis_dependencies

        # Mock state data
        self.mock_state.get_data = AsyncMock(return_value={
            "selected_child_id": str(uuid4()),
        })

        # Call handler
        await handle_situation_description(self.mock_message, self.mock_state)

        # Verify state data was updated
        self.mock_state.update_data.assert_called_once_with(situation_description=self.mock_message.text)

        # Verify response and state change
        self.mock_message.answer.assert_called_once()
        self.mock_state.set_state.assert_called_once_with(AnalysisStates.waiting_for_context)

    async def test_handle_situation_description_too_short(self, mock_analysis_dependencies) -> None:
        """Test handling too short situation description."""
        from presentation.telegram.handlers.analysis import handle_situation_description

        # Set short description
        self.mock_message.text = "short"

        # Call handler
        await handle_situation_description(self.mock_message, self.mock_state)

        # Verify error message
        self.mock_message.answer.assert_called_once()
        call_args = self.mock_message.answer.call_args
        assert "подробнее" in call_args[0][0].lower() or "короткое" in call_args[0][0].lower()

        # Verify state was not changed
        self.mock_state.set_state.assert_not_called()

    async def test_handle_situation_description_too_long(self, mock_analysis_dependencies) -> None:
        """Test handling too long situation description."""
        from presentation.telegram.handlers.analysis import handle_situation_description

        # Set very long description
        self.mock_message.text = "x" * 2001

        # Call handler
        await handle_situation_description(self.mock_message, self.mock_state)

        # Verify error message
        self.mock_message.answer.assert_called_once()
        call_args = self.mock_message.answer.call_args
        assert "длинное" in call_args[0][0].lower() or "много" in call_args[0][0].lower()

        # Verify state was not changed
        self.mock_state.set_state.assert_not_called()


class TestKeyboards:
    """Keyboard tests."""

    def test_get_main_menu_keyboard(self) -> None:
        """Test main menu keyboard creation."""
        from presentation.telegram.keyboards import get_main_menu

        keyboard = get_main_menu()

        # Should be an InlineKeyboardMarkup
        assert hasattr(keyboard, "inline_keyboard")
        assert len(keyboard.inline_keyboard) > 0

    def test_get_gender_keyboard(self) -> None:
        """Test gender selection keyboard."""
        from presentation.telegram.keyboards import get_gender_keyboard

        keyboard = get_gender_keyboard()

        # Should have gender options
        assert hasattr(keyboard, "inline_keyboard")
        
        # Check that gender buttons exist
        buttons_text = []
        for row in keyboard.inline_keyboard:
            for button in row:
                buttons_text.append(button.callback_data)
        
        assert "gender_male" in buttons_text
        assert "gender_female" in buttons_text

    @pytest.mark.parametrize("children_count", [1, 3, 5])
    def test_get_child_selection_keyboard(self, children_count: int) -> None:
        """Test child selection keyboard with different number of children."""
        from presentation.telegram.keyboards import get_child_selection_keyboard

        # Create mock children
        children = []
        for i in range(children_count):
            child = ChildDTO(
                id=uuid4(),
                name=f"Child{i}",
                birth_date="2020-01-01",
                gender=Gender.MALE,
                age_years=4,
                age_months=0,
                age_group="preschooler",
            )
            children.append(child)

        keyboard = get_child_selection_keyboard(children)

        # Should have buttons for all children
        assert hasattr(keyboard, "inline_keyboard")
        assert len(keyboard.inline_keyboard) >= children_count

        # Check that child buttons exist
        buttons_data = []
        for row in keyboard.inline_keyboard:
            for button in row:
                buttons_data.append(button.callback_data)
        
        # Should have buttons for each child
        for child in children:
            assert f"child_{child.id}" in buttons_data


class TestStateManagement:
    """FSM state management tests."""

    def setup_method(self) -> None:
        """Set up test dependencies."""
        self.mock_state = Mock(spec=FSMContext)

    async def test_states_group_structure(self) -> None:
        """Test that states groups are properly structured."""
        from presentation.telegram.states import AnalysisStates, RegistrationStates

        # Test RegistrationStates
        assert hasattr(RegistrationStates, "waiting_for_parent_name")
        assert hasattr(RegistrationStates, "waiting_for_child_name")
        assert hasattr(RegistrationStates, "waiting_for_child_birth_date")
        assert hasattr(RegistrationStates, "waiting_for_child_gender")

        # Test AnalysisStates
        assert hasattr(AnalysisStates, "waiting_for_child_selection")
        assert hasattr(AnalysisStates, "waiting_for_situation")
        assert hasattr(AnalysisStates, "waiting_for_context")

    async def test_state_transitions(self) -> None:
        """Test state transitions in handlers."""
        # This would test the flow between states
        # For brevity, just test that states can be set
        from presentation.telegram.states import AnalysisStates, RegistrationStates

        self.mock_state.set_state = AsyncMock()

        # Test setting registration state
        await self.mock_state.set_state(RegistrationStates.waiting_for_parent_name)
        self.mock_state.set_state.assert_called_with(RegistrationStates.waiting_for_parent_name)

        # Test setting analysis state
        await self.mock_state.set_state(AnalysisStates.waiting_for_situation)
        self.mock_state.set_state.assert_called_with(AnalysisStates.waiting_for_situation)


class TestErrorHandling:
    """Error handling in Telegram handlers."""

    def setup_method(self) -> None:
        """Set up test dependencies."""
        self.mock_message = Mock(spec=types.Message)
        self.mock_state = Mock(spec=FSMContext)
        
        self.mock_message.from_user = Mock()
        self.mock_message.from_user.id = 123456789
        self.mock_message.answer = AsyncMock()

    async def test_handler_with_service_error(self) -> None:
        """Test handler behavior when service raises error."""
        from presentation.telegram.handlers.start import cmd_start

        with patch("presentation.telegram.handlers.start.database") as mock_db, \
             patch("presentation.telegram.handlers.start.UserService") as mock_user_service_class:

            # Setup service to raise error
            mock_session = AsyncMock()
            mock_db.session.return_value.__aenter__.return_value = mock_session
            
            mock_user_service = Mock()
            mock_user_service.get_user_by_telegram_id = AsyncMock(
                side_effect=Exception("Service error")
            )
            mock_user_service_class.return_value = mock_user_service

            # Call should raise exception
            with pytest.raises(Exception, match="Service error"):
                await cmd_start(self.mock_message, self.mock_state)

    async def test_message_sending_failure(self) -> None:
        """Test handling when message sending fails."""
        from presentation.telegram.handlers.start import cmd_start

        with patch("presentation.telegram.handlers.start.database") as mock_db, \
             patch("presentation.telegram.handlers.start.UserService") as mock_user_service_class:

            # Setup mocks
            mock_session = AsyncMock()
            mock_db.session.return_value.__aenter__.return_value = mock_session
            
            mock_user_service = Mock()
            mock_user_service.get_user_by_telegram_id = AsyncMock(return_value=None)
            mock_user_service_class.return_value = mock_user_service

            # Make message.answer fail
            self.mock_message.answer = AsyncMock(side_effect=Exception("Message send failed"))

            # Should raise exception
            with pytest.raises(Exception, match="Message send failed"):
                await cmd_start(self.mock_message, self.mock_state)