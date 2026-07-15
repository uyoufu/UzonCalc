"""Saved calculation-report instance table definition."""

import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class CalcReportInstance(BaseModel):
    """Persist a reproducible saved result backed by an immutable bundle."""

    __tablename__ = "calc_report_instance"
    __table_args__ = (
        ForeignKeyConstraint(
            ["reportId", "sourceVersionId"],
            ["calc_report_version.reportId", "calc_report_version.id"],
            name="fk_calc_report_instance_source_version",
            ondelete="RESTRICT",
        ),
        CheckConstraint("revision >= 1", name="revision_positive"),
        Index(
            "ix_calc_report_instance_user_deleted_updated",
            "userId",
            "deletedAt",
            "updatedAt",
        ),
    )

    userId: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    categoryId: Mapped[int] = mapped_column(
        ForeignKey(
            "calc_report_instance_category.id",
            name="fk_report_instance_category",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    reportId: Mapped[int] = mapped_column(
        ForeignKey("calc_report.id", ondelete="RESTRICT"), nullable=False
    )
    sourceVersionId: Mapped[int | None] = mapped_column(nullable=True)
    bundleId: Mapped[int] = mapped_column(
        ForeignKey("calc_execution_bundle.id", ondelete="RESTRICT"), nullable=False
    )
    executionId: Mapped[int | None] = mapped_column(
        ForeignKey("calc_execution.id", ondelete="SET NULL"), nullable=True
    )
    reportName: Mapped[str | None] = mapped_column(String(100), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    defaults: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    resultPath: Mapped[str] = mapped_column(String(500), nullable=False)
    revision: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=1, server_default="1"
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
