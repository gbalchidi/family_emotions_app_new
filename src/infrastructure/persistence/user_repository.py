"""User repository implementation."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.user.aggregates import Child, User
from src.domain.user.repositories import UserRepository
from src.domain.user.value_objects import TelegramId, UserName
from src.infrastructure.persistence.models import ChildModel, UserModel


class SqlAlchemyUserRepository(UserRepository):
    """SQLAlchemy implementation of UserRepository."""
    
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
    
    async def save(self, user: User) -> None:
        """Save user aggregate."""
        # Check if user exists
        stmt = select(UserModel).where(UserModel.id == user.id)
        result = await self._session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        if db_user:
            # Update existing user
            db_user.name = str(user.name)
            db_user.updated_at = user.updated_at
            db_user.is_active = user.is_active
            
            # Sync children
            existing_child_ids = {child.id for child in db_user.children}
            domain_child_ids = {child.id for child in user.children}
            
            # Remove deleted children
            for db_child in db_user.children[:]:
                if db_child.id not in domain_child_ids:
                    self._session.delete(db_child)
            
            # Add new children
            for child in user.children:
                if child.id not in existing_child_ids:
                    db_child = ChildModel(
                        id=child.id,
                        user_id=user.id,
                        name=child.name,
                        age=child.age,
                        gender=child.gender,
                        created_at=child.created_at
                    )
                    db_user.children.append(db_child)
        else:
            # Create new user
            db_user = UserModel(
                id=user.id,
                telegram_id=user.telegram_id.value,
                name=str(user.name),
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at
            )
            
            # Add children
            for child in user.children:
                db_child = ChildModel(
                    id=child.id,
                    user_id=user.id,
                    name=child.name,
                    age=child.age,
                    gender=child.gender,
                    created_at=child.created_at
                )
                db_user.children.append(db_child)
            
            self._session.add(db_user)
        
        await self._session.flush()
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        stmt = select(UserModel).options(
            selectinload(UserModel.children)
        ).where(UserModel.id == user_id)
        
        result = await self._session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            return None
        
        return self._to_domain(db_user)
    
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        stmt = select(UserModel).options(
            selectinload(UserModel.children)
        ).where(UserModel.telegram_id == telegram_id)
        
        result = await self._session.execute(stmt)
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            return None
        
        return self._to_domain(db_user)
    
    async def exists_by_telegram_id(self, telegram_id: int) -> bool:
        """Check if user exists by Telegram ID."""
        stmt = select(UserModel.id).where(UserModel.telegram_id == telegram_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None
    
    def _to_domain(self, db_user: UserModel) -> User:
        """Convert database model to domain aggregate."""
        children = [
            Child(
                id=db_child.id,
                name=db_child.name,
                age=db_child.age,
                gender=db_child.gender,
                created_at=db_child.created_at
            )
            for db_child in db_user.children
        ]
        
        return User(
            id=db_user.id,
            telegram_id=TelegramId(db_user.telegram_id),
            name=UserName(db_user.name),
            children=children,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at,
            is_active=db_user.is_active
        )