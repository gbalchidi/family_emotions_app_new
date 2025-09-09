"""Analysis repository implementation."""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.analysis.aggregates import AIRecommendation, Analysis, AnalysisStatus
from src.domain.analysis.repositories import AnalysisRepository
from src.domain.analysis.value_objects import SituationDescription
from src.infrastructure.persistence.models import AnalysisModel


class SqlAlchemyAnalysisRepository(AnalysisRepository):
    """SQLAlchemy implementation of AnalysisRepository."""
    
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
    
    async def save(self, analysis: Analysis) -> None:
        """Save analysis aggregate."""
        # Check if analysis exists
        stmt = select(AnalysisModel).where(AnalysisModel.id == analysis.id)
        result = await self._session.execute(stmt)
        db_analysis = result.scalar_one_or_none()
        
        if db_analysis:
            # Update existing analysis
            db_analysis.status = analysis.status.value
            db_analysis.completed_at = analysis.completed_at
            db_analysis.error_message = analysis.error_message
            
            if analysis.recommendation:
                db_analysis.hidden_meaning = analysis.recommendation.hidden_meaning
                db_analysis.immediate_actions = analysis.recommendation.immediate_actions
                db_analysis.long_term_recommendations = analysis.recommendation.long_term_recommendations
                db_analysis.what_not_to_do = analysis.recommendation.what_not_to_do
                db_analysis.confidence_score = analysis.recommendation.confidence_score
        else:
            # Create new analysis
            db_analysis = AnalysisModel(
                id=analysis.id,
                user_id=analysis.user_id,
                child_id=analysis.child_id,
                situation_description=str(analysis.situation),
                status=analysis.status.value,
                created_at=analysis.created_at,
                completed_at=analysis.completed_at,
                error_message=analysis.error_message
            )
            
            if analysis.recommendation:
                db_analysis.hidden_meaning = analysis.recommendation.hidden_meaning
                db_analysis.immediate_actions = analysis.recommendation.immediate_actions
                db_analysis.long_term_recommendations = analysis.recommendation.long_term_recommendations
                db_analysis.what_not_to_do = analysis.recommendation.what_not_to_do
                db_analysis.confidence_score = analysis.recommendation.confidence_score
            
            self._session.add(db_analysis)
        
        await self._session.flush()
    
    async def get_by_id(self, analysis_id: UUID) -> Optional[Analysis]:
        """Get analysis by ID."""
        stmt = select(AnalysisModel).where(AnalysisModel.id == analysis_id)
        result = await self._session.execute(stmt)
        db_analysis = result.scalar_one_or_none()
        
        if not db_analysis:
            return None
        
        return self._to_domain(db_analysis)
    
    async def get_user_analyses(
        self,
        user_id: UUID,
        limit: int = 10,
        offset: int = 0
    ) -> List[Analysis]:
        """Get user's analyses with pagination."""
        stmt = (
            select(AnalysisModel)
            .where(AnalysisModel.user_id == user_id)
            .order_by(AnalysisModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await self._session.execute(stmt)
        db_analyses = result.scalars().all()
        
        return [self._to_domain(db_analysis) for db_analysis in db_analyses]
    
    async def count_user_analyses_today(self, user_id: UUID) -> int:
        """Count user's analyses created today."""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        stmt = (
            select(func.count(AnalysisModel.id))
            .where(
                and_(
                    AnalysisModel.user_id == user_id,
                    AnalysisModel.created_at >= today_start
                )
            )
        )
        
        result = await self._session.execute(stmt)
        return result.scalar() or 0
    
    def _to_domain(self, db_analysis: AnalysisModel) -> Analysis:
        """Convert database model to domain aggregate."""
        recommendation = None
        if db_analysis.hidden_meaning:
            recommendation = AIRecommendation(
                hidden_meaning=db_analysis.hidden_meaning,
                immediate_actions=db_analysis.immediate_actions or "",
                long_term_recommendations=db_analysis.long_term_recommendations or "",
                what_not_to_do=db_analysis.what_not_to_do or "",
                confidence_score=db_analysis.confidence_score or 0.0
            )
        
        return Analysis(
            id=db_analysis.id,
            user_id=db_analysis.user_id,
            child_id=db_analysis.child_id,
            situation=SituationDescription(db_analysis.situation_description),
            status=AnalysisStatus(db_analysis.status),
            recommendation=recommendation,
            created_at=db_analysis.created_at,
            completed_at=db_analysis.completed_at,
            error_message=db_analysis.error_message
        )