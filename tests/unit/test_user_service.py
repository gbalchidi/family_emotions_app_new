"""User service tests."""
from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest

from application.commands import (
    AddChildCommand,
    CompleteOnboardingCommand,
    GetUserCommand,
    RegisterUserCommand,
)
from application.services.user_service import UserService
from domain.aggregates.user import User
from domain.exceptions import (
    ChildLimitExceededException,
    DomainException,
    UserAlreadyExistsException,
    UserNotFoundException,
)
from domain.repositories.user import UserRepository
from domain.value_objects import Gender


class MockUserRepository:
    """Mock user repository for testing."""

    def __init__(self):
        self.users: dict[UUID, User] = {}
        self.telegram_users: dict[int, User] = {}

    async def save(self, user: User) -> None:
        """Save user."""
        self.users[user.id] = user
        self.telegram_users[user.telegram_user.telegram_id] = user

    async def get(self, user_id: UUID) -> User | None:
        """Get user by ID."""
        return self.users.get(user_id)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """Get user by telegram ID."""
        return self.telegram_users.get(telegram_id)

    async def exists_by_telegram_id(self, telegram_id: int) -> bool:
        """Check if user exists by telegram ID."""
        return telegram_id in self.telegram_users

    async def delete(self, user_id: UUID) -> None:
        """Delete user."""
        user = self.users.get(user_id)
        if user:
            del self.users[user_id]
            del self.telegram_users[user.telegram_user.telegram_id]


