"""Analysis handlers."""
from __future__ import annotations

from uuid import UUID

import structlog
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from application.commands import AnalyzeSituationCommand, GetUserCommand
from application.services.analysis_service import AnalysisService
from application.services.user_service import UserService
from domain.exceptions import DomainException
from domain.value_objects import EmotionalTone
from infrastructure.claude.adapter import ClaudeAdapter
from infrastructure.database.session import get_session
from infrastructure.database.repositories import (
    SQLAlchemySituationRepository,
    SQLAlchemyUserRepository,
)
from presentation.keyboards import (
    back_to_menu_keyboard,
    child_selection_keyboard,
    main_menu_keyboard,
    skip_context_keyboard,
)
from presentation.states import AnalysisStates

logger = structlog.get_logger()
router = Router(name="analysis")


@router.callback_query(F.data == "analyze_situation")
async def start_analysis(callback: CallbackQuery, state: FSMContext) -> None:
    """Start situation analysis."""
    if not callback.from_user:
        return

    async for session in get_session():
        try:
            user_repo = SQLAlchemyUserRepository(session)
            user_service = UserService(user_repo)

            # Get user
            get_user_cmd = GetUserCommand(telegram_id=callback.from_user.id)
            user = await user_service.get_user(get_user_cmd)

            if not user:
                await callback.answer("Пользователь не найден", show_alert=True)
                return

            if not user.onboarding_completed:
                await callback.answer(
                    "Сначала завершите регистрацию", show_alert=True
                )
                return

            if not user.children:
                await callback.answer(
                    "Сначала добавьте информацию о ребенке", show_alert=True
                )
                return

            await state.update_data(user_id=str(user.id))

            if len(user.children) == 1:
                # Only one child, skip selection
                child = user.children[0]
                await state.update_data(child_id=str(child.id))
                await callback.message.edit_text(
                    f"Анализ ситуации для {child.name}\n\n"
                    "Опишите ситуацию, которую хотите проанализировать.\n\n"
                    "Например:\n"
                    "• Ребенок устроил истерику в магазине\n"
                    "• Не хочет делать уроки\n"
                    "• Дерется с другими детьми\n\n"
                    "Чем подробнее опишете, тем точнее будет анализ.",
                    reply_markup=None,
                )
                await state.set_state(AnalysisStates.waiting_for_situation)
            else:
                # Multiple children, show selection
                await callback.message.edit_text(
                    "Выберите ребенка для анализа:",
                    reply_markup=child_selection_keyboard(user.children),
                )
                await state.set_state(AnalysisStates.waiting_for_child_selection)

        except Exception as e:
            logger.exception("Error starting analysis")
            await callback.answer("Произошла ошибка", show_alert=True)


