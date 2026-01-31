from typing import Any
from sqlalchemy import JSON, String, Text
from .base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column


class CalcReportArchive(BaseModel):
    """system_settings table model"""

    __tablename__ = "calc_report_archive"

    userId: Mapped[int] = mapped_column(nullable=False, index=True)
    # 状态： 0-删除，1-正常
    status: Mapped[int] = mapped_column(nullable=False, default=1)
    # 归档状态： 0-临时的，用于记录用户在这个 reportId 下的上一次历史记录，1-已归档
    type: Mapped[int] = mapped_column(nullable=False, default=1)
    # 报告 id
    reportId: Mapped[int]
    # 名称，必须项
    name: Mapped[str] = mapped_column(String(100))
    # 描述
    description: Mapped[str | None] = mapped_column(Text)
    # 计算书参数值
    defaults: Mapped[dict[str, dict[str, Any]]] = mapped_column(JSON, default={})
