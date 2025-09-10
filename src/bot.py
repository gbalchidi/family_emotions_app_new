"""Main bot module."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

# Add src to path
sys.path.append(str(Path(__file__).parent))

from config import settings
from infrastructure.database.session import db_manager
from presentation.handlers import analysis, start, translator, menu

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
        structlog.dev.ConsoleRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


async def on_startup(bot: Bot) -> None:
    """Actions to perform on bot startup."""
    logger.info("Bot starting...")
    
    # Create database tables
    await db_manager.create_all()
    logger.info("Database initialized")
    
    # Get bot info
    bot_info = await bot.get_me()
    logger.info(
        "Bot started",
        username=bot_info.username,
        id=bot_info.id,
    )


async def on_shutdown(bot: Bot) -> None:
    """Actions to perform on bot shutdown."""
    logger.info("Bot shutting down...")
    
    # Close database connections
    await db_manager.close()
    logger.info("Database connections closed")
    
    logger.info("Bot stopped")


async def main() -> None:
    """Main bot function."""
    # Initialize Redis storage for FSM
    redis = Redis.from_url(
        str(settings.redis_url),
        decode_responses=True,
    )
    storage = RedisStorage(redis=redis)
    
    # Initialize bot and dispatcher
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    dp = Dispatcher(storage=storage)
    
    # Register startup and shutdown handlers
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Register routers
    dp.include_router(start.router)
    dp.include_router(translator.router)
    dp.include_router(menu.router)
    dp.include_router(analysis.router)
    
    # Start polling
    try:
        logger.info("Starting bot polling...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.exception("Error in bot polling")
        raise
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.exception("Fatal error")
        sys.exit(1)