"""Telegram bot FSM states."""

from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    """Registration flow states."""
    
    waiting_for_parent_name = State()
    waiting_for_child_name = State()
    waiting_for_child_age = State()
    waiting_for_child_gender = State()


class AddChildStates(StatesGroup):
    """Add child flow states."""
    
    waiting_for_name = State()
    waiting_for_age = State()
    waiting_for_gender = State()


class AnalysisStates(StatesGroup):
    """Analysis flow states."""
    
    waiting_for_child_selection = State()
    waiting_for_situation = State()