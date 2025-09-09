"""Main application entry point."""

import asyncio
import logging
import sys
from pathlib import Path

import structlog
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.infrastructure.config.settings import settings
from src.infrastructure.persistence.database import database
from src.presentation.telegram.bot import setup_bot
from src.presentation.telegram.middlewares import setup_middlewares


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer() if settings.debug else structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Get logger
logger = structlog.get_logger()


async def main() -> None:
    """Main application function."""
    logger.info(
        "Starting Family Emotions Light Bot",
        environment=settings.env,
        debug=settings.debug
    )
    
    # Initialize Redis
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    storage = RedisStorage(redis=redis)
    
    # Initialize bot and dispatcher
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=storage)
    
    # Setup middlewares
    setup_middlewares(dp)
    
    # Setup bot handlers
    await setup_bot(dp)
    
    try:
        # Start polling
        logger.info("Bot started polling")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error("Bot crashed", error=str(e), exc_info=True)
        raise
    
    finally:
        # Cleanup
        await bot.session.close()
        await redis.close()
        await database.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    # Setup basic logging
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Run bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error("Fatal error", error=str(e), exc_info=True)
        sys.exit(1)