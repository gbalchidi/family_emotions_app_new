.PHONY: help install test lint format run docker-up docker-down migrate clean

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

install: ## Install dependencies with Poetry
	poetry install

test: ## Run tests with coverage
	poetry run pytest tests/ -v --cov=src --cov-report=term-missing

lint: ## Run linting with ruff and mypy
	poetry run ruff check src tests
	poetry run mypy src

format: ## Format code with black and ruff
	poetry run black src tests
	poetry run ruff check --fix src tests

run: ## Run the bot locally
	poetry run python -m src.bot

docker-up: ## Start all services with Docker Compose
	docker-compose up -d

docker-down: ## Stop all Docker services
	docker-compose down

docker-logs: ## Show Docker logs
	docker-compose logs -f bot

migrate: ## Run database migrations
	poetry run alembic upgrade head

migrate-create: ## Create new migration
	@read -p "Enter migration message: " msg; \
	poetry run alembic revision --autogenerate -m "$$msg"

clean: ## Clean cache and temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache

dev-setup: install ## Setup development environment
	cp .env.example .env
	@echo "Please edit .env file with your credentials"
	@echo "Then run: make docker-up && make migrate"