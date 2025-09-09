"""User application service."""

from typing import Optional
from uuid import UUID

from src.application.commands.user_commands import (
    AddChildCommand,
    RegisterUserCommand,
)
from src.domain.user.aggregates import User
from src.domain.user.repositories import UserRepository


class UserService:
    """User application service."""
    
    def __init__(self, user_repository: UserRepository) -> None:
        self._repository = user_repository
    
    async def register_user(self, command: RegisterUserCommand) -> User:
        """Register a new user."""
        # Check if user already exists
        existing_user = await self._repository.get_by_telegram_id(
            command.telegram_id
        )
        if existing_user:
            raise ValueError(f"User with Telegram ID {command.telegram_id} already exists")
        
        # Create new user
        user = User.register(
            telegram_id=command.telegram_id,
            name=command.parent_name,
            child_name=command.child_name,
            child_age=command.child_age,
            child_gender=command.child_gender
        )
        
        # Save to repository
        await self._repository.save(user)
        
        return user
    
    async def add_child(self, command: AddChildCommand) -> User:
        """Add a child to user's family."""
        user = await self._repository.get_by_id(command.user_id)
        if not user:
            raise ValueError(f"User {command.user_id} not found")
        
        user.add_child(
            name=command.child_name,
            age=command.child_age,
            gender=command.child_gender
        )
        
        await self._repository.save(user)
        
        return user
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        return await self._repository.get_by_telegram_id(telegram_id)