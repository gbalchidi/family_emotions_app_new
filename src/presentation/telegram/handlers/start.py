"""Start command handler."""

from aiogram import Router, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from src.application.services.user_service import UserService
from src.infrastructure.persistence.database import database
from src.infrastructure.persistence.user_repository import SqlAlchemyUserRepository
from src.presentation.telegram.keyboards import get_main_menu
from src.presentation.telegram.states import RegistrationStates

router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext) -> None:
    """Handle /start command."""
    user_id = message.from_user.id
    
    # Check if user exists
    async with database.session() as session:
        repo = SqlAlchemyUserRepository(session)
        service = UserService(repo)
        user = await service.get_user_by_telegram_id(user_id)
    
    if user:
        # User exists, show main menu
        await message.answer(
            f"С возвращением, {user.name}! 👋\n\n"
            "Я помогу вам лучше понять вашего ребенка. "
            "Выберите действие из меню:",
            reply_markup=get_main_menu()
        )
    else:
        # New user, start registration
        await message.answer(
            "Добро пожаловать в Family Emotions Light! 🌟\n\n"
            "Я помогу вам лучше понимать эмоции и поведение вашего ребенка.\n\n"
            "Давайте знакомиться! Как вас зовут?"
        )
        await state.set_state(RegistrationStates.waiting_for_parent_name)