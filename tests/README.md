# Family Emotions Light - Test Suite

Comprehensive test suite for the Family Emotions Light Telegram bot application.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (80% of coverage)
│   ├── test_user_aggregate.py
│   ├── test_situation_aggregate.py
│   ├── test_value_objects.py
│   ├── test_domain_events.py
│   ├── test_user_service.py
│   ├── test_analysis_service.py
│   └── test_telegram_handlers.py
├── integration/             # Integration tests (15% of coverage)
│   ├── test_repositories.py
│   ├── test_claude_adapter.py
│   └── test_redis_cache.py
└── e2e/                     # End-to-end tests (5% of coverage)
    └── test_user_journey.py
```

## Test Pyramid

Our test strategy follows the test pyramid approach:

- **Unit Tests (80%)**: Fast, isolated tests for individual components
- **Integration Tests (15%)**: Tests for component interactions
- **E2E Tests (5%)**: Full user journey tests

## Test Categories

### Unit Tests
- **Domain Layer**: Aggregates, Value Objects, Events
- **Application Layer**: Services with mocked dependencies
- **Presentation Layer**: Telegram handlers and keyboards

### Integration Tests
- **Infrastructure Layer**: Repository implementations with real database
- **External Services**: Claude API adapter with mocked responses
- **Cache Layer**: Redis integration tests

### End-to-End Tests
- **User Journeys**: Complete workflows from registration to analysis
- **Performance Tests**: Response time and throughput validation
- **Error Scenarios**: Comprehensive error handling validation

## Running Tests

### Prerequisites

1. **Install Dependencies**:
   ```bash
   poetry install
   ```

2. **Set Environment Variables**:
   ```bash
   export DATABASE_URL=postgresql://user:pass@localhost:5432/testdb
   export REDIS_URL=redis://localhost:6379
   export ANTHROPIC_API_KEY=test-key
   export TELEGRAM_BOT_TOKEN=test-token
   ```

3. **Start Services** (for integration tests):
   ```bash
   # PostgreSQL
   docker run -d --name postgres-test -p 5432:5432 -e POSTGRES_PASSWORD=testpass postgres:15
   
   # Redis
   docker run -d --name redis-test -p 6379:6379 redis:7-alpine
   ```

### Quick Start

```bash
# Run all tests
./scripts/run_tests.sh

# Run specific test types
./scripts/run_tests.sh unit
./scripts/run_tests.sh integration
./scripts/run_tests.sh e2e
```

### Manual Test Commands

```bash
# Unit tests only
poetry run pytest tests/unit -v

# Integration tests with real services
poetry run pytest tests/integration -v

# E2E tests
poetry run pytest tests/e2e -v

# With coverage
poetry run pytest tests/ --cov=src --cov-report=html

# Performance tests only
poetry run pytest tests/e2e -v -m "performance"

# Run specific test file
poetry run pytest tests/unit/test_user_service.py -v

# Run specific test method
poetry run pytest tests/unit/test_user_service.py::TestUserService::test_register_user_success -v
```

### Test Markers

Use pytest markers to run specific test categories:

```bash
# Run only unit tests
poetry run pytest -m "unit"

# Run only integration tests
poetry run pytest -m "integration"

# Run only E2E tests
poetry run pytest -m "e2e"

# Run only performance tests
poetry run pytest -m "performance"

# Exclude slow tests
poetry run pytest -m "not slow"
```

## Test Configuration

### pytest.ini
Main pytest configuration with markers and settings.

### conftest.py
Shared fixtures including:
- Database session management
- Mock services (Redis, Claude API)
- Test data factories
- Sample aggregates

### Coverage Configuration
- Minimum coverage: 80%
- HTML reports: `htmlcov/index.html`
- XML reports: `coverage.xml`

## Writing Tests

### Test Naming Convention

```python
class TestUserService:
    """Test class for UserService."""
    
    async def test_register_user_success(self) -> None:
        """Test successful user registration."""
        # Arrange
        command = RegisterUserCommand(...)
        
        # Act
        result = await user_service.register_user(command)
        
        # Assert
        assert result.telegram_id == expected_id
```

### Fixture Usage

```python
async def test_with_database(db_session):
    """Test that uses real database."""
    # Test implementation
    
async def test_with_mock_services(mock_redis, mock_claude_adapter):
    """Test with mocked external services."""
    # Test implementation
    
