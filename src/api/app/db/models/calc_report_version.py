"""Published calculation-report version table definition."""

import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel
from .enums import VersionReviewStatus


class CalcReportVersion(BaseModel):
    """Persist an immutable semantic version of a report source artifact."""

    __tablename__ = "calc_report_version"
    __table_args__ = (
        UniqueConstraint(
            "reportId",
            "major",
            "minor",
            "patch",
            name="uq_calc_report_version_semver",
        ),
        UniqueConstraint("reportId", "id", name="uq_calc_report_version_report_id"),
        CheckConstraint("major >= 0", name="major_nonnegative"),
        CheckConstraint("minor >= 0", name="minor_nonnegative"),
        CheckConstraint("patch >= 0", name="patch_nonnegative"),
        CheckConstraint("reviewStatus IN (0, 1, 2)", name="review_status_values"),
    )

    reportId: Mapped[int] = mapped_column(
        ForeignKey("calc_report.id", ondelete="CASCADE"), nullable=False
    )
    sourceArtifactId: Mapped[int] = mapped_column(
        ForeignKey("calc_report_artifact.id", ondelete="RESTRICT"), nullable=False
    )
    major: Mapped[int] = mapped_column(Integer, nullable=False)
    minor: Mapped[int] = mapped_column(Integer, nullable=False)
    patch: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    publishedByUserId: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    reviewStatus: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=VersionReviewStatus.PENDING.value,
        server_default=str(VersionReviewStatus.PENDING.value),
    )
    reviewedByUserId: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    reviewedAt: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reviewComment: Mapped[str | None] = mapped_column(Text, nullable=True)
