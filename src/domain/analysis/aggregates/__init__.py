"""Analysis aggregate root and related entities."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from src.domain.analysis.value_objects import SituationDescription
from src.domain.analysis.events import AnalysisRequested, AnalysisCompleted


class AnalysisStatus(Enum):
    """Analysis status enumeration."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AIRecommendation:
    """AI-generated recommendation value object."""
    
    hidden_meaning: str
    immediate_actions: str
    long_term_recommendations: str
    what_not_to_do: str
    confidence_score: float = 0.0
    
    def __post_init__(self) -> None:
        if not 0 <= self.confidence_score <= 1:
            raise ValueError("Confidence score must be between 0 and 1")


@dataclass
class Analysis:
    """Analysis aggregate root."""
    
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    child_id: UUID = field(default_factory=uuid4)
    situation: SituationDescription = field(
        default_factory=lambda: SituationDescription("")
    )
    status: AnalysisStatus = AnalysisStatus.PENDING
    recommendation: Optional[AIRecommendation] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    _events: list = field(default_factory=list, init=False, repr=False)
    
    @classmethod
    def create(
        cls,
        user_id: UUID,
        child_id: UUID,
        situation_text: str
    ) -> "Analysis":
        """Create a new analysis request."""
        analysis = cls(
            user_id=user_id,
            child_id=child_id,
            situation=SituationDescription(situation_text),
            status=AnalysisStatus.PENDING
        )
        
        analysis._events.append(
            AnalysisRequested(
                analysis_id=analysis.id,
                user_id=user_id,
                child_id=child_id,
                situation=situation_text,
                timestamp=analysis.created_at
            )
        )
        return analysis
    
    def start_processing(self) -> None:
        """Mark analysis as processing."""
        if self.status != AnalysisStatus.PENDING:
            raise ValueError(f"Cannot start processing from status {self.status}")
        self.status = AnalysisStatus.PROCESSING
    
    def complete(self, recommendation: AIRecommendation) -> None:
        """Complete analysis with AI recommendation."""
        if self.status != AnalysisStatus.PROCESSING:
            raise ValueError(f"Cannot complete from status {self.status}")
        
        self.status = AnalysisStatus.COMPLETED
        self.recommendation = recommendation
        self.completed_at = datetime.utcnow()
        
        self._events.append(
            AnalysisCompleted(
                analysis_id=self.id,
                user_id=self.user_id,
                timestamp=self.completed_at,
                confidence_score=recommendation.confidence_score
            )
        )
    
    def fail(self, error_message: str) -> None:
        """Mark analysis as failed."""
        self.status = AnalysisStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
    
    def get_events(self) -> list:
        """Get and clear domain events."""
        events = self._events.copy()
        self._events.clear()
        return events