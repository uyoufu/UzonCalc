import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class CalcReportInstance(BaseModel):
    """计算实例"""

    __tablename__ = "calc_report_instance"

    userId: Mapped[int] = mapped_column(nullable=False, index=True)
    categoryId: Mapped[int] = mapped_column(nullable=False, index=True)
    # 来源计算报告 ID
    reportId: Mapped[int] = mapped_column(nullable=False, index=True)
    # 来源报告名称快照，用于列表展示
    reportName: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # 状态：0-删除，1-正常
    status: Mapped[int] = mapped_column(nullable=False, default=1)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    defaults: Mapped[dict[str, dict[str, Any]]] = mapped_column(JSON, default={})
    # 保存后的 HTML 相对路径，例如 public/calc-instances/1/xxx/hash.html
    resultPath: Mapped[str | None] = mapped_column(String(500), nullable=True)

    version: Mapped[int] = mapped_column(nullable=False, default=1)
    lastModified: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
        index=True,
        comment="最近一次修改时间，自动更新",
    )
