"""Telegram bot keyboards."""

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def get_main_menu() -> ReplyKeyboardMarkup:
    """Get main menu keyboard."""
    keyboard = [
        [KeyboardButton(text="💭 Проанализировать ситуацию")],
        [KeyboardButton(text="👨‍👩‍👧‍👦 Мои дети")],
        [KeyboardButton(text="📊 История анализов")],
        [KeyboardButton(text="ℹ️ Помощь")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_gender_keyboard() -> InlineKeyboardMarkup:
    """Get gender selection keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(text="👦 Мальчик", callback_data="gender:male"),
            InlineKeyboardButton(text="👧 Девочка", callback_data="gender:female")
        ],
        [InlineKeyboardButton(text="🤷 Не указывать", callback_data="gender:not_specified")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_child_selection_keyboard(children: list) -> InlineKeyboardMarkup:
    """Get child selection keyboard."""
    keyboard = []
    for child in children:
        emoji = "👦" if child.gender == "male" else "👧" if child.gender == "female" else "👤"
        keyboard.append([
            InlineKeyboardButton(
                text=f"{emoji} {child.name} ({child.age} лет)",
                callback_data=f"child:{child.id}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(text="➕ Добавить ребенка", callback_data="add_child")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Get confirmation keyboard."""
    keyboard = [
        [
            InlineKeyboardButton(text="✅ Да", callback_data="confirm:yes"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="confirm:no")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_back_keyboard() -> InlineKeyboardMarkup:
    """Get back button keyboard."""
    keyboard = [
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)