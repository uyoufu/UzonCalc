"""Published-version sharing table definitions."""

import datetime

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, BaseModel


class CalcReportShareLink(BaseModel):
    """Persist a revocable access token for an approved report version."""

    __tablename__ = "calc_report_share_link"
    __table_args__ = (
        CheckConstraint("accessType IN (1, 2, 3)", name="access_type_values"),
        CheckConstraint(
            "maxUseCount IS NULL OR maxUseCount >= 0",
            name="max_use_count_nonnegative",
        ),
        CheckConstraint("useCount >= 0", name="use_count_nonnegative"),
    )

    versionId: Mapped[int] = mapped_column(
        ForeignKey("calc_report_version.id", ondelete="RESTRICT"), nullable=False
    )
    tokenHash: Mapped[str] = mapped_column(CHAR(64), nullable=False, unique=True)
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
