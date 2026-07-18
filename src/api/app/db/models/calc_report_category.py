"""Calculation-report category table definition."""

import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    false,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class CalcReportCategory(BaseModel):
    """Group a user's calculation reports for navigation and ordering."""

    __tablename__ = "calc_report_category"
    __table_args__ = (
        Index(
            "uq_calc_report_category_active_user_name",
            "userId",
            "name",
            unique=True,
            sqlite_where=text('"deletedAt" IS NULL'),
            postgresql_where=text('"deletedAt" IS NULL'),
        ),
        Index(
            "ix_calc_report_category_user_deleted_sort",
            "userId",
            "deletedAt",
            "isPinned",
            "manualOrder",
        ),
    )

    userId: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    manualOrder: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    isPinned: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    isHidden: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    frequencyCount: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    agingEpoch: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    lastUsedAt: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updatedAt: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    deletedAt: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
