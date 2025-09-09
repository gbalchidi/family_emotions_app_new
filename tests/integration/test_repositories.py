"""Integration tests for repositories."""
from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest

from domain.aggregates.situation import Situation
from domain.aggregates.user import User
from domain.value_objects import EmotionalTone, Gender


class TestUserRepositoryIntegration:
    """User repository integration tests."""

    async def test_save_and_get_user(self, db_session) -> None:
        """Test saving and retrieving user from database."""
        # Import here to avoid circular imports
        from infrastructure.persistence.user_repository import UserRepositoryImpl

        repository = UserRepositoryImpl(db_session)

        # Create user
        user = User.create(
            telegram_id=123456789,
            username="testuser",
            first_name="John",
            last_name="Doe",
            language_code="en",
        )

        # Add child
        child = user.add_child(
            name="Alice",
            birth_date=date(2018, 5, 15),
            gender=Gender.FEMALE,
            notes="Test child",
        )

        # Save user
        await repository.save(user)
        await db_session.commit()

        # Retrieve user
        retrieved_user = await repository.get(user.id)
        
        # Verify user data
        assert retrieved_user is not None
        assert retrieved_user.id == user.id
        assert retrieved_user.telegram_user.telegram_id == 123456789
        assert retrieved_user.telegram_user.username == "testuser"
        assert retrieved_user.telegram_user.first_name == "John"
        assert retrieved_user.telegram_user.last_name == "Doe"
        assert retrieved_user.telegram_user.language_code == "en"
        
        # Verify children
        assert len(retrieved_user.children) == 1
        retrieved_child = retrieved_user.children[0]
        assert retrieved_child.id == child.id
        assert retrieved_child.name == "Alice"
        assert retrieved_child.birth_date == date(2018, 5, 15)
        assert retrieved_child.gender == Gender.FEMALE
        assert retrieved_child.notes == "Test child"

    async def test_get_user_by_telegram_id(self, db_session) -> None:
        """Test retrieving user by telegram ID."""
        from infrastructure.persistence.user_repository import UserRepositoryImpl

        repository = UserRepositoryImpl(db_session)

        # Create and save user
        user = User.create(
            telegram_id=987654321,
            username="testuser2",
            first_name="Jane",
        )
        await repository.save(user)
        await db_session.commit()

        # Retrieve by telegram ID
        retrieved_user = await repository.get_by_telegram_id(987654321)
        
        assert retrieved_user is not None
        assert retrieved_user.id == user.id
        assert retrieved_user.telegram_user.telegram_id == 987654321
        assert retrieved_user.telegram_user.username == "testuser2"

    async def test_exists_by_telegram_id(self, db_session) -> None:
        """Test checking user existence by telegram ID."""
        from infrastructure.persistence.user_repository import UserRepositoryImpl

        repository = UserRepositoryImpl(db_session)

        # Check non-existent user
        exists = await repository.exists_by_telegram_id(111111111)
        assert not exists

        # Create and save user
        user = User.create(
            telegram_id=111111111,
            username="existinguser",
            first_name="Existing",
        )
        await repository.save(user)
        await db_session.commit()

        # Check existing user
        exists = await repository.exists_by_telegram_id(111111111)
        assert exists

    async def test_user_not_found(self, db_session) -> None:
        """Test retrieving non-existent user."""
        from infrastructure.persistence.user_repository import UserRepositoryImpl

        repository = UserRepositoryImpl(db_session)

        # Try to get non-existent user
        user = await repository.get(uuid4())
        assert user is None

        # Try to get by non-existent telegram ID
        user = await repository.get_by_telegram_id(999999999)
        assert user is None

    async def test_update_user(self, db_session) -> None:
        """Test updating existing user."""
        from infrastructure.persistence.user_repository import UserRepositoryImpl

        repository = UserRepositoryImpl(db_session)

        # Create and save user
        user = User.create(
            telegram_id=123456789,
            username="testuser",
            first_name="John",
        )
        await repository.save(user)
        await db_session.commit()

        # Add child and complete onboarding
        user.add_child(
            name="Bob",
            birth_date=date(2020, 1, 1),
            gender=Gender.MALE,
        )
        user.complete_onboarding()

        # Update user
        await repository.save(user)
        await db_session.commit()

        # Retrieve updated user
        updated_user = await repository.get(user.id)
        
        assert updated_user is not None
        assert len(updated_user.children) == 1
        assert updated_user.onboarding_completed
        assert updated_user.children[0].name == "Bob"

    async def test_multiple_children(self, db_session) -> None:
        """Test user with multiple children."""
        from infrastructure.persistence.user_repository import UserRepositoryImpl

        repository = UserRepositoryImpl(db_session)

        # Create user with multiple children
        user = User.create(
            telegram_id=123456789,
            username="parentuser",
            first_name="Parent",
        )

        child1 = user.add_child(
            name="Alice",
            birth_date=date(2018, 5, 15),
            gender=Gender.FEMALE,
        )

        child2 = user.add_child(
            name="Bob",
            birth_date=date(2020, 3, 10),
            gender=Gender.MALE,
            notes="Second child",
        )

        child3 = user.add_child(
            name="Charlie",
            birth_date=date(2016, 12, 25),
            gender=Gender.OTHER,
        )

        await repository.save(user)
        await db_session.commit()

        # Retrieve and verify
        retrieved_user = await repository.get(user.id)
        
        assert retrieved_user is not None
        assert len(retrieved_user.children) == 3

        # Verify children are correctly stored and retrieved
        names = {child.name for child in retrieved_user.children}
        assert names == {"Alice", "Bob", "Charlie"}

        # Find specific children and verify their data
        alice = next(c for c in retrieved_user.children if c.name == "Alice")
        bob = next(c for c in retrieved_user.children if c.name == "Bob")
        charlie = next(c for c in retrieved_user.children if c.name == "Charlie")

        assert alice.birth_date == date(2018, 5, 15)
        assert alice.gender == Gender.FEMALE
        assert alice.notes is None

        assert bob.birth_date == date(2020, 3, 10)
        assert bob.gender == Gender.MALE
        assert bob.notes == "Second child"

        assert charlie.birth_date == date(2016, 12, 25)
        assert charlie.gender == Gender.OTHER
        assert charlie.notes is None


