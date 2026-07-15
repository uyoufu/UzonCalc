"""Favorite calculation-report association table definition."""

import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class FavoriteCalcReport(Base):
    """Associate a user with one favorited calculation report."""

    __tablename__ = "favorite_calc_reports"

    userId: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    reportId: Mapped[int] = mapped_column(
        ForeignKey("calc_report.id", ondelete="CASCADE"), primary_key=True
    )
    createdAt: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
    )
