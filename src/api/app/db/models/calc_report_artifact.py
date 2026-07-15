"""Immutable report artifacts and mutable instrumentation build tables."""

import datetime

from sqlalchemy import (
    BigInteger,
    CHAR,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel
from .enums import ArtifactBuildStatus


class CalcReportArtifact(BaseModel):
    """Describe an atomically published immutable report content object."""

    __tablename__ = "calc_report_artifact"
    __table_args__ = (
        CheckConstraint("artifactKind IN (1, 2)", name="artifact_kind_values"),
        CheckConstraint("fileCount >= 0", name="file_count_nonnegative"),
        CheckConstraint("totalSize >= 0", name="total_size_nonnegative"),
        CheckConstraint("formatVersion >= 1", name="format_version_positive"),
    )

    artifactKind: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    contentHash: Mapped[str] = mapped_column(CHAR(64), nullable=False, unique=True)
    storageKey: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    manifest: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    fileCount: Mapped[int] = mapped_column(Integer, nullable=False)
    totalSize: Mapped[int] = mapped_column(BigInteger, nullable=False)
    formatVersion: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=1, server_default="1"
    )


class CalcReportArtifactBuild(BaseModel):
    """Track one instrumented-artifact build for a source/runtime pair."""

    __tablename__ = "calc_report_artifact_build"
    __table_args__ = (
        UniqueConstraint(
            "sourceArtifactId",
            "runtimeFingerprint",
            name="uq_calc_report_artifact_build_source_runtime",
        ),
        CheckConstraint("status IN (0, 1, 2, 3)", name="status_values"),
        CheckConstraint("attemptCount >= 0", name="attempt_count_nonnegative"),
        CheckConstraint(
            f"status != {ArtifactBuildStatus.READY.value} OR outputArtifactId IS NOT NULL",
            name="ready_requires_output",
        ),
        CheckConstraint(
            f"status = {ArtifactBuildStatus.BUILDING.value} OR "
            "(leaseOwner IS NULL AND leaseExpiresAt IS NULL)",
            name="lease_only_while_building",
        ),
        Index(
            "ix_calc_report_artifact_build_status_lease",
            "status",
            "leaseExpiresAt",
        ),
    )

    sourceArtifactId: Mapped[int] = mapped_column(
        ForeignKey(
            "calc_report_artifact.id",
            name="fk_artifact_build_source",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )
    runtimeFingerprint: Mapped[str] = mapped_column(String(255), nullable=False)
    outputArtifactId: Mapped[int | None] = mapped_column(
        ForeignKey(
            "calc_report_artifact.id",
            name="fk_artifact_build_output",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )
    status: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=ArtifactBuildStatus.PENDING.value,
        server_default=str(ArtifactBuildStatus.PENDING.value),
    )
    diagnostics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    attemptCount: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    leaseOwner: Mapped[str | None] = mapped_column(String(128), nullable=True)
    leaseExpiresAt: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    startedAt: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completedAt: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updatedAt: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
