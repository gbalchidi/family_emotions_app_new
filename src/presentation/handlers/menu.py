"""Menu handlers."""
from __future__ import annotations

import structlog
from aiogram import F, Router
from aiogram.types import Message

logger = structlog.get_logger()
router = Router(name="menu")


@router.message(F.text == "✅ Начать ежедневный чек-ин")
async def start_checkin(message: Message) -> None:
    """Handle daily check-in start."""
    await message.answer(
        "🔔 Время семейного чек-ина!\n\n"
        "Эта функция будет доступна в следующей версии бота.\n"
        "Следите за обновлениями!"
    )


@router.message(F.text == "📊 Мой профиль")
async def show_profile(message: Message) -> None:
    """Show user profile."""
    await message.answer(
        "👨‍👩‍👧‍👦 ПРОФИЛЬ СЕМЬИ\n\n"
        "Эта функция будет доступна в следующей версии бота.\n"
        "Следите за обновлениями!"
    )


@router.message(F.text == "⚙️ Настройки")
async def show_settings(message: Message) -> None:
    """Show settings menu."""
    await message.answer(
        "⚙️ НАСТРОЙКИ\n\n"
        "Доступные команды:\n"
        "/reset - Сбросить все данные и начать заново\n"
        "/start - Вернуться в главное меню\n\n"
        "Другие настройки будут доступны в следующей версии."
    )