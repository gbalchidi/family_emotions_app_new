"""Database repository implementations."""
from __future__ import annotations

import json
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from domain.aggregates.situation import Situation
from domain.aggregates.user import User
from domain.repositories.situation import SituationRepository
from domain.repositories.user import UserRepository
from domain.value_objects import AnalysisResult, Child, EmotionalTone, Gender, TelegramUser
from infrastructure.database.models import ChildModel, SituationModel, UserModel


class SQLAlchemyUserRepository(UserRepository):
    """SQLAlchemy user repository implementation."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository."""
        self.session = session

    async def save(self, user: User) -> None:
        """Save user aggregate."""
        # Check if user exists
        stmt = select(UserModel).where(UserModel.id == user.id)
        result = await self.session.execute(stmt)
        db_user = result.scalar_one_or_none()

        if db_user:
            # Update existing
            db_user.username = user.telegram_user.username
            db_user.first_name = user.telegram_user.first_name
            db_user.last_name = user.telegram_user.last_name
            db_user.language_code = user.telegram_user.language_code
            db_user.onboarding_completed = user.onboarding_completed
            db_user.is_active = user.is_active
            db_user.updated_at = user.updated_at

            # Update children
            existing_child_ids = {child.id for child in db_user.children}
            current_child_ids = {child.id for child in user.children}

            # Remove deleted children
            for child in db_user.children:
                if child.id not in current_child_ids:
                    await self.session.delete(child)

            # Add or update children
            for child in user.children:
                if child.id not in existing_child_ids:
                    db_child = ChildModel(
                        id=child.id,
                        user_id=user.id,
                        name=child.name,
                        birth_date=child.birth_date,
                        gender=child.gender.value,
                        notes=child.notes,
                    )
                    self.session.add(db_child)
        else:
            # Create new
            db_user = UserModel(
                id=user.id,
                telegram_id=user.telegram_user.telegram_id,
                username=user.telegram_user.username,
                first_name=user.telegram_user.first_name,
                last_name=user.telegram_user.last_name,
                language_code=user.telegram_user.language_code,
                onboarding_completed=user.onboarding_completed,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )

            # Add children
            for child in user.children:
                db_child = ChildModel(
                    id=child.id,
                    user_id=user.id,
                    name=child.name,
                    birth_date=child.birth_date,
                    gender=child.gender.value,
                    notes=child.notes,
                )
                db_user.children.append(db_child)

            self.session.add(db_user)

        # Process domain events (could publish to event bus here)
        for event in user.collect_events():
            # Log or publish event
            pass

    async def get(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        stmt = (
            select(UserModel)
            .options(selectinload(UserModel.children))
            .where(UserModel.id == user_id)
        )
        result = await self.session.execute(stmt)
        db_user = result.scalar_one_or_none()

        if not db_user:
            return None

        return self._to_domain(db_user)

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        stmt = (
            select(UserModel)
            .options(selectinload(UserModel.children))
            .where(UserModel.telegram_id == telegram_id)
        )
        result = await self.session.execute(stmt)
        db_user = result.scalar_one_or_none()

        if not db_user:
            return None

        return self._to_domain(db_user)

    async def exists_by_telegram_id(self, telegram_id: int) -> bool:
        """Check if user exists by Telegram ID."""
        stmt = select(func.count()).select_from(UserModel).where(
            UserModel.telegram_id == telegram_id
        )
        result = await self.session.execute(stmt)
        count = result.scalar()
        return count > 0

    async def delete(self, user_id: UUID) -> None:
        """Delete user by ID."""
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(stmt)
        db_user = result.scalar_one_or_none()

        if db_user:
            await self.session.delete(db_user)

    def _to_domain(self, db_user: UserModel) -> User:
        """Convert database model to domain aggregate."""
        telegram_user = TelegramUser(
            telegram_id=db_user.telegram_id,
            username=db_user.username,
            first_name=db_user.first_name,
            last_name=db_user.last_name,
            language_code=db_user.language_code,
        )

        user = User(
            id=db_user.id,
            telegram_user=telegram_user,
            onboarding_completed=db_user.onboarding_completed,
            created_at=db_user.created_at,
            updated_at=db_user.updated_at,
            is_active=db_user.is_active,
        )

        # Add children
        for db_child in db_user.children:
            child = Child(
                id=db_child.id,
                name=db_child.name,
                birth_date=db_child.birth_date.date()
                if isinstance(db_child.birth_date, datetime)
                else db_child.birth_date,
                gender=Gender(db_child.gender),
                notes=db_child.notes,
            )
            user.children.append(child)

        return user


class SQLAlchemySituationRepository(SituationRepository):
    """SQLAlchemy situation repository implementation."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository."""
        self.session = session

    async def save(self, situation: Situation) -> None:
        """Save situation aggregate."""
        # Check if situation exists
        stmt = select(SituationModel).where(SituationModel.id == situation.id)
        result = await self.session.execute(stmt)
        db_situation = result.scalar_one_or_none()

        if db_situation:
            # Update existing
            db_situation.description = situation.description
            db_situation.context = situation.context
            db_situation.analyzed_at = situation.analyzed_at

            if situation.analysis_result:
                db_situation.hidden_meaning = situation.analysis_result.hidden_meaning
                db_situation.immediate_actions = json.dumps(
                    situation.analysis_result.immediate_actions
                )
                db_situation.long_term_recommendations = json.dumps(
                    situation.analysis_result.long_term_recommendations
                )
                db_situation.what_not_to_do = json.dumps(
                    situation.analysis_result.what_not_to_do
                )
                db_situation.emotional_tone = situation.analysis_result.emotional_tone.value
                db_situation.confidence_score = situation.analysis_result.confidence_score
        else:
            # Create new
            db_situation = SituationModel(
                id=situation.id,
                user_id=situation.user_id,
                child_id=situation.child_id,
                description=situation.description,
                context=situation.context,
                created_at=situation.created_at,
                analyzed_at=situation.analyzed_at,
            )

            if situation.analysis_result:
                db_situation.hidden_meaning = situation.analysis_result.hidden_meaning
                db_situation.immediate_actions = json.dumps(
                    situation.analysis_result.immediate_actions
                )
                db_situation.long_term_recommendations = json.dumps(
                    situation.analysis_result.long_term_recommendations
                )
                db_situation.what_not_to_do = json.dumps(
                    situation.analysis_result.what_not_to_do
                )
                db_situation.emotional_tone = situation.analysis_result.emotional_tone.value
                db_situation.confidence_score = situation.analysis_result.confidence_score

            self.session.add(db_situation)

        # Process domain events
        for event in situation.collect_events():
            # Log or publish event
            pass

    async def get(self, situation_id: UUID) -> Optional[Situation]:
        """Get situation by ID."""
        stmt = select(SituationModel).where(SituationModel.id == situation_id)
        result = await self.session.execute(stmt)
        db_situation = result.scalar_one_or_none()

        if not db_situation:
            return None

        return self._to_domain(db_situation)

    async def get_user_situations(
        self, user_id: UUID, limit: int = 10, offset: int = 0
    ) -> list[Situation]:
        """Get user's situations."""
        stmt = (
            select(SituationModel)
            .where(SituationModel.user_id == user_id)
            .order_by(SituationModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        db_situations = result.scalars().all()

        return [self._to_domain(s) for s in db_situations]

    async def get_child_situations(
        self, child_id: UUID, limit: int = 10, offset: int = 0
    ) -> list[Situation]:
        """Get child's situations."""
        stmt = (
            select(SituationModel)
            .where(SituationModel.child_id == child_id)
            .order_by(SituationModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        db_situations = result.scalars().all()

        return [self._to_domain(s) for s in db_situations]

    async def count_user_situations(self, user_id: UUID) -> int:
        """Count user's situations."""
        stmt = select(func.count()).select_from(SituationModel).where(
            SituationModel.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def delete(self, situation_id: UUID) -> None:
        """Delete situation by ID."""
        stmt = select(SituationModel).where(SituationModel.id == situation_id)
        result = await self.session.execute(stmt)
        db_situation = result.scalar_one_or_none()

        if db_situation:
            await self.session.delete(db_situation)

    def _to_domain(self, db_situation: SituationModel) -> Situation:
        """Convert database model to domain aggregate."""
        situation = Situation(
            id=db_situation.id,
            user_id=db_situation.user_id,
            child_id=db_situation.child_id,
            description=db_situation.description,
            context=db_situation.context,
            created_at=db_situation.created_at,
            analyzed_at=db_situation.analyzed_at,
        )

        if db_situation.hidden_meaning:
            situation.analysis_result = AnalysisResult(
                hidden_meaning=db_situation.hidden_meaning,
                immediate_actions=json.loads(db_situation.immediate_actions or "[]"),
                long_term_recommendations=json.loads(
                    db_situation.long_term_recommendations or "[]"
                ),
                what_not_to_do=json.loads(db_situation.what_not_to_do or "[]"),
                emotional_tone=EmotionalTone(db_situation.emotional_tone),
                confidence_score=db_situation.confidence_score or 0.8,
                analyzed_at=db_situation.analyzed_at,
            )

        return situation