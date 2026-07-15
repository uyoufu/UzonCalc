"""Workspace dependency and version-selector table definitions."""

import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
    false,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class CalcReportDependency(BaseModel):
    """Name a report dependency within one workspace namespace."""

    __tablename__ = "calc_report_dependency"
    __table_args__ = (
        UniqueConstraint(
            "reportId", "alias", name="uq_calc_report_dependency_report_alias"
        ),
        UniqueConstraint(
            "id",
            "targetReportId",
            name="uq_calc_report_dependency_id_target_report",
        ),
        CheckConstraint("reportId != targetReportId", name="reports_differ"),
    )

    reportId: Mapped[int] = mapped_column(
        ForeignKey("calc_report.id", ondelete="CASCADE"), nullable=False
    )
    targetReportId: Mapped[int] = mapped_column(
        ForeignKey("calc_report.id", ondelete="RESTRICT"), nullable=False
    )
    alias: Mapped[str] = mapped_column(String(64), nullable=False)
    updatedAt: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
    )


class CalcReportDependencySelector(BaseModel):
    """Resolve one dependency alias to latest or an explicit target version."""

    __tablename__ = "calc_report_dependency_selector"
    __table_args__ = (
        ForeignKeyConstraint(
            ["dependencyId", "targetReportId"],
            ["calc_report_dependency.id", "calc_report_dependency.targetReportId"],
            name="fk_dependency_selector_dependency_target",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["targetReportId", "targetVersionId"],
            ["calc_report_version.reportId", "calc_report_version.id"],
            name="fk_dependency_selector_target_version",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "dependencyId",
            "selectorKey",
            name="uq_dependency_selector_dependency_key",
        ),
        CheckConstraint(
            "(selectorKey = 'latest' AND targetVersionId IS NULL) OR "
            "(selectorKey != 'latest' AND targetVersionId IS NOT NULL)",
            name="selector_target_shape",
        ),
        Index(
            "uq_dependency_selector_default",
            "dependencyId",
            unique=True,
            sqlite_where=text('"isDefault" IS TRUE'),
            postgresql_where=text('"isDefault" IS TRUE'),
        ),
    )

    dependencyId: Mapped[int] = mapped_column(nullable=False)
    targetReportId: Mapped[int] = mapped_column(nullable=False)
    selectorKey: Mapped[str] = mapped_column(String(32), nullable=False)
    targetVersionId: Mapped[int | None] = mapped_column(nullable=True)
    isDefault: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
