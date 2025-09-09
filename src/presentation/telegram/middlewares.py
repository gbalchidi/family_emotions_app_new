"""Telegram bot middlewares."""

import time
from typing import Any, Awaitable, Callable, Dict

import structlog
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

logger = structlog.get_logger()


class LoggingMiddleware(BaseMiddleware):
    """Middleware for logging requests."""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        """Process request with logging."""
        start_time = time.time()
        user_id = event.from_user.id if event.from_user else None
        username = event.from_user.username if event.from_user else None
        
        # Log incoming request
        if isinstance(event, Message):
            logger.info(
                "Incoming message",
                user_id=user_id,
                username=username,
                text=event.text[:100] if event.text else None
            )
        elif isinstance(event, CallbackQuery):
            logger.info(
                "Incoming callback",
                user_id=user_id,
                username=username,
                data=event.data
            )
        
        try:
            result = await handler(event, data)
            elapsed = time.time() - start_time
            
            logger.info(
                "Request processed",
                user_id=user_id,
                elapsed=f"{elapsed:.3f}s"
            )
            
            return result
            
        except Exception as e:
            elapsed = time.time() - start_time
            
            logger.error(
                "Request failed",
                user_id=user_id,
                elapsed=f"{elapsed:.3f}s",
                error=str(e),
                exc_info=True
            )
            raise


class ErrorHandlerMiddleware(BaseMiddleware):
    """Middleware for handling errors."""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        """Process request with error handling."""
        try:
            return await handler(event, data)
        except Exception as e:
            error_message = (
                "😔 Произошла ошибка при обработке вашего запроса.\n"
                "Попробуйте еще раз или обратитесь в поддержку."
            )
            
            if isinstance(event, Message):
                await event.answer(error_message)
            elif isinstance(event, CallbackQuery):
                await event.message.answer(error_message)
                await event.answer()
            
            # Re-raise for logging middleware
            raise


def setup_middlewares(dp) -> None:
    """Setup all middlewares."""
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    dp.message.middleware(ErrorHandlerMiddleware())
    dp.callback_query.middleware(ErrorHandlerMiddleware())