class TestSituationRepositoryIntegration:
    """Situation repository integration tests."""

    async def test_save_and_get_situation(self, db_session, sample_user_with_child) -> None:
        """Test saving and retrieving situation from database."""
        from infrastructure.persistence.analysis_repository import SituationRepositoryImpl

        repository = SituationRepositoryImpl(db_session)

        # Create situation
        child = sample_user_with_child.children[0]
        situation = Situation.create(
            user_id=sample_user_with_child.id,
            child_id=child.id,
            description="Ребенок не хочет делать уроки и капризничает",
            context="Это происходит каждый день после школы",
        )

        # Apply analysis
        situation.apply_analysis(
            hidden_meaning="Ребенок устал и нуждается в отдыхе",
            immediate_actions=[
                "Дать отдохнуть",
                "Предложить перекус",
            ],
            long_term_recommendations=[
                "Пересмотреть режим дня",
                "Добавить активности",
            ],
            what_not_to_do=[
                "Не кричать",
                "Не наказывать",
            ],
            emotional_tone=EmotionalTone.CONCERNING,
            confidence_score=0.85,
        )

        # Save situation
        await repository.save(situation)
        await db_session.commit()

        # Retrieve situation
        retrieved_situation = await repository.get(situation.id)
        
        # Verify basic data
        assert retrieved_situation is not None
        assert retrieved_situation.id == situation.id
        assert retrieved_situation.user_id == sample_user_with_child.id
        assert retrieved_situation.child_id == child.id
        assert retrieved_situation.description == "Ребенок не хочет делать уроки и капризничает"
        assert retrieved_situation.context == "Это происходит каждый день после школы"
        assert retrieved_situation.is_analyzed

        # Verify analysis result
        analysis = retrieved_situation.analysis_result
        assert analysis is not None
        assert analysis.hidden_meaning == "Ребенок устал и нуждается в отдыхе"
        assert len(analysis.immediate_actions) == 2
        assert "Дать отдохнуть" in analysis.immediate_actions
        assert "Предложить перекус" in analysis.immediate_actions
        assert len(analysis.long_term_recommendations) == 2
        assert len(analysis.what_not_to_do) == 2
        assert analysis.emotional_tone == EmotionalTone.CONCERNING
        assert analysis.confidence_score == 0.85

    async def test_get_user_situations(self, db_session, sample_user_with_child) -> None:
        """Test retrieving user's situations."""
        from infrastructure.persistence.analysis_repository import SituationRepositoryImpl

        repository = SituationRepositoryImpl(db_session)
        child = sample_user_with_child.children[0]

        # Create multiple situations
        situation1 = Situation.create(
            user_id=sample_user_with_child.id,
            child_id=child.id,
            description="First situation description that is long enough",
        )

        situation2 = Situation.create(
            user_id=sample_user_with_child.id,
            child_id=child.id,
            description="Second situation description that is long enough",
        )

        situation3 = Situation.create(
            user_id=sample_user_with_child.id,
            child_id=child.id,
            description="Third situation description that is long enough",
        )

        # Save situations
        await repository.save(situation1)
        await repository.save(situation2)
        await repository.save(situation3)
        await db_session.commit()

        # Get user situations
        user_situations = await repository.get_user_situations(
            sample_user_with_child.id,
            limit=10,
            offset=0,
        )

        # Verify results
        assert len(user_situations) == 3
        situation_ids = {s.id for s in user_situations}
        assert situation_ids == {situation1.id, situation2.id, situation3.id}

        # All situations should belong to the same user
        for situation in user_situations:
            assert situation.user_id == sample_user_with_child.id
            assert situation.child_id == child.id

    async def test_get_user_situations_with_pagination(self, db_session, sample_user_with_child) -> None:
        """Test retrieving user's situations with pagination."""
        from infrastructure.persistence.analysis_repository import SituationRepositoryImpl

        repository = SituationRepositoryImpl(db_session)
        child = sample_user_with_child.children[0]

        # Create 5 situations
        situations = []
        for i in range(5):
            situation = Situation.create(
                user_id=sample_user_with_child.id,
                child_id=child.id,
                description=f"Situation {i} description that is long enough",
            )
            situations.append(situation)
            await repository.save(situation)

        await db_session.commit()

        # Test first page
        first_page = await repository.get_user_situations(
            sample_user_with_child.id,
            limit=3,
            offset=0,
        )
        assert len(first_page) == 3

        # Test second page
        second_page = await repository.get_user_situations(
            sample_user_with_child.id,
            limit=3,
            offset=3,
        )
        assert len(second_page) == 2

        # Ensure no overlap between pages
        first_page_ids = {s.id for s in first_page}
        second_page_ids = {s.id for s in second_page}
        assert first_page_ids.isdisjoint(second_page_ids)

        # All situations should be accounted for
        all_situation_ids = {s.id for s in situations}
        retrieved_ids = first_page_ids.union(second_page_ids)
        assert retrieved_ids == all_situation_ids

    async def test_situation_not_found(self, db_session) -> None:
        """Test retrieving non-existent situation."""
        from infrastructure.persistence.analysis_repository import SituationRepositoryImpl

        repository = SituationRepositoryImpl(db_session)

        # Try to get non-existent situation
        situation = await repository.get(uuid4())
        assert situation is None

    async def test_empty_user_situations(self, db_session) -> None:
        """Test retrieving situations for user with no situations."""
        from infrastructure.persistence.analysis_repository import SituationRepositoryImpl

        repository = SituationRepositoryImpl(db_session)

        # Get situations for non-existent user
        user_situations = await repository.get_user_situations(uuid4())
        assert user_situations == []

    async def test_situation_without_analysis(self, db_session, sample_user_with_child) -> None:
        """Test situation without analysis result."""
        from infrastructure.persistence.analysis_repository import SituationRepositoryImpl

        repository = SituationRepositoryImpl(db_session)

        # Create situation without analysis
        child = sample_user_with_child.children[0]
        situation = Situation.create(
            user_id=sample_user_with_child.id,
            child_id=child.id,
            description="Unanalyzed situation description that is long enough",
        )

        # Save situation
        await repository.save(situation)
        await db_session.commit()

        # Retrieve situation
        retrieved_situation = await repository.get(situation.id)
        
        assert retrieved_situation is not None
        assert not retrieved_situation.is_analyzed
        assert retrieved_situation.analysis_result is None
        assert retrieved_situation.analyzed_at is None