@router.callback_query(
    AnalysisStates.waiting_for_child_selection, F.data.startswith("select_child_")
)
async def select_child(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle child selection."""
    if not callback.data:
        return

    child_id = callback.data.replace("select_child_", "")
    await state.update_data(child_id=child_id)

    data = await state.get_data()
    
    async for session in get_session():
        try:
            user_repo = SQLAlchemyUserRepository(session)
            user_service = UserService(user_repo)

            user = await user_service.get_user_by_id(UUID(data["user_id"]))
            if not user:
                await callback.answer("Пользователь не найден", show_alert=True)
                return

            child = next((c for c in user.children if str(c.id) == child_id), None)
            if not child:
                await callback.answer("Ребенок не найден", show_alert=True)
                return

            await callback.message.edit_text(
                f"Анализ ситуации для {child.name}\n\n"
                "Опишите ситуацию, которую хотите проанализировать.\n\n"
                "Например:\n"
                "• Ребенок устроил истерику в магазине\n"
                "• Не хочет делать уроки\n"
                "• Дерется с другими детьми\n\n"
                "Чем подробнее опишете, тем точнее будет анализ.",
            )
            await state.set_state(AnalysisStates.waiting_for_situation)

        except Exception as e:
            logger.exception("Error selecting child")
            await callback.answer("Произошла ошибка", show_alert=True)


@router.message(AnalysisStates.waiting_for_situation)
async def process_situation(message: Message, state: FSMContext) -> None:
    """Process situation description."""
    if not message.text:
        await message.answer("Пожалуйста, опишите ситуацию текстом.")
        return

    if len(message.text) < 10:
        await message.answer(
            "Слишком короткое описание. Пожалуйста, опишите ситуацию подробнее."
        )
        return

    await state.update_data(situation=message.text)
    await message.answer(
        "Хотите добавить дополнительный контекст?\n\n"
        "Например:\n"
        "• Это происходит регулярно или впервые?\n"
        "• Были ли какие-то изменения в жизни ребенка?\n"
        "• Как вы обычно реагируете на такое поведение?",
        reply_markup=skip_context_keyboard(),
    )
    await state.set_state(AnalysisStates.waiting_for_context)


@router.message(AnalysisStates.waiting_for_context)
async def process_context(message: Message, state: FSMContext) -> None:
    """Process additional context."""
    if not message.text:
        await message.answer("Пожалуйста, введите контекст текстом или пропустите этот шаг.")
        return

    await state.update_data(context=message.text)
    await analyze_situation(message, state)


@router.callback_query(AnalysisStates.waiting_for_context, F.data == "skip_context")
async def skip_context(callback: CallbackQuery, state: FSMContext) -> None:
    """Skip adding context."""
    await callback.answer()
    await analyze_situation(callback.message, state)


async def analyze_situation(message: Message, state: FSMContext) -> None:
    """Analyze the situation."""
    data = await state.get_data()
    
    # Show loading message
    loading_msg = await message.answer("🔍 Анализирую ситуацию...")
    
    async for session in get_session():
        try:
            user_repo = SQLAlchemyUserRepository(session)
            situation_repo = SQLAlchemySituationRepository(session)
            claude_adapter = ClaudeAdapter()
            
            analysis_service = AnalysisService(
                user_repo, situation_repo, claude_adapter
            )

            # Analyze situation
            analyze_cmd = AnalyzeSituationCommand(
                user_id=UUID(data["user_id"]),
                child_id=UUID(data["child_id"]),
                description=data["situation"],
                context=data.get("context"),
            )
            
            situation = await analysis_service.analyze_situation(analyze_cmd)
            
            # Delete loading message
            await loading_msg.delete()
            
            # Format and send analysis result
            if situation.analysis_result:
                result = situation.analysis_result
                
                # Determine emoji based on emotional tone
                tone_emoji = {
                    EmotionalTone.POSITIVE: "✅",
                    EmotionalTone.NEUTRAL: "💭",
                    EmotionalTone.CONCERNING: "⚠️",
                    EmotionalTone.URGENT: "🚨",
                }.get(result.emotional_tone, "💭")
                
                response = f"{tone_emoji} **Анализ ситуации для {situation.child_name}**\n\n"
                
                response += f"**🔍 Скрытый смысл:**\n{result.hidden_meaning}\n\n"
                
                response += "**✅ Что делать сейчас:**\n"
                for i, action in enumerate(result.immediate_actions, 1):
                    response += f"{i}. {action}\n"
                response += "\n"
                
                response += "**📚 Долгосрочные рекомендации:**\n"
                for i, rec in enumerate(result.long_term_recommendations, 1):
                    response += f"{i}. {rec}\n"
                response += "\n"
                
                response += "**❌ Чего НЕ делать:**\n"
                for i, dont in enumerate(result.what_not_to_do, 1):
                    response += f"{i}. {dont}\n"
                
                await message.answer(
                    response,
                    parse_mode="Markdown",
                    reply_markup=main_menu_keyboard(),
                )
            else:
                await message.answer(
                    "Не удалось проанализировать ситуацию. Попробуйте еще раз.",
                    reply_markup=main_menu_keyboard(),
                )
            
            await state.clear()

        except DomainException as e:
            await loading_msg.delete()
            logger.error("Domain error analyzing situation", error=str(e))
            await message.answer(
                f"Ошибка: {str(e)}",
                reply_markup=main_menu_keyboard(),
            )
            await state.clear()
        except Exception as e:
            await loading_msg.delete()
            logger.exception("Unexpected error analyzing situation")
            await message.answer(
                "Произошла ошибка при анализе. Пожалуйста, попробуйте еще раз.",
                reply_markup=main_menu_keyboard(),
            )
            await state.clear()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Go back to main menu."""
    await callback.answer()
    await callback.message.edit_text(
        "Главное меню. Выберите действие:",
        reply_markup=main_menu_keyboard(),
    )
    await state.clear()


@router.callback_query(F.data == "cancel")
async def cancel_analysis(callback: CallbackQuery, state: FSMContext) -> None:
    """Cancel current operation."""
    await callback.answer()
    await callback.message.edit_text(
        "Операция отменена. Выберите действие:",
        reply_markup=main_menu_keyboard(),
    )
    await state.clear()