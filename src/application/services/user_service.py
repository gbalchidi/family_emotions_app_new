"""User service."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from domain.aggregates.user import User
from domain.exceptions import UserAlreadyExistsException, UserNotFoundException
from domain.repositories.user import UserRepository
from application.commands import (
    AddChildCommand,
    CompleteOnboardingCommand,
    GetUserCommand,
    RegisterUserCommand,
)
from application.dto import ChildDTO, UserDTO


class UserService:
    """User application service."""

    def __init__(self, user_repository: UserRepository) -> None:
        """Initialize user service."""
        self.user_repository = user_repository

    async def register_user(self, command: RegisterUserCommand) -> UserDTO:
        """Register new user."""
        # Check if user already exists
        if await self.user_repository.exists_by_telegram_id(command.telegram_id):
            raise UserAlreadyExistsException(command.telegram_id)

        # Create user aggregate
        user = User.create(
            telegram_id=command.telegram_id,
            username=command.username,
            first_name=command.first_name,
            last_name=command.last_name,
            language_code=command.language_code,
        )

        # Save user
        await self.user_repository.save(user)

        return self._to_dto(user)

    async def add_child(self, command: AddChildCommand) -> ChildDTO:
        """Add child to user."""
        # Get user
        user = await self.user_repository.get(command.user_id)
        if not user:
            raise UserNotFoundException(str(command.user_id))

        # Add child
        child = user.add_child(
            name=command.name,
            birth_date=command.birth_date,
            gender=command.gender,
            notes=command.notes,
        )

        # Save user
        await self.user_repository.save(user)

        return self._child_to_dto(child)

    async def complete_onboarding(self, command: CompleteOnboardingCommand) -> UserDTO:
        """Complete user onboarding."""
        # Get user
        user = await self.user_repository.get(command.user_id)
        if not user:
            raise UserNotFoundException(str(command.user_id))

        # Complete onboarding
        user.complete_onboarding()

        # Save user
        await self.user_repository.save(user)

        return self._to_dto(user)

    async def get_user(self, command: GetUserCommand) -> Optional[UserDTO]:
        """Get user by telegram ID."""
        user = await self.user_repository.get_by_telegram_id(command.telegram_id)
        if not user:
            return None

        return self._to_dto(user)

    async def get_user_by_id(self, user_id: UUID) -> Optional[UserDTO]:
        """Get user by ID."""
        user = await self.user_repository.get(user_id)
        if not user:
            return None

        return self._to_dto(user)

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[UserDTO]:
        """Get user by telegram ID."""
        user = await self.user_repository.get_by_telegram_id(telegram_id)
        if not user:
            return None

        return self._to_dto(user)

    def _to_dto(self, user: User) -> UserDTO:
        """Convert user to DTO."""
        return UserDTO(
            id=user.id,
            telegram_id=user.telegram_user.telegram_id,
            username=user.telegram_user.username,
            first_name=user.telegram_user.first_name,
            last_name=user.telegram_user.last_name,
            full_name=user.telegram_user.full_name,
            children=[self._child_to_dto(child) for child in user.children],
            onboarding_completed=user.onboarding_completed,
            created_at=user.created_at,
            is_active=user.is_active,
        )

    def _child_to_dto(self, child) -> ChildDTO:
        """Convert child to DTO."""
        age = child.age
        return ChildDTO(
            id=child.id,
            name=child.name,
            birth_date=child.birth_date,
            gender=child.gender,
            age_years=age.years,
            age_months=age.months or 0,
            age_group=age.age_group,
            notes=child.notes,
        )