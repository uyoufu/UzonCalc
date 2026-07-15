"""Temporary-file cleanup table definition."""

import datetime

from sqlalchemy import Boolean, DateTime, Index, String, Text, UniqueConstraint, false
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class TmpFile(BaseModel):
    """Track an expiring temporary file and its cleanup state."""

    __tablename__ = "tmp_files"
    __table_args__ = (
        UniqueConstraint("filePath", name="uq_tmp_files_filePath"),
        Index("ix_tmp_files_filePath", "filePath"),
        Index("ix_tmp_files_expireTime", "expireTime"),
        Index("ix_tmp_files_isDeleted", "isDeleted"),
    )

    filePath: Mapped[str] = mapped_column(String(500), nullable=False)
    expireTime: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    isDeleted: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false(), nullable=False
    )
    deletedAt: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        """Return a concise diagnostic representation of the temporary file.

        Returns:
            String containing the row ID, path, and expiration timestamp.
        """

        return (
            f"<TmpFile(id={self.id}, filePath='{self.filePath}', "
            f"expireTime='{self.expireTime}')>"
        )
