"""Execution interaction history and recent-input cache table definitions."""

import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class UserInputHistory(BaseModel):
    """Persist high-frequency interactive input state for one execution."""

    __tablename__ = "user_input_history"

    executionId: Mapped[int] = mapped_column(
        ForeignKey("calc_execution.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    defaults: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    windows: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    inputHistory: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    currentStep: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    totalSteps: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    updatedAt: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
    )


class InputCache(BaseModel):
    """Persist a user's most recent input for one report entry point."""

    __tablename__ = "input_cache"
    __table_args__ = (
        UniqueConstraint(
            "userId",
            "reportId",
            "entryName",
            name="uq_input_cache_user_report_entry",
        ),
    )

    userId: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    reportId: Mapped[int] = mapped_column(
        ForeignKey("calc_report.id", ondelete="CASCADE"), nullable=False
    )
    entryName: Mapped[str] = mapped_column(String(128), nullable=False)
    sourceArtifactId: Mapped[int] = mapped_column(
        ForeignKey("calc_report_artifact.id", ondelete="RESTRICT"), nullable=False
    )
    defaults: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    updatedAt: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    expiresAt: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
