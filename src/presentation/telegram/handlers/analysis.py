"""Analysis flow handlers."""

from uuid import UUID

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from src.application.commands.analysis_commands import RequestAnalysisCommand
from src.application.services.analysis_service import AnalysisService
from src.application.services.user_service import UserService
from src.infrastructure.cache.rate_limiter import RedisRateLimiter
from src.infrastructure.external_services.claude_analyzer import ClaudeAnalyzer
from src.infrastructure.persistence.analysis_repository import SqlAlchemyAnalysisRepository
from src.infrastructure.persistence.database import database
from src.infrastructure.persistence.user_repository import SqlAlchemyUserRepository
from src.infrastructure.security.validators import InputValidator
from src.presentation.telegram.keyboards import get_child_selection_keyboard
from src.presentation.telegram.states import AnalysisStates

router = Router()


@router.message(F.text == "💭 Проанализировать ситуацию")
async def start_analysis(message: types.Message, state: FSMContext) -> None:
    """Start analysis flow."""
    user_id = message.from_user.id
    
    # Get user and children
    async with database.session() as session:
        repo = SqlAlchemyUserRepository(session)
        service = UserService(repo)
        user = await service.get_user_by_telegram_id(user_id)
    
    if not user:
        await message.answer(
            "Вы не зарегистрированы. Используйте команду /start для регистрации."
        )
        return
    
    if not user.children:
        await message.answer(
            "У вас нет добавленных детей. Сначала добавьте ребенка через меню."
        )
        return
    
    if len(user.children) == 1:
        # Only one child, skip selection
        child = user.children[0]
        await state.update_data(
            user_id=str(user.id),
            child_id=str(child.id),
            child_age=child.age,
            child_gender=child.gender
        )
        await message.answer(
            f"Анализ для: {child.name} ({child.age} лет)\n\n"
            "Опишите ситуацию, которую хотите проанализировать.\n"
            "Что сказал или сделал ваш ребенок?\n\n"
            "Постарайтесь описать как можно подробнее:"
        )
        await state.set_state(AnalysisStates.waiting_for_situation)
    else:
        # Multiple children, show selection
        await message.answer(
            "Выберите ребенка для анализа:",
            reply_markup=get_child_selection_keyboard(user.children)
        )
        await state.update_data(user_id=str(user.id))
        await state.set_state(AnalysisStates.waiting_for_child_selection)


@router.callback_query(
    AnalysisStates.waiting_for_child_selection,
    F.data.startswith("child:")
)
async def process_child_selection(
    callback: types.CallbackQuery,
    state: FSMContext
) -> None:
    """Process child selection for analysis."""
    child_id = UUID(callback.data.split(":")[1])
    data = await state.get_data()
    user_id = UUID(data["user_id"])
    
    # Get child info
    async with database.session() as session:
        repo = SqlAlchemyUserRepository(session)
        service = UserService(repo)
        user = await service.get_user_by_telegram_id(callback.from_user.id)
    
    child = next((c for c in user.children if c.id == child_id), None)
    if not child:
        await callback.message.answer("Ребенок не найден.")
        await state.clear()
        return
    
    await state.update_data(
        child_id=str(child_id),
        child_age=child.age,
        child_gender=child.gender
    )
    
    await callback.message.edit_text(
        f"Анализ для: {child.name} ({child.age} лет)"
    )
    
    await callback.message.answer(
        "Опишите ситуацию, которую хотите проанализировать.\n"
        "Что сказал или сделал ваш ребенок?\n\n"
        "Постарайтесь описать как можно подробнее:"
    )
    await state.set_state(AnalysisStates.waiting_for_situation)
    await callback.answer()


@router.message(AnalysisStates.waiting_for_situation)
async def process_situation(message: types.Message, state: FSMContext) -> None:
    """Process situation description and perform analysis."""
    # Sanitize input
    situation = InputValidator.sanitize_text(message.text.strip(), max_length=2000)
    
    if len(situation) < 10:
        await message.answer(
            "Описание слишком короткое. "
            "Пожалуйста, опишите ситуацию более подробно (минимум 10 символов):"
        )
        return
    
    # Check for potential injection attacks
    if InputValidator.check_sql_injection(situation):
        await message.answer("Обнаружен недопустимый контент. Попробуйте еще раз.")
        return
    
    data = await state.get_data()
    
    # Show processing message
    processing_msg = await message.answer(
        "🔄 Анализирую ситуацию...\n"
        "Это может занять несколько секунд..."
    )
    
    try:
        # Perform analysis
        async with database.session() as session:
            analysis_repo = SqlAlchemyAnalysisRepository(session)
            ai_analyzer = ClaudeAnalyzer()
            rate_limiter = RedisRateLimiter()
            
            service = AnalysisService(
                analysis_repository=analysis_repo,
                ai_analyzer=ai_analyzer,
                rate_limiter=rate_limiter
            )
            
            command = RequestAnalysisCommand(
                user_id=UUID(data["user_id"]),
                child_id=UUID(data["child_id"]),
                situation_description=situation,
                child_age=data["child_age"],
                child_gender=data["child_gender"]
            )
            
            analysis = await service.request_analysis(command)
        
        # Delete processing message
        await processing_msg.delete()
        
        # Format and send results
        if analysis.recommendation:
            result_text = (
                "📊 **АНАЛИЗ СИТУАЦИИ**\n\n"
                f"🔍 **Скрытый смысл:**\n{analysis.recommendation.hidden_meaning}\n\n"
                f"⚡ **Что делать сейчас:**\n{analysis.recommendation.immediate_actions}\n\n"
                f"📈 **Долгосрочные рекомендации:**\n{analysis.recommendation.long_term_recommendations}\n\n"
                f"⛔ **Чего НЕ делать:**\n{analysis.recommendation.what_not_to_do}\n\n"
                f"_Уверенность анализа: {analysis.recommendation.confidence_score:.0%}_"
            )
            
            await message.answer(
                result_text,
                parse_mode="Markdown"
            )
        else:
            await message.answer(
                "Анализ выполнен, но результаты не получены. "
                "Попробуйте еще раз позже."
            )
        
    except ValueError as e:
        await processing_msg.delete()
        await message.answer(
            f"⚠️ {str(e)}\n\n"
            "Вы достигли лимита анализов. Попробуйте позже."
        )
    except Exception as e:
        await processing_msg.delete()
        await message.answer(
            "❌ Произошла ошибка при анализе.\n"
            "Попробуйте еще раз или обратитесь в поддержку."
        )
    
    await state.clear()