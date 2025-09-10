"""Emotion translator handlers."""
from __future__ import annotations

import structlog
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from application.commands import GetUserCommand
from application.services.user_service import UserService
from infrastructure.claude.adapter import ClaudeAdapter
from infrastructure.database.session import get_session
from infrastructure.database.repositories import SQLAlchemyUserRepository
from presentation.keyboards import cancel_keyboard
from presentation.states import TranslatorStates

logger = structlog.get_logger()
router = Router(name="translator")


@router.message(F.text == "💬 Перевести фразу ребенка")
@router.message(Command("translate"))
async def start_translation(message: Message, state: FSMContext) -> None:
    """Start emotion translation flow."""
    if not message.from_user:
        return
    
    async for session in get_session():
        try:
            user_repo = SQLAlchemyUserRepository(session)
            user_service = UserService(user_repo)
            
            # Check if user exists and completed onboarding
            get_user_cmd = GetUserCommand(telegram_id=message.from_user.id)
            user = await user_service.get_user(get_user_cmd)
            
            if not user or not user.onboarding_completed:
                await message.answer(
                    "Пожалуйста, сначала пройдите регистрацию.\n"
                    "Отправьте /start для начала."
                )
                return
            
            await state.update_data(user_id=str(user.id))
            
            await message.answer(
                "Что сказал ваш ребенок?\n\n"
                "Отправьте мне текстовое сообщение с его словами.\n\n"
                "Примеры фраз:\n"
                '"Отстань от меня!"\n'
                '"Ты ничего не понимаешь"\n'
                '"Все нормально" (когда явно не нормально)',
                reply_markup=cancel_keyboard(),
            )
            await state.set_state(TranslatorStates.waiting_for_phrase)
            
        except Exception as e:
            logger.exception("Error starting translation")
            await message.answer("Произошла ошибка. Попробуйте позже.")


@router.message(TranslatorStates.waiting_for_phrase)
async def process_phrase(message: Message, state: FSMContext) -> None:
    """Process child's phrase for translation."""
    if not message.text:
        await message.answer("Пожалуйста, отправьте текстовое сообщение.")
        return
    
    phrase = message.text.strip()
    
    # Show typing while processing
    await message.bot.send_chat_action(message.chat.id, "typing")
    
    await message.answer("🔍 Анализирую фразу...")
    
    try:
        # Use Claude to analyze the phrase
        claude = ClaudeAdapter()
        
        prompt = f"""Ты - эксперт по детской психологии и семейным отношениям. 
        
Родитель прислал фразу, которую сказал ребенок: "{phrase}"

Проанализируй эту фразу и ответь в следующем формате:

💭 "{phrase}"

📝 ЧТО НА САМОМ ДЕЛЕ ЧУВСТВУЕТ РЕБЕНОК:

🎯 Скрытый смысл:
[Объясни, что на самом деле чувствует и хочет сказать ребенок]

😔 Эмоции:
[Перечисли основные эмоции с процентами]

💡 РЕКОМЕНДАЦИИ:

Вместо: [Типичная неэффективная реакция родителя]
Скажите: [Эффективная фраза для ответа]

✅ Что делать сейчас:
1. [Конкретное действие 1]
2. [Конкретное действие 2]
3. [Конкретное действие 3]"""

        analysis = await claude.analyze_situation(
            situation_text=phrase,
            context=prompt,
            child_age=10,  # Default age
            child_name="ребенок"
        )
        
        # Send analysis result
        await message.answer(
            analysis.analysis_text,
            parse_mode="HTML"
        )
        
        # Add feedback keyboard
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="👍 Полезно", callback_data="feedback_useful"),
                    InlineKeyboardButton(text="👎 Не помогло", callback_data="feedback_not_useful"),
                ],
                [
                    InlineKeyboardButton(text="💬 Перевести еще", callback_data="translate_more"),
                ],
            ]
        )
        
        await message.answer(
            "Была ли эта информация полезной?",
            reply_markup=keyboard
        )
        
        await state.clear()
        
    except Exception as e:
        logger.exception("Error analyzing phrase", phrase=phrase)
        await message.answer(
            "Не удалось проанализировать фразу. Попробуйте еще раз.\n"
            "Если ошибка повторяется, обратитесь в поддержку."
        )
        await state.clear()


@router.callback_query(F.data == "translate_more")
async def translate_more(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle request to translate another phrase."""
    await callback.answer()
    await callback.message.answer(
        "Что еще сказал ваш ребенок?\n\n"
        "Отправьте мне текстовое сообщение с его словами.",
        reply_markup=cancel_keyboard(),
    )
    await state.set_state(TranslatorStates.waiting_for_phrase)


@router.callback_query(F.data == "cancel")
@router.message(Command("cancel"))
async def cancel_handler(update: Message | CallbackQuery, state: FSMContext) -> None:
    """Cancel current operation."""
    await state.clear()
    
    if isinstance(update, CallbackQuery):
        await update.answer()
        await update.message.answer("Действие отменено.")
    else:
        await update.answer("Действие отменено.")