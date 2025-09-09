"""SQLAlchemy database models."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class UserModel(Base):
    """User database model."""
    
    __tablename__ = "users"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    telegram_username = Column(String(100), nullable=True)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    children = relationship("ChildModel", back_populates="user", cascade="all, delete-orphan")
    analyses = relationship("AnalysisModel", back_populates="user")


class ChildModel(Base):
    """Child database model."""
    
    __tablename__ = "children"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(
        Enum("male", "female", "not_specified", name="child_gender"),
        default="not_specified",
        nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("UserModel", back_populates="children")
    analyses = relationship("AnalysisModel", back_populates="child")


class AnalysisModel(Base):
    """Analysis database model."""
    
    __tablename__ = "analyses"
    
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    child_id = Column(PG_UUID(as_uuid=True), ForeignKey("children.id"), nullable=False)
    situation_description = Column(Text, nullable=False)
    status = Column(
        Enum("pending", "processing", "completed", "failed", name="analysis_status"),
        default="pending",
        nullable=False
    )
    
    # AI Recommendation fields
    hidden_meaning = Column(Text, nullable=True)
    immediate_actions = Column(Text, nullable=True)
    long_term_recommendations = Column(Text, nullable=True)
    what_not_to_do = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("UserModel", back_populates="analyses")
    child = relationship("ChildModel", back_populates="analyses")
    
    __table_args__ = (
        # Index for fetching user's analyses by date
        UniqueConstraint("user_id", "created_at", name="idx_user_analyses_by_date"),
    )