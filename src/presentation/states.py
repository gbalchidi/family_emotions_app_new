"""Bot FSM states."""
from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class OnboardingStates(StatesGroup):
    """Onboarding states."""

    waiting_for_parent_name = State()
    waiting_for_children_count = State()
    waiting_for_children_ages = State()
    waiting_for_child_name = State()
    waiting_for_problem_type = State()
    # Legacy states for compatibility
    waiting_for_child_birth_date = State()  # Deprecated
    waiting_for_child_age = State()
    waiting_for_child_gender = State()
    waiting_for_another_child = State()


class AnalysisStates(StatesGroup):
    """Analysis states."""

    waiting_for_child_selection = State()
    waiting_for_situation = State()
    waiting_for_context = State()


class TranslatorStates(StatesGroup):
    """Emotion translator states."""
    
    waiting_for_phrase = State()