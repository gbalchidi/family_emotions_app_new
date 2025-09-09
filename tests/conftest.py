"""Test configuration and fixtures."""
from __future__ import annotations

import asyncio
from datetime import date, datetime, timezone
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from anthropic import Anthropic
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from domain.aggregates.situation import Situation
from domain.aggregates.user import User
from domain.value_objects import Child, Gender
from infrastructure.database.session import get_session
from infrastructure.external_services.claude_analyzer import ClaudeAnalyzer
from infrastructure.persistence.database import Base


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
def mock_redis() -> Mock:
    """Create mock Redis client."""
    mock = Mock(spec=Redis)
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = 1
    mock.exists.return_value = False
    return mock


@pytest.fixture
def mock_claude_client() -> Mock:
    """Create mock Claude client."""
    mock = Mock(spec=Anthropic)
    mock_response = Mock()
    mock_response.content = [Mock(text="Mocked Claude response")]
    mock.messages.create.return_value = mock_response
    return mock


@pytest.fixture
def mock_claude_analyzer(mock_claude_client) -> ClaudeAnalyzer:
    """Create mock Claude analyzer."""
    return ClaudeAnalyzer(client=mock_claude_client)


@pytest.fixture
def sample_user() -> User:
    """Create sample user for testing."""
    return User.create(
        telegram_id=123456789,
        username="testuser",
        first_name="Test",
        last_name="User",
        language_code="en",
    )


@pytest.fixture
def sample_user_with_child(sample_user: User) -> User:
    """Create sample user with child."""
    sample_user.add_child(
        name="Alice",
        birth_date=date(2018, 5, 15),
        gender=Gender.FEMALE,
        notes="Test child",
    )
    sample_user.complete_onboarding()
    sample_user.collect_events()  # Clear events
    return sample_user


@pytest.fixture
def sample_child() -> Child:
    """Create sample child for testing."""
    return Child(
        id=uuid4(),
        name="Bob",
        birth_date=date(2019, 3, 10),
        gender=Gender.MALE,
        notes="Sample child for tests",
    )


@pytest.fixture
def sample_situation(sample_user_with_child: User) -> Situation:
    """Create sample situation for testing."""
    child = sample_user_with_child.children[0]
    return Situation.create(
        user_id=sample_user_with_child.id,
        child_id=child.id,
        description="Ребенок не хочет делать уроки и капризничает",
        context="Это происходит каждый день после школы",
    )


@pytest.fixture
def sample_analyzed_situation(sample_situation: Situation) -> Situation:
    """Create sample analyzed situation."""
    sample_situation.apply_analysis(
        hidden_meaning="Ребенок устал после школы и нуждается в отдыхе",
        immediate_actions=[
            "Дать ребенку отдохнуть 15-20 минут",
            "Предложить перекус",
            "Поговорить о том, как прошел день",
        ],
        long_term_recommendations=[
            "Пересмотреть режим дня",
            "Добавить физической активности",
            "Создать уютное место для выполнения домашних заданий",
        ],
        what_not_to_do=[
            "Не повышать голос",
            "Не заставлять силой делать уроки",
            "Не лишать прогулок",
        ],
        emotional_tone="concerning",
        confidence_score=0.85,
    )
    sample_situation.collect_events()  # Clear events
    return sample_situation


@pytest.fixture
def mock_telegram_bot() -> Mock:
    """Create mock Telegram bot."""
    bot = Mock()
    bot.send_message = AsyncMock()
    bot.answer_callback_query = AsyncMock()
    bot.edit_message_text = AsyncMock()
    bot.edit_message_reply_markup = AsyncMock()
    return bot


@pytest.fixture
def mock_telegram_message() -> Mock:
    """Create mock Telegram message."""
    message = Mock()
    message.message_id = 1
    message.chat = Mock()
    message.chat.id = 123456789
    message.from_user = Mock()
    message.from_user.id = 123456789
    message.from_user.username = "testuser"
    message.from_user.first_name = "Test"
    message.from_user.last_name = "User"
    message.from_user.language_code = "en"
    message.text = "Test message"
    message.answer = AsyncMock()
    message.edit_text = AsyncMock()
    return message


@pytest.fixture
def mock_callback_query() -> Mock:
    """Create mock callback query."""
    callback = Mock()
    callback.id = "test_callback"
    callback.data = "test_data"
    callback.message = Mock()
    callback.message.message_id = 1
    callback.message.chat = Mock()
    callback.message.chat.id = 123456789
    callback.from_user = Mock()
    callback.from_user.id = 123456789
    callback.answer = AsyncMock()
    callback.message.edit_text = AsyncMock()
    callback.message.edit_reply_markup = AsyncMock()
    return callback


class TestDataFactory:
    """Factory for creating test data."""

    @staticmethod
    def create_user(
        telegram_id: int = None,
        username: str = None,
        first_name: str = None,
    ) -> User:
        """Create test user."""
        return User.create(
            telegram_id=telegram_id or 123456789,
            username=username or "testuser",
            first_name=first_name or "Test",
            last_name="User",
            language_code="en",
        )

    @staticmethod
    def create_child(
        name: str = None,
        birth_date: date = None,
        gender: Gender = None,
    ) -> Child:
        """Create test child."""
        return Child(
            id=uuid4(),
            name=name or "TestChild",
            birth_date=birth_date or date(2018, 1, 1),
            gender=gender or Gender.MALE,
        )

    @staticmethod
    def create_situation(
        user_id: UUID = None,
        child_id: UUID = None,
        description: str = None,
    ) -> Situation:
        """Create test situation."""
        return Situation.create(
            user_id=user_id or uuid4(),
            child_id=child_id or uuid4(),
            description=description or "Test situation description that is long enough",
            context="Test context",
        )


@pytest.fixture
def test_factory() -> TestDataFactory:
    """Test data factory fixture."""
    return TestDataFactory()


# Performance test configurations
@pytest.fixture
def performance_config():
    """Performance test configuration."""
    return {
        "concurrent_users": 10,
        "requests_per_user": 5,
        "max_response_time": 1.0,  # seconds
    }


# Security test configurations
@pytest.fixture
def security_payloads():
    """Common security test payloads."""
    return {
        "sql_injection": [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users--",
        ],
        "xss": [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
        ],
        "command_injection": [
            "; ls -la",
            "| cat /etc/passwd",
            "&& rm -rf /",
        ],
    }