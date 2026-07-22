"""Published-version sharing table definitions."""

import datetime

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    SmallInteger,
    String,
    Text,
    Boolean,
    false,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, BaseModel


class CalcReportShareLink(BaseModel):
    """Persist a revocable access token for an approved report version."""

    __tablename__ = "calc_report_share_link"
    __table_args__ = (
        CheckConstraint("accessType IN (1, 2, 3, 4)", name="access_type_values"),
        CheckConstraint(
            "maxUseCount IS NULL OR maxUseCount >= 0",
            name="max_use_count_nonnegative",
        ),
        CheckConstraint("useCount >= 0", name="use_count_nonnegative"),
        ForeignKeyConstraint(
            ["reportId", "versionId"],
            ["calc_report_version.reportId", "calc_report_version.id"],
            name="fk_share_link_report_version",
            ondelete="RESTRICT",
        ),
    )

    reportId: Mapped[int] = mapped_column(Integer, nullable=False)
    versionId: Mapped[int] = mapped_column(nullable=False)
    tokenHash: Mapped[str] = mapped_column(CHAR(64), nullable=False, unique=True)
    tokenCiphertext: Mapped[str] = mapped_column(Text, nullable=False)
    accessType: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    expiresAt: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revokedAt: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    maxUseCount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    useCount: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    canEdit: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    canShare: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    createdByUserId: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )


class CalcReportShareRecipient(Base):
    """Associate a specified-users share link with an authorized user."""

    __tablename__ = "calc_report_share_recipient"

    shareLinkId: Mapped[int] = mapped_column(
        ForeignKey(
            "calc_report_share_link.id",
            name="fk_share_recipient_link",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    userId: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )


class CalcReportShareDepartment(Base):
    """Associate a department-scoped share link with an authorized department."""

    __tablename__ = "calc_report_share_department"

    shareLinkId: Mapped[int] = mapped_column(
        ForeignKey("calc_report_share_link.id", ondelete="CASCADE"), primary_key=True
    )
    departmentId: Mapped[int] = mapped_column(
        ForeignKey("department.id", ondelete="CASCADE"), primary_key=True
    )