class TestUserService:
    """User service test cases."""

    def setup_method(self) -> None:
        """Set up test dependencies."""
        self.user_repository = MockUserRepository()
        self.user_service = UserService(self.user_repository)

    async def test_register_user_success(self) -> None:
        """Test successful user registration."""
        command = RegisterUserCommand(
            telegram_id=123456789,
            username="testuser",
            first_name="John",
            last_name="Doe",
            language_code="en",
        )

        result = await self.user_service.register_user(command)

        # Check result
        assert result.telegram_id == command.telegram_id
        assert result.username == command.username
        assert result.first_name == command.first_name
        assert result.last_name == command.last_name
        assert result.full_name == "John Doe"
        assert not result.onboarding_completed
        assert result.is_active
        assert len(result.children) == 0

        # Check user was saved
        saved_user = await self.user_repository.get_by_telegram_id(command.telegram_id)
        assert saved_user is not None
        assert saved_user.telegram_user.telegram_id == command.telegram_id

    async def test_register_user_already_exists(self) -> None:
        """Test registering user that already exists."""
        command = RegisterUserCommand(
            telegram_id=123456789,
            username="testuser",
            first_name="John",
        )

        # Register user first time
        await self.user_service.register_user(command)

        # Try to register again
        with pytest.raises(UserAlreadyExistsException):
            await self.user_service.register_user(command)

    async def test_register_user_without_optional_fields(self) -> None:
        """Test registering user without optional fields."""
        command = RegisterUserCommand(
            telegram_id=123456789,
            username=None,
            first_name="John",
            last_name=None,
        )

        result = await self.user_service.register_user(command)

        assert result.username is None
        assert result.last_name is None
        assert result.full_name == "John"
        assert result.language_code == "ru"  # Default

    async def test_add_child_success(self) -> None:
        """Test successful child addition."""
        # Register user first
        register_command = RegisterUserCommand(
            telegram_id=123456789,
            username="testuser",
            first_name="John",
        )
        user_dto = await self.user_service.register_user(register_command)

        # Add child
        add_child_command = AddChildCommand(
            user_id=user_dto.id,
            name="Alice",
            birth_date=date(2018, 5, 15),
            gender=Gender.FEMALE,
            notes="Test child",
        )

        result = await self.user_service.add_child(add_child_command)

        # Check result
        assert result.name == "Alice"
        assert result.birth_date == date(2018, 5, 15)
        assert result.gender == Gender.FEMALE
        assert result.notes == "Test child"
        assert result.age_years >= 5  # Approximately 5+ years old

        # Check user was updated
        updated_user = await self.user_repository.get(user_dto.id)
        assert updated_user is not None
        assert len(updated_user.children) == 1
        assert updated_user.children[0].name == "Alice"

    async def test_add_child_user_not_found(self) -> None:
        """Test adding child when user doesn't exist."""
        command = AddChildCommand(
            user_id=uuid4(),
            name="Alice",
            birth_date=date(2018, 5, 15),
            gender=Gender.FEMALE,
        )

        with pytest.raises(UserNotFoundException):
            await self.user_service.add_child(command)

    async def test_add_child_too_many_children(self) -> None:
        """Test adding child when user has too many children."""
        # Register user
        register_command = RegisterUserCommand(
            telegram_id=123456789,
            username="testuser",
            first_name="John",
        )
        user_dto = await self.user_service.register_user(register_command)

        # Add maximum number of children
        for i in range(User.MAX_CHILDREN):
            add_child_command = AddChildCommand(
                user_id=user_dto.id,
                name=f"Child{i}",
                birth_date=date(2018, 1, 1),
                gender=Gender.MALE,
            )
            await self.user_service.add_child(add_child_command)

        # Try to add one more
        extra_child_command = AddChildCommand(
            user_id=user_dto.id,
            name="ExtraChild",
            birth_date=date(2018, 1, 1),
            gender=Gender.FEMALE,
        )

        with pytest.raises(ChildLimitExceededException):
            await self.user_service.add_child(extra_child_command)

    async def test_complete_onboarding_success(self) -> None:
        """Test successful onboarding completion."""
        # Register user and add child
        register_command = RegisterUserCommand(
            telegram_id=123456789,
            username="testuser",
            first_name="John",
        )
        user_dto = await self.user_service.register_user(register_command)

        add_child_command = AddChildCommand(
            user_id=user_dto.id,
            name="Alice",
            birth_date=date(2018, 5, 15),
            gender=Gender.FEMALE,
        )
        await self.user_service.add_child(add_child_command)

        # Complete onboarding
        complete_command = CompleteOnboardingCommand(user_id=user_dto.id)
        result = await self.user_service.complete_onboarding(complete_command)

        # Check result
        assert result.onboarding_completed

        # Check user was updated
        updated_user = await self.user_repository.get(user_dto.id)
        assert updated_user is not None
        assert updated_user.onboarding_completed

    async def test_complete_onboarding_user_not_found(self) -> None:
        """Test completing onboarding when user doesn't exist."""
        command = CompleteOnboardingCommand(user_id=uuid4())

        with pytest.raises(UserNotFoundException):
            await self.user_service.complete_onboarding(command)

    async def test_complete_onboarding_without_children(self) -> None:
        """Test completing onboarding without children."""
        # Register user without children
        register_command = RegisterUserCommand(
            telegram_id=123456789,
            username="testuser",
            first_name="John",
        )
        user_dto = await self.user_service.register_user(register_command)

        # Try to complete onboarding
        complete_command = CompleteOnboardingCommand(user_id=user_dto.id)

        with pytest.raises(DomainException):
            await self.user_service.complete_onboarding(complete_command)

    async def test_get_user_success(self) -> None:
        """Test successful user retrieval by telegram ID."""
        # Register user
        register_command = RegisterUserCommand(
            telegram_id=123456789,
            username="testuser",
            first_name="John",
        )
        await self.user_service.register_user(register_command)

        # Get user
        get_command = GetUserCommand(telegram_id=123456789)
        result = await self.user_service.get_user(get_command)

        # Check result
        assert result is not None
        assert result.telegram_id == 123456789
        assert result.username == "testuser"
        assert result.first_name == "John"

    async def test_get_user_not_found(self) -> None:
        """Test getting user that doesn't exist."""
        command = GetUserCommand(telegram_id=987654321)
        result = await self.user_service.get_user(command)
        assert result is None

    async def test_get_user_by_id_success(self) -> None:
        """Test successful user retrieval by ID."""
        # Register user
        register_command = RegisterUserCommand(
            telegram_id=123456789,
            username="testuser",
            first_name="John",
        )
        user_dto = await self.user_service.register_user(register_command)

        # Get user by ID
        result = await self.user_service.get_user_by_id(user_dto.id)

        # Check result
        assert result is not None
        assert result.id == user_dto.id
        assert result.telegram_id == 123456789

    async def test_get_user_by_id_not_found(self) -> None:
        """Test getting user by ID that doesn't exist."""
        result = await self.user_service.get_user_by_id(uuid4())
        assert result is None

    async def test_dto_conversion_with_children(self) -> None:
        """Test DTO conversion includes children data."""
        # Register user and add multiple children
        register_command = RegisterUserCommand(
            telegram_id=123456789,
            username="testuser",
            first_name="John",
        )
        user_dto = await self.user_service.register_user(register_command)

        # Add first child
        add_child_command1 = AddChildCommand(
            user_id=user_dto.id,
            name="Alice",
            birth_date=date(2018, 5, 15),
            gender=Gender.FEMALE,
            notes="First child",
        )
        child1 = await self.user_service.add_child(add_child_command1)

        # Add second child
        add_child_command2 = AddChildCommand(
            user_id=user_dto.id,
            name="Bob",
            birth_date=date(2020, 3, 10),
            gender=Gender.MALE,
        )
        child2 = await self.user_service.add_child(add_child_command2)

        # Get updated user
        result = await self.user_service.get_user_by_id(user_dto.id)

        # Check children data
        assert result is not None
        assert len(result.children) == 2
        
        # Check first child
        alice = next(c for c in result.children if c.name == "Alice")
        assert alice.birth_date == date(2018, 5, 15)
        assert alice.gender == Gender.FEMALE
        assert alice.notes == "First child"
        assert alice.age_group in ["school_age", "preschooler"]  # Depends on current date

        # Check second child
        bob = next(c for c in result.children if c.name == "Bob")
        assert bob.birth_date == date(2020, 3, 10)
        assert bob.gender == Gender.MALE
        assert bob.notes is None

    @pytest.mark.parametrize(
        "telegram_id,username,first_name,last_name,language_code",
        [
            (123456789, "user1", "John", "Doe", "en"),
            (987654321, None, "Jane", None, "ru"),
            (555666777, "user2", "Bob", "Smith", None),
        ],
    )
    async def test_register_user_various_inputs(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str,
        last_name: str | None,
        language_code: str | None,
    ) -> None:
        """Test user registration with various input combinations."""
        command = RegisterUserCommand(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            language_code=language_code,
        )

        result = await self.user_service.register_user(command)

        assert result.telegram_id == telegram_id
        assert result.username == username
        assert result.first_name == first_name
        assert result.last_name == last_name
        
        # Check default language code
        expected_language_code = language_code or "ru"
        saved_user = await self.user_repository.get_by_telegram_id(telegram_id)
        assert saved_user.telegram_user.language_code == expected_language_code


