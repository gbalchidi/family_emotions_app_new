"""Database models."""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, Float
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base model."""

    pass


class UserModel(Base):
    """User database model."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True)
    telegram_id: Mapped[int] = mapped_column(unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    language_code: Mapped[str] = mapped_column(String(10), default="ru")
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    # Relationships
    children: Mapped[list["ChildModel"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    situations: Mapped[list["SituationModel"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class ChildModel(Base):
    """Child database model."""

    __tablename__ = "children"

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    birth_date: Mapped[datetime] = mapped_column(DateTime)
    gender: Mapped[str] = mapped_column(String(20))
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["UserModel"] = relationship(back_populates="children")
    situations: Mapped[list["SituationModel"]] = relationship(
        back_populates="child", cascade="all, delete-orphan"
    )


class SituationModel(Base):
    """Situation database model."""

    __tablename__ = "situations"

    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    child_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), index=True
    )
    description: Mapped[str] = mapped_column(Text)
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    analyzed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Analysis result fields
    hidden_meaning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    immediate_actions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    long_term_recommendations: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    what_not_to_do: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    emotional_tone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    user: Mapped["UserModel"] = relationship(back_populates="situations")
    child: Mapped["ChildModel"] = relationship(back_populates="situations")