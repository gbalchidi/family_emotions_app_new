"""Analysis application service."""

from typing import List, Protocol
from uuid import UUID

from src.application.commands.analysis_commands import RequestAnalysisCommand
from src.domain.analysis.aggregates import AIRecommendation, Analysis
from src.domain.analysis.repositories import AnalysisRepository


class AIAnalyzer(Protocol):
    """AI analyzer protocol."""
    
    async def analyze_situation(
        self,
        situation: str,
        child_age: int,
        child_gender: str
    ) -> AIRecommendation:
        """Analyze situation and generate recommendations."""
        ...


class RateLimiter(Protocol):
    """Rate limiter protocol."""
    
    async def check_limit(self, user_id: UUID) -> bool:
        """Check if user has reached rate limit."""
        ...
    
    async def increment_usage(self, user_id: UUID) -> None:
        """Increment usage counter."""
        ...


class AnalysisService:
    """Analysis application service."""
    
    def __init__(
        self,
        analysis_repository: AnalysisRepository,
        ai_analyzer: AIAnalyzer,
        rate_limiter: RateLimiter
    ) -> None:
        self._repository = analysis_repository
        self._ai_analyzer = ai_analyzer
        self._rate_limiter = rate_limiter
    
    async def request_analysis(self, command: RequestAnalysisCommand) -> Analysis:
        """Request situation analysis."""
        # Check rate limits
        if not await self._rate_limiter.check_limit(command.user_id):
            raise ValueError("Daily analysis limit exceeded")
        
        # Create analysis request
        analysis = Analysis.create(
            user_id=command.user_id,
            child_id=command.child_id,
            situation_text=command.situation_description
        )
        
        # Save initial state
        await self._repository.save(analysis)
        
        try:
            # Start processing
            analysis.start_processing()
            await self._repository.save(analysis)
            
            # Get AI recommendations
            recommendation = await self._ai_analyzer.analyze_situation(
                situation=command.situation_description,
                child_age=command.child_age,
                child_gender=command.child_gender
            )
            
            # Complete analysis
            analysis.complete(recommendation)
            await self._repository.save(analysis)
            
            # Update rate limiter
            await self._rate_limiter.increment_usage(command.user_id)
            
        except Exception as e:
            # Mark as failed
            analysis.fail(str(e))
            await self._repository.save(analysis)
            raise
        
        return analysis
    
    async def get_user_analyses(
        self,
        user_id: UUID,
        limit: int = 10
    ) -> List[Analysis]:
        """Get user's analysis history."""
        return await self._repository.get_user_analyses(user_id, limit=limit)