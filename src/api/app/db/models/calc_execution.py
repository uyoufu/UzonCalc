"""Execution bundle, component, and execution audit table definitions."""

import datetime

from sqlalchemy import (
    Boolean,
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
    UniqueConstraint,
    and_,
    false,
    or_,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel
from .enums import ExecutionSourceType, ExecutionStatus, ExecutionTargetType


class CalcExecutionBundle(BaseModel):
    """Persist an immutable, content-addressed executable report bundle."""

    __tablename__ = "calc_execution_bundle"
    __table_args__ = (
        CheckConstraint("formatVersion >= 1", name="format_version_positive"),
    )

    bundleHash: Mapped[str] = mapped_column(CHAR(64), nullable=False, unique=True)
    runtimeFingerprint: Mapped[str] = mapped_column(String(255), nullable=False)
    runtimeImageDigest: Mapped[str | None] = mapped_column(String(71), nullable=True)
    entrySourceArtifactId: Mapped[int] = mapped_column(
        ForeignKey(
            "calc_report_artifact.id",
            name="fk_execution_bundle_entry_source",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    entryExecutionArtifactId: Mapped[int] = mapped_column(
        ForeignKey(
            "calc_report_artifact.id",
            name="fk_execution_bundle_entry_execution",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    manifest: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    formatVersion: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=1, server_default="1"
    )


class CalcExecutionBundleComponent(BaseModel):
    """Persist one entry or dependency component referenced by a bundle."""

    __tablename__ = "calc_execution_bundle_component"

    bundleId: Mapped[int] = mapped_column(
        ForeignKey(
            "calc_execution_bundle.id",
            name="fk_bundle_component_bundle",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    componentKey: Mapped[str] = mapped_column(String(160), nullable=False)
    scopeKey: Mapped[str] = mapped_column(String(80), nullable=False)
    alias: Mapped[str | None] = mapped_column(String(64), nullable=True)
    selectorKey: Mapped[str | None] = mapped_column(String(32), nullable=True)
    sourceArtifactId: Mapped[int] = mapped_column(
        ForeignKey(
            "calc_report_artifact.id",
            name="fk_bundle_component_source",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    executionArtifactId: Mapped[int] = mapped_column(
        ForeignKey(
            "calc_report_artifact.id",
            name="fk_bundle_component_execution",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    isEntry: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )

    __table_args__ = (
        UniqueConstraint(
            "bundleId",
            "componentKey",
            name="uq_execution_bundle_component_key",
        ),
        CheckConstraint(
            or_(
                and_(isEntry.is_(True), alias.is_(None), selectorKey.is_(None)),
                and_(
                    isEntry.is_(False),
                    alias.is_not(None),
                    selectorKey.is_not(None),
                ),
            ),
            name="entry_dependency_shape",
        ),
        Index(
            "uq_execution_bundle_entry",
            "bundleId",
            unique=True,
            sqlite_where=text('"isEntry" IS TRUE'),
            postgresql_where=text('"isEntry" IS TRUE'),
        ),
    )


class CalcExecution(BaseModel):
    """Persist low-frequency execution state and reproducibility provenance."""

    __tablename__ = "calc_execution"
    __table_args__ = (
        ForeignKeyConstraint(
            ["reportId", "resolvedVersionId"],
            ["calc_report_version.reportId", "calc_report_version.id"],
            name="fk_calc_execution_resolved_version",
            ondelete="RESTRICT",
        ),
        CheckConstraint("sourceType IN (1, 2, 3)", name="source_type_values"),
        CheckConstraint("executorType IN (1, 2)", name="executor_type_values"),
        CheckConstraint("status IN (0, 1, 2, 3, 4, 5)", name="status_values"),
        CheckConstraint(
            f"(sourceType = {ExecutionSourceType.WORKSPACE.value} "
            "AND resolvedVersionId IS NULL) OR "
            f"(sourceType IN ({ExecutionSourceType.LATEST.value}, "
            f"{ExecutionSourceType.VERSION.value}) AND resolvedVersionId IS NOT NULL)",
            name="source_version_shape",
        ),
        Index("ix_calc_execution_user_created", "userId", "createdAt"),
        Index("ix_calc_execution_report_created", "reportId", "createdAt"),
        Index("ix_calc_execution_status_expires", "status", "expiresAt"),
    )

    userId: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    reportId: Mapped[int] = mapped_column(
        ForeignKey("calc_report.id", ondelete="RESTRICT"), nullable=False
    )
    bundleId: Mapped[int] = mapped_column(
        ForeignKey("calc_execution_bundle.id", ondelete="RESTRICT"), nullable=False
    )
    sourceType: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    resolvedVersionId: Mapped[int | None] = mapped_column(nullable=True)
    executorType: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    status: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=ExecutionStatus.PENDING.value,
        server_default=str(ExecutionStatus.PENDING.value),
    )
    sandboxExecutionId: Mapped[str | None] = mapped_column(
        String(64), nullable=True, unique=True
    )
    executorNodeId: Mapped[str | None] = mapped_column(String(128), nullable=True)
    startedAt: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    lastActiveAt: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expiresAt: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completedAt: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resultPath: Mapped[str | None] = mapped_column(String(500), nullable=True)
    errorCode: Mapped[str | None] = mapped_column(String(64), nullable=True)
    errorMessage: Mapped[str | None] = mapped_column(Text, nullable=True)
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class CalcExecutionSlot(BaseModel):
    """Retain one active and one last-successful execution per business target."""

    __tablename__ = "calc_execution_slot"
    __table_args__ = (
        CheckConstraint(
            f"(targetType = {ExecutionTargetType.WORKSPACE.value} AND reportId IS NOT NULL "
            "AND versionId IS NULL AND instanceId IS NULL AND shareLinkId IS NULL) OR "
            f"(targetType = {ExecutionTargetType.VERSION.value} AND reportId IS NULL "
            "AND versionId IS NOT NULL AND instanceId IS NULL AND shareLinkId IS NULL) OR "
            f"(targetType = {ExecutionTargetType.INSTANCE.value} AND reportId IS NULL "
            "AND versionId IS NULL AND instanceId IS NOT NULL AND shareLinkId IS NULL) OR "
            f"(targetType = {ExecutionTargetType.SHARE_PREVIEW.value} AND reportId IS NULL "
            "AND versionId IS NULL AND instanceId IS NULL AND shareLinkId IS NOT NULL)",
            name="execution_slot_target_shape",
        ),
        CheckConstraint("targetType IN (1, 2, 3, 4)", name="target_type_values"),
        Index(
            "uq_execution_slot_workspace",
            "userId",
            "reportId",
            unique=True,
            sqlite_where=text('"targetType" = 1'),
            postgresql_where=text('"targetType" = 1'),
        ),
        Index(
            "uq_execution_slot_version",
            "userId",
            "versionId",
            unique=True,
            sqlite_where=text('"targetType" = 2'),
            postgresql_where=text('"targetType" = 2'),
        ),
        Index(
            "uq_execution_slot_instance",
            "userId",
            "instanceId",
            unique=True,
            sqlite_where=text('"targetType" = 3'),
            postgresql_where=text('"targetType" = 3'),
        ),
        Index(
            "uq_execution_slot_share",
            "userId",
            "shareLinkId",
            unique=True,
            sqlite_where=text('"targetType" = 4'),
            postgresql_where=text('"targetType" = 4'),
        ),
    )

    userId: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    targetType: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    reportId: Mapped[int | None] = mapped_column(
        ForeignKey("calc_report.id", ondelete="CASCADE"), nullable=True
    )
    versionId: Mapped[int | None] = mapped_column(
        ForeignKey("calc_report_version.id", ondelete="CASCADE"), nullable=True
    )
    instanceId: Mapped[int | None] = mapped_column(
        ForeignKey("calc_report_instance.id", ondelete="CASCADE"), nullable=True
    )
    shareLinkId: Mapped[int | None] = mapped_column(
        ForeignKey("calc_report_share_link.id", ondelete="CASCADE"), nullable=True
    )
    currentExecutionId: Mapped[int | None] = mapped_column(
        ForeignKey("calc_execution.id", ondelete="SET NULL"), nullable=True
    )
    activeExecutionId: Mapped[int | None] = mapped_column(
        ForeignKey("calc_execution.id", ondelete="SET NULL"), nullable=True
    )
