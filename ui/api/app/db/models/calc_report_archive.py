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
    # 报告 id, 非必须, 默认为 0
    reportId: Mapped[int] = mapped_column(default=0)
    # 名称
    # 当没有 reportId 时，该字段为文件路径的 hash 值
    name: Mapped[str | None] = mapped_column(String(255), nullable=False)
    # 描述
    description: Mapped[str | None] = mapped_column(Text)
    # 计算书参数值
    defaults: Mapped[dict[str, dict[str, Any]]] = mapped_column(JSON, default={})
