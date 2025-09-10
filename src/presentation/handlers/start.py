"""Start and onboarding handlers."""
from __future__ import annotations

from datetime import datetime

import structlog
from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from application.commands import (
    AddChildCommand,
    CompleteOnboardingCommand,
    GetUserCommand,
    RegisterUserCommand,
)
from application.services.user_service import UserService
from domain.exceptions import DomainException
from domain.value_objects import Gender
from infrastructure.database.session import get_session
from infrastructure.database.repositories import SQLAlchemyUserRepository
from presentation.keyboards import (
    gender_keyboard,
    main_menu_keyboard,
    yes_no_keyboard,
)
from presentation.states import OnboardingStates

logger = structlog.get_logger()
router = Router(name="start")


@router.message(Command("reset"))
async def reset_handler(message: Message, state: FSMContext) -> None:
    """Handle /reset command - clear user data and start fresh."""
    if not message.from_user:
        return
    
    async for session in get_session():
        try:
            user_repo = SQLAlchemyUserRepository(session)
            
            # Delete user if exists
            user = await user_repo.get_by_telegram_id(message.from_user.id)
            if user:
                await user_repo.delete(user.id)
                # Session will be committed automatically by context manager
            
            await state.clear()
            await message.answer(
                "✅ Данные удалены. Отправьте /start чтобы начать заново."
            )
        except Exception as e:
            logger.exception("Error resetting user")
            await message.answer("Произошла ошибка при сбросе данных.")


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    """Handle /start command."""
    if not message.from_user:
        return

    async for session in get_session():
        try:
            user_repo = SQLAlchemyUserRepository(session)
            user_service = UserService(user_repo)

            # Check if user exists
            get_user_cmd = GetUserCommand(telegram_id=message.from_user.id)
            user = await user_service.get_user(get_user_cmd)

            if user and user.onboarding_completed:
                # User exists and completed onboarding, show main menu
                await message.answer(
                    f"С возвращением, {user.first_name}! 👋\n\n"
                    "Чем могу помочь сегодня?",
                    reply_markup=main_menu_keyboard(),
                )
                await state.clear()
            elif user and not user.onboarding_completed:
                # User exists but didn't complete onboarding
                await state.update_data(user_id=str(user.id))
                await message.answer(
                    f"Привет, {user.first_name}! 👋\n\n"
                    "Давайте завершим настройку. Для начала добавим информацию о вашем ребенке.\n\n"
                    "Как зовут вашего ребенка?",
                )
                await state.set_state(OnboardingStates.waiting_for_child_name)
            else:
                # Register new user
                register_cmd = RegisterUserCommand(
                    telegram_id=message.from_user.id,
                    username=message.from_user.username,
                    first_name=message.from_user.first_name,
                    last_name=message.from_user.last_name,
                    language_code=message.from_user.language_code,
                )
                user = await user_service.register_user(register_cmd)

                # Start onboarding
                await state.update_data(user_id=str(user.id))
                await message.answer(
                    f"Привет, {user.first_name}! 👋\n\n"
                    "Я помогу вам лучше понимать эмоции и поведение вашего ребенка.\n\n"
                    "Для начала давайте добавим информацию о вашем ребенке.\n\n"
                    "Как зовут вашего ребенка?",
                )
                await state.set_state(OnboardingStates.waiting_for_child_name)

        except DomainException as e:
            logger.error("Domain error in start handler", error=str(e))
            await message.answer(
                "Произошла ошибка. Пожалуйста, попробуйте позже или обратитесь в поддержку."
            )
        except Exception as e:
            logger.exception("Unexpected error in start handler")
            await message.answer(
                "Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже."
            )


@router.message(OnboardingStates.waiting_for_child_name)
async def process_child_name(message: Message, state: FSMContext) -> None:
    """Process child name input."""
    if not message.text:
        await message.answer("Пожалуйста, введите имя ребенка текстом.")
        return

    await state.update_data(child_name=message.text.strip())
    
    # Create keyboard with age options
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"{age} лет", callback_data=f"age_{age}")
                for age in range(2, 7)
            ],
            [
                InlineKeyboardButton(text=f"{age} лет", callback_data=f"age_{age}")
                for age in range(7, 12)
            ],
            [
                InlineKeyboardButton(text=f"{age} лет", callback_data=f"age_{age}")
                for age in range(12, 17)
            ],
            [
                InlineKeyboardButton(text=f"{age} лет", callback_data=f"age_{age}")
                for age in range(17, 19)
            ],
        ]
    )
    
    await message.answer(
        f"Выберите возраст ребенка {message.text.strip()}:",
        reply_markup=keyboard,
    )
    await state.set_state(OnboardingStates.waiting_for_child_age)


