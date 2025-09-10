"""Application configuration module."""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Bot Configuration
    bot_token: str = Field(description="Telegram bot token")
    anthropic_api_key: str = Field(description="Anthropic API key")

    # Database Configuration
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)
    postgres_db: str = Field(default="family_emotions")
    postgres_user: str = Field(default="family_bot")
    postgres_password: str = Field(default="changeme")
    
    @property
    def database_url(self) -> str:
        """Construct database URL from components."""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    database_pool_size: int = Field(default=20)
    database_max_overflow: int = Field(default=10)
    database_echo: bool = Field(default=False)

    # Redis Configuration
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=0)
    
    @property
    def redis_url(self) -> str:
        """Construct Redis URL from components."""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    redis_pool_size: int = Field(default=10)

    # Application Settings
    log_level: str = Field(default="INFO")
    debug: bool = Field(default=False)
    environment: str = Field(default="production")

    # Claude Settings
    claude_model: str = Field(default="claude-3-5-sonnet-20241022")
    claude_max_tokens: int = Field(default=4096)
    claude_temperature: float = Field(default=0.7)
    claude_retry_attempts: int = Field(default=3)
    claude_timeout: int = Field(default=30)
    
    # Rate Limiting
    max_requests_per_user_per_day: int = Field(default=100)
    max_requests_per_user_per_hour: int = Field(default=10)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()