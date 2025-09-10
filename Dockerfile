FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first
COPY pyproject.toml ./

# Install dependencies using pip directly (without poetry)
RUN pip install --no-cache-dir \
    aiogram==3.13.0 \
    sqlalchemy[asyncio]==2.0.35 \
    asyncpg==0.29.0 \
    psycopg2-binary==2.9.9 \
    redis==5.0.7 \
    anthropic==0.34.0 \
    pydantic==2.8.2 \
    pydantic-settings==2.4.0 \
    alembic==1.13.2 \
    python-dotenv==1.0.1 \
    structlog==24.4.0

# Copy application code
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./
COPY migrations ./migrations
COPY start.sh ./

# Create non-root user
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app && chmod +x /app/start.sh
USER botuser

# Run bot with startup delay
CMD ["/app/start.sh"]