@pytest.mark.integration
class TestRepositoryTransactions:
    """Test repository transaction handling."""

    async def test_rollback_on_error(self, db_session) -> None:
        """Test that transaction is rolled back on error."""
        from infrastructure.persistence.user_repository import UserRepositoryImpl

        repository = UserRepositoryImpl(db_session)

        # Create user
        user = User.create(
            telegram_id=123456789,
            username="testuser",
            first_name="John",
        )

        # Save user
        await repository.save(user)

        # Verify user exists in session but not committed
        retrieved_user = await repository.get(user.id)
        assert retrieved_user is not None

        # Rollback transaction
        await db_session.rollback()

        # Verify user no longer exists after rollback
        retrieved_user = await repository.get(user.id)
        assert retrieved_user is None

    async def test_concurrent_access(self, test_engine) -> None:
        """Test concurrent access to repositories."""
        from infrastructure.persistence.user_repository import UserRepositoryImpl
        from sqlalchemy.ext.asyncio import AsyncSession

        # Create two separate sessions
        async with AsyncSession(test_engine) as session1:
            async with AsyncSession(test_engine) as session2:
                repository1 = UserRepositoryImpl(session1)
                repository2 = UserRepositoryImpl(session2)

                # Create user in first session
                user = User.create(
                    telegram_id=123456789,
                    username="testuser",
                    first_name="John",
                )

                await repository1.save(user)
                await session1.commit()

                # Retrieve from second session
                retrieved_user = await repository2.get_by_telegram_id(123456789)
                
                assert retrieved_user is not None
                assert retrieved_user.telegram_user.telegram_id == 123456789

    async def test_batch_operations(self, db_session) -> None:
        """Test batch repository operations."""
        from infrastructure.persistence.user_repository import UserRepositoryImpl

        repository = UserRepositoryImpl(db_session)

        # Create multiple users
        users = []
        for i in range(5):
            user = User.create(
                telegram_id=123456789 + i,
                username=f"user{i}",
                first_name=f"User{i}",
            )
            users.append(user)
            await repository.save(user)

        # Commit all at once
        await db_session.commit()

        # Verify all users were saved
        for i, original_user in enumerate(users):
            retrieved_user = await repository.get_by_telegram_id(123456789 + i)
            assert retrieved_user is not None
            assert retrieved_user.id == original_user.id
            assert retrieved_user.telegram_user.username == f"user{i}"