@router.callback_query(OnboardingStates.waiting_for_child_age, F.data.startswith("age_"))
async def process_child_age(callback: CallbackQuery, state: FSMContext) -> None:
    """Process child age selection."""
    if not callback.data:
        return
    
    # Extract age from callback data
    age = int(callback.data.split("_")[1])
    
    # Calculate birth date from age
    from datetime import date
    today = date.today()
    birth_year = today.year - age
    birth_date = date(birth_year, today.month, today.day)
    
    await state.update_data(child_birth_date=birth_date.isoformat(), child_age=age)
    
    data = await state.get_data()
    
    await callback.answer()
    await callback.message.edit_text(
        f"Укажите пол ребенка {data['child_name']}:",
        reply_markup=gender_keyboard(),
    )
    await state.set_state(OnboardingStates.waiting_for_child_gender)


@router.callback_query(OnboardingStates.waiting_for_child_gender, F.data.startswith("gender_"))
async def process_child_gender(callback: CallbackQuery, state: FSMContext) -> None:
    """Process child gender selection."""
    if not callback.data:
        return

    gender = Gender.MALE if callback.data == "gender_male" else Gender.FEMALE
    
    data = await state.get_data()
    
    async for session in get_session():
        try:
            user_repo = SQLAlchemyUserRepository(session)
            user_service = UserService(user_repo)

            # Add child
            add_child_cmd = AddChildCommand(
                user_id=data["user_id"],
                name=data["child_name"],
                birth_date=datetime.fromisoformat(data["child_birth_date"]).date(),
                gender=gender,
            )
            child = await user_service.add_child(add_child_cmd)

            await callback.answer()
            
            # Get age from state data
            age = data.get("child_age", 0)
            
            await callback.message.edit_text(
                f"✅ {child.name} добавлен(а)!\n\n"
                f"Возраст: {age} лет\n\n"
                "Хотите добавить еще одного ребенка?",
                reply_markup=yes_no_keyboard(),
            )
            await state.set_state(OnboardingStates.waiting_for_another_child)

        except DomainException as e:
            logger.error("Domain error adding child", error=str(e))
            await callback.answer("Ошибка при добавлении ребенка", show_alert=True)
        except Exception as e:
            logger.exception("Unexpected error adding child")
            await callback.answer("Произошла ошибка", show_alert=True)


@router.callback_query(OnboardingStates.waiting_for_another_child, F.data == "yes")
async def add_another_child(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle adding another child."""
    await callback.answer()
    await callback.message.edit_text("Как зовут вашего ребенка?")
    await state.set_state(OnboardingStates.waiting_for_child_name)


@router.callback_query(OnboardingStates.waiting_for_another_child, F.data == "no")
async def complete_onboarding(callback: CallbackQuery, state: FSMContext) -> None:
    """Complete onboarding process."""
    data = await state.get_data()
    
    async for session in get_session():
        try:
            user_repo = SQLAlchemyUserRepository(session)
            user_service = UserService(user_repo)

            # Complete onboarding
            complete_cmd = CompleteOnboardingCommand(user_id=data["user_id"])
            user = await user_service.complete_onboarding(complete_cmd)

            await callback.answer()
            await callback.message.edit_text(
                "🎉 Отлично! Регистрация завершена.\n\n"
                "Теперь вы можете:\n"
                "• Анализировать ситуации с вашим ребенком\n"
                "• Получать персонализированные рекомендации\n"
                "• Лучше понимать эмоции и поведение ребенка\n\n"
                "Выберите действие:",
                reply_markup=main_menu_keyboard(),
            )
            await state.clear()

        except DomainException as e:
            logger.error("Domain error completing onboarding", error=str(e))
            await callback.answer("Ошибка при завершении регистрации", show_alert=True)
        except Exception as e:
            logger.exception("Unexpected error completing onboarding")
            await callback.answer("Произошла ошибка", show_alert=True)