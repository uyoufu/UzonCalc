"""Calculation-report workspace identity and origin table definitions."""

import datetime

from sqlalchemy import (
    BigInteger,
    CHAR,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    JSON,
    SmallInteger,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class CalcReport(BaseModel):
    """Persist a user's mutable calculation-report workspace identity."""

    __tablename__ = "calc_report"
    __table_args__ = (
        ForeignKeyConstraint(
            ["id", "latestVersionId"],
            ["calc_report_version.reportId", "calc_report_version.id"],
            name="fk_calc_report_latest_version",
            ondelete="RESTRICT",
            use_alter=True,
        ),
        CheckConstraint("formatVersion >= 1", name="format_version_positive"),
        CheckConstraint(
            "workspaceRevision >= 0", name="workspace_revision_nonnegative"
        ),
        Index(
            "uq_calc_report_active_user_category_name",
            "userId",
            "categoryId",
            "name",
            unique=True,
            sqlite_where=text('"deletedAt" IS NULL'),
            postgresql_where=text('"deletedAt" IS NULL'),
        ),
        Index(
            "ix_calc_report_user_deleted_updated",
            "userId",
            "deletedAt",
            "updatedAt",
        ),
    )

    userId: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    categoryId: Mapped[int] = mapped_column(
        ForeignKey("calc_report_category.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover: Mapped[str | None] = mapped_column(String(500), nullable=True)
    entryPath: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="src/main.py",
        server_default="src/main.py",
    )
    formatVersion: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=1, server_default="1"
    )
    workspaceRevision: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0"
    )
    workspaceArtifactId: Mapped[int | None] = mapped_column(
        ForeignKey("calc_report_artifact.id", ondelete="RESTRICT"), nullable=True
    )
    latestVersionId: Mapped[int | None] = mapped_column(nullable=True)
    updatedAt: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
    deletedAt: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class CalcReportOrigin(BaseModel):
    """Persist optional provenance for a calculation report."""

    __tablename__ = "calc_report_origin"
    __table_args__ = (
        CheckConstraint("originType IN (1, 2, 3, 4)", name="origin_type_values"),
    )

    reportId: Mapped[int] = mapped_column(
        ForeignKey("calc_report.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    originType: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    sourceReportId: Mapped[int | None] = mapped_column(
        ForeignKey("calc_report.id", ondelete="RESTRICT"), nullable=True
    )
    sourceVersionId: Mapped[int | None] = mapped_column(
        ForeignKey("calc_report_version.id", ondelete="RESTRICT"), nullable=True
    )
    sourceArtifactId: Mapped[int | None] = mapped_column(
        ForeignKey("calc_report_artifact.id", ondelete="RESTRICT"), nullable=True
    )
    sourceArchiveHash: Mapped[str | None] = mapped_column(CHAR(64), nullable=True)
    originMetadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
