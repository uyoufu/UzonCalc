"""
Temporary File Model - Tracks temporary files that need to be cleaned up after expiration
"""

import datetime
from sqlalchemy import String, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from .base import BaseModel


class TmpFile(BaseModel):
    """临时文件表模型"""

    __tablename__ = "tmp_files"

    # 文件路径（绝对路径）
    filePath: Mapped[str] = mapped_column(
        String(500), nullable=False, index=True, unique=True
    )

    # 过期时间（UTC时间）
    expireTime: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    # 备注信息
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 是否已删除
    isDeleted: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )

    # 删除时间
    deletedAt: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self):
        return f"<TmpFile(id={self.id}, filePath='{self.filePath}', expireTime='{self.expireTime}')>"
