"""Main bot setup."""

from aiogram import Dispatcher

from src.presentation.telegram.handlers import (
    analysis,
    registration,
    start,
)


async def setup_bot(dp: Dispatcher) -> None:
    """Setup bot handlers and routers."""
    # Include routers
    dp.include_router(start.router)
    dp.include_router(registration.router)
    dp.include_router(analysis.router)