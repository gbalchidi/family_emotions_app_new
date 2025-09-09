"""Analysis service."""
from __future__ import annotations

from typing import Optional, Protocol
from uuid import UUID

from domain.aggregates.situation import Situation
from domain.exceptions import (
    AnalysisFailedException,
    OnboardingNotCompletedException,
    UserNotFoundException,
)
from domain.repositories.situation import SituationRepository
from domain.repositories.user import UserRepository
from domain.value_objects import EmotionalTone
from application.commands import AnalyzeSituationCommand, GetSituationCommand
from application.dto import AnalysisResultDTO, SituationDTO


class ClaudeAdapter(Protocol):
    """Claude adapter protocol."""

    async def analyze_situation(
        self,
        situation: str,
        child_age: str,
        child_gender: str,
        context: Optional[str] = None,
    ) -> dict:
        """Analyze situation using Claude."""
        ...


class AnalysisService:
    """Analysis application service."""

    def __init__(
        self,
        user_repository: UserRepository,
        situation_repository: SituationRepository,
        claude_adapter: ClaudeAdapter,
    ) -> None:
        """Initialize analysis service."""
        self.user_repository = user_repository
        self.situation_repository = situation_repository
        self.claude_adapter = claude_adapter

    async def analyze_situation(
        self, command: AnalyzeSituationCommand
    ) -> SituationDTO:
        """Analyze situation."""
        # Get user
        user = await self.user_repository.get(command.user_id)
        if not user:
            raise UserNotFoundException(str(command.user_id))

        # Check onboarding
        if not user.onboarding_completed:
            raise OnboardingNotCompletedException()

        # Get child
        child = user.get_child(command.child_id)
        if not child:
            raise UserNotFoundException(f"Child {command.child_id} not found")

        # Create situation
        situation = Situation.create(
            user_id=command.user_id,
            child_id=command.child_id,
            description=command.description,
            context=command.context,
        )

        # Analyze with Claude
        try:
            analysis_result = await self.claude_adapter.analyze_situation(
                situation=command.description,
                child_age=str(child.age),
                child_gender=child.gender.value,
                context=command.context,
            )

            # Apply analysis to situation
            situation.apply_analysis(
                hidden_meaning=analysis_result["hidden_meaning"],
                immediate_actions=analysis_result["immediate_actions"],
                long_term_recommendations=analysis_result["long_term_recommendations"],
                what_not_to_do=analysis_result["what_not_to_do"],
                emotional_tone=EmotionalTone(analysis_result["emotional_tone"]),
                confidence_score=analysis_result.get("confidence_score", 0.8),
            )

        except Exception as e:
            raise AnalysisFailedException(str(e))

        # Save situation
        await self.situation_repository.save(situation)

        return self._to_dto(situation, child.name)

    async def get_situation(
        self, command: GetSituationCommand
    ) -> Optional[SituationDTO]:
        """Get situation by ID."""
        situation = await self.situation_repository.get(command.situation_id)
        if not situation:
            return None

        # Get user to find child name
        user = await self.user_repository.get(situation.user_id)
        if not user:
            return None

        child = user.get_child(situation.child_id)
        child_name = child.name if child else "Unknown"

        return self._to_dto(situation, child_name)

    async def get_user_situations(
        self, user_id: UUID, limit: int = 10, offset: int = 0
    ) -> list[SituationDTO]:
        """Get user's situations."""
        situations = await self.situation_repository.get_user_situations(
            user_id, limit, offset
        )

        # Get user to find child names
        user = await self.user_repository.get(user_id)
        if not user:
            return []

        result = []
        for situation in situations:
            child = user.get_child(situation.child_id)
            child_name = child.name if child else "Unknown"
            result.append(self._to_dto(situation, child_name))

        return result

    def _to_dto(self, situation: Situation, child_name: str) -> SituationDTO:
        """Convert situation to DTO."""
        analysis_dto = None
        if situation.analysis_result:
            analysis_dto = AnalysisResultDTO(
                hidden_meaning=situation.analysis_result.hidden_meaning,
                immediate_actions=situation.analysis_result.immediate_actions,
                long_term_recommendations=situation.analysis_result.long_term_recommendations,
                what_not_to_do=situation.analysis_result.what_not_to_do,
                emotional_tone=situation.analysis_result.emotional_tone,
                confidence_score=situation.analysis_result.confidence_score,
                analyzed_at=situation.analysis_result.analyzed_at,
            )

        return SituationDTO(
            id=situation.id,
            user_id=situation.user_id,
            child_id=situation.child_id,
            child_name=child_name,
            description=situation.description,
            context=situation.context,
            analysis_result=analysis_dto,
            created_at=situation.created_at,
            analyzed_at=situation.analyzed_at,
            is_analyzed=situation.is_analyzed,
        )