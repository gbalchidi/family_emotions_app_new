"""Registration flow handlers."""

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from src.application.commands.user_commands import RegisterUserCommand
from src.application.services.user_service import UserService
from src.infrastructure.persistence.database import database
from src.infrastructure.persistence.user_repository import SqlAlchemyUserRepository
from src.presentation.telegram.keyboards import get_gender_keyboard, get_main_menu
from src.presentation.telegram.states import RegistrationStates

router = Router()


@router.message(RegistrationStates.waiting_for_parent_name)
async def process_parent_name(message: types.Message, state: FSMContext) -> None:
    """Process parent name input."""
    parent_name = message.text.strip()
    
    if len(parent_name) < 2:
        await message.answer("Имя слишком короткое. Пожалуйста, введите ваше имя:")
        return
    
    await state.update_data(parent_name=parent_name)
    await message.answer(
        f"Приятно познакомиться, {parent_name}! 😊\n\n"
        "Теперь расскажите о вашем ребенке.\n"
        "Как зовут вашего ребенка?"
    )
    await state.set_state(RegistrationStates.waiting_for_child_name)


@router.message(RegistrationStates.waiting_for_child_name)
async def process_child_name(message: types.Message, state: FSMContext) -> None:
    """Process child name input."""
    child_name = message.text.strip()
    
    if len(child_name) < 2:
        await message.answer("Имя слишком короткое. Пожалуйста, введите имя ребенка:")
        return
    
    await state.update_data(child_name=child_name)
    await message.answer(
        f"Отлично! Сколько лет {child_name}?\n"
        "Введите возраст числом (от 1 до 18):"
    )
    await state.set_state(RegistrationStates.waiting_for_child_age)


@router.message(RegistrationStates.waiting_for_child_age)
async def process_child_age(message: types.Message, state: FSMContext) -> None:
    """Process child age input."""
    try:
        age = int(message.text.strip())
        if not 1 <= age <= 18:
            raise ValueError()
    except ValueError:
        await message.answer(
            "Пожалуйста, введите корректный возраст (число от 1 до 18):"
        )
        return
    
    await state.update_data(child_age=age)
    await message.answer(
        "Укажите пол ребенка:",
        reply_markup=get_gender_keyboard()
    )
    await state.set_state(RegistrationStates.waiting_for_child_gender)


@router.callback_query(
    RegistrationStates.waiting_for_child_gender,
    F.data.startswith("gender:")
)
async def process_child_gender(
    callback: types.CallbackQuery,
    state: FSMContext
) -> None:
    """Process child gender selection."""
    gender = callback.data.split(":")[1]
    data = await state.get_data()
    
    # Register user
    async with database.session() as session:
        repo = SqlAlchemyUserRepository(session)
        service = UserService(repo)
        
        command = RegisterUserCommand(
            telegram_id=callback.from_user.id,
            telegram_username=callback.from_user.username or "",
            parent_name=data["parent_name"],
            child_name=data["child_name"],
            child_age=data["child_age"],
            child_gender=gender
        )
        
        try:
            user = await service.register_user(command)
            
            await callback.message.edit_text(
                "✅ Регистрация успешно завершена!"
            )
            
            await callback.message.answer(
                f"Отлично, {data['parent_name']}! 🎉\n\n"
                f"Я запомнил информацию о {data['child_name']}.\n\n"
                "Теперь вы можете:\n"
                "• Анализировать ситуации с ребенком\n"
                "• Получать рекомендации от ИИ\n"
                "• Вести историю анализов\n\n"
                "Выберите действие из меню:",
                reply_markup=get_main_menu()
            )
            
            await state.clear()
            
        except Exception as e:
            await callback.message.answer(
                f"Произошла ошибка при регистрации: {str(e)}\n"
                "Попробуйте еще раз /start"
            )
            await state.clear()
    
    await callback.answer()