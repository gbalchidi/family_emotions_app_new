"""Bot keyboards."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from application.dto import ChildDTO


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Create main menu keyboard according to documentation."""
    buttons = [
        [KeyboardButton(text="💬 Перевести фразу ребенка")],
        [KeyboardButton(text="✅ Начать ежедневный чек-ин")],
        [KeyboardButton(text="📊 Мой профиль"), KeyboardButton(text="⚙️ Настройки")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def gender_keyboard() -> InlineKeyboardMarkup:
    """Create gender selection keyboard."""
    buttons = [
        [
            InlineKeyboardButton(text="👦 Мальчик", callback_data="gender_male"),
            InlineKeyboardButton(text="👧 Девочка", callback_data="gender_female"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def yes_no_keyboard() -> InlineKeyboardMarkup:
    """Create yes/no keyboard."""
    buttons = [
        [
            InlineKeyboardButton(text="✅ Да", callback_data="yes"),
            InlineKeyboardButton(text="❌ Нет", callback_data="no"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def child_selection_keyboard(children: list[ChildDTO]) -> InlineKeyboardMarkup:
    """Create child selection keyboard."""
    buttons = []
    for child in children:
        age_text = f"{child.age_years} лет"
        if child.age_months:
            age_text = f"{child.age_years} лет {child.age_months} мес"
        
        button_text = f"{child.name} ({age_text})"
        buttons.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"select_child_{child.id}"
            )
        ])
    
    buttons.append([InlineKeyboardButton(text="↩️ Назад", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def skip_context_keyboard() -> InlineKeyboardMarkup:
    """Create skip context keyboard."""
    buttons = [
        [InlineKeyboardButton(text="⏭ Пропустить", callback_data="skip_context")],
        [InlineKeyboardButton(text="↩️ Отмена", callback_data="cancel")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    """Create back to menu keyboard."""
    buttons = [
        [InlineKeyboardButton(text="↩️ В главное меню", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cancel_keyboard() -> InlineKeyboardMarkup:
    """Create cancel keyboard."""
    buttons = [
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)