def test_with_sample_data(sample_user_with_child):
    """Test using pre-created sample data."""
    # Test implementation
```

### Parametrized Tests

```python
@pytest.mark.parametrize("age,expected_group", [
    (2, "toddler"),
    (5, "preschooler"),
    (8, "school_age"),
    (15, "teenager"),
])
def test_age_groups(age, expected_group):
    """Test age group classification."""
    child_age = ChildAge(years=age)
    assert child_age.age_group == expected_group
```

### Async Tests

```python
@pytest.mark.asyncio
async def test_async_operation():
    """Test asynchronous operations."""
    result = await some_async_function()
    assert result is not None
```

## Mock Strategies

### Service Layer Mocks
```python
# Mock external dependencies
mock_user_repo = Mock(spec=UserRepository)
mock_user_repo.save = AsyncMock()
mock_user_repo.get = AsyncMock(return_value=user)
```

### API Mocks
```python
# Mock Claude API responses
mock_claude_adapter.analyze_situation = AsyncMock(return_value={
    "hidden_meaning": "Test analysis",
    "immediate_actions": ["Action"],
    # ... rest of response
})
```

### Database Mocks for Unit Tests
```python
# In-memory mock repository
class MockUserRepository:
    def __init__(self):
        self.users = {}
    
    async def save(self, user):
        self.users[user.id] = user
```

## Performance Testing

### Benchmarking
```python
@pytest.mark.performance
async def test_analysis_performance():
    """Test analysis response time."""
    start = time.time()
    await analysis_service.analyze_situation(command)
    end = time.time()
    
    assert (end - start) < 1.0  # Under 1 second
```

### Load Testing
```python
@pytest.mark.performance
async def test_concurrent_analysis():
    """Test concurrent analysis requests."""
    tasks = [
        analysis_service.analyze_situation(command)
        for _ in range(10)
    ]
    
    results = await asyncio.gather(*tasks)
    assert len(results) == 10
```

## Continuous Integration

### GitHub Actions
The `.github/workflows/test.yml` file defines:
- Multi-Python version testing (3.11, 3.12)
- Service dependencies (PostgreSQL, Redis)
- Test execution with coverage reporting
- Security scanning
- Code quality checks

### Coverage Reports
- Codecov integration for coverage tracking
- SonarCloud for code quality analysis
- HTML reports in GitHub Actions artifacts

## Troubleshooting

### Common Issues

1. **Database Connection Errors**:
   ```bash
   # Check PostgreSQL is running
   pg_isready -h localhost -p 5432
   
   # Or use Docker
   docker run --name postgres-test -p 5432:5432 -e POSTGRES_PASSWORD=testpass -d postgres:15
   ```

2. **Redis Connection Errors**:
   ```bash
   # Check Redis is running
   redis-cli ping
   
   # Or use Docker
   docker run --name redis-test -p 6379:6379 -d redis:7-alpine
   ```

3. **Import Errors**:
   ```bash
   # Make sure project is installed in development mode
   poetry install
   
   # Check PYTHONPATH includes src directory
   export PYTHONPATH="${PYTHONPATH}:./src"
   ```

4. **Async Test Issues**:
   ```python
   # Make sure to use pytest-asyncio
   @pytest.mark.asyncio
   async def test_async_function():
       # Test implementation
   ```

### Test Data Management

For integration tests that modify database state:
- Each test gets a fresh database session
- Transactions are rolled back after each test
- Use factories for consistent test data creation

### Debugging Tests

```bash
# Run with verbose output and stop on first failure
poetry run pytest tests/ -v -x

# Run with pdb debugger
poetry run pytest tests/ --pdb

# Show print statements
poetry run pytest tests/ -s

# Run specific failing test
poetry run pytest tests/unit/test_user_service.py::TestUserService::test_failing_case -v -s
```

## Best Practices

1. **Test Independence**: Each test should be completely independent
2. **Clear Naming**: Test names should describe what is being tested
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Mock External Dependencies**: Don't depend on external services in unit tests
5. **Test Edge Cases**: Include boundary conditions and error scenarios
6. **Keep Tests Fast**: Unit tests should run in milliseconds
7. **Maintain High Coverage**: Aim for >80% overall coverage
8. **Review Test Quality**: Tests should be as well-written as production code

## Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Ensure all existing tests pass
3. Add integration tests for new external integrations
4. Update test documentation for new test patterns
5. Maintain or improve coverage percentage