class TestUserServiceWithMockRepository:
    """Test UserService with mock repository to verify repository interactions."""

    def setup_method(self) -> None:
        """Set up test dependencies with mocks."""
        self.mock_repository = Mock(spec=UserRepository)
        self.user_service = UserService(self.mock_repository)

    async def test_register_user_calls_repository_methods(self) -> None:
        """Test that register_user calls appropriate repository methods."""
        # Setup mocks
        self.mock_repository.exists_by_telegram_id = AsyncMock(return_value=False)
        self.mock_repository.save = AsyncMock()

        command = RegisterUserCommand(
            telegram_id=123456789,
            username="testuser",
            first_name="John",
        )

        await self.user_service.register_user(command)

        # Verify repository calls
        self.mock_repository.exists_by_telegram_id.assert_called_once_with(123456789)
        self.mock_repository.save.assert_called_once()

        # Verify the user passed to save has correct data
        saved_user = self.mock_repository.save.call_args[0][0]
        assert saved_user.telegram_user.telegram_id == 123456789
        assert saved_user.telegram_user.username == "testuser"
        assert saved_user.telegram_user.first_name == "John"

    async def test_add_child_calls_repository_methods(self) -> None:
        """Test that add_child calls appropriate repository methods."""
        # Create a test user
        user = User.create(
            telegram_id=123456789,
            username="testuser",
            first_name="John",
        )
        
        # Setup mocks
        self.mock_repository.get = AsyncMock(return_value=user)
        self.mock_repository.save = AsyncMock()

        command = AddChildCommand(
            user_id=user.id,
            name="Alice",
            birth_date=date(2018, 5, 15),
            gender=Gender.FEMALE,
        )

        await self.user_service.add_child(command)

        # Verify repository calls
        self.mock_repository.get.assert_called_once_with(user.id)
        self.mock_repository.save.assert_called_once_with(user)

        # Verify child was added to user
        assert len(user.children) == 1
        assert user.children[0].name == "Alice"