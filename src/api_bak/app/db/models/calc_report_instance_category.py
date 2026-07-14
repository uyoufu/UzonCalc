from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class CalcReportInstanceCategory(BaseModel):
    """计算实例分类"""

    __tablename__ = "calc_report_instance_category"

    userId: Mapped[int] = mapped_column(nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(50), index=True)
    # 状态：0-删除，1-正常
    status: Mapped[int] = mapped_column(nullable=False, default=1)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order: Mapped[int] = mapped_column(nullable=False)
    # 关联的计算实例数量
    total: Mapped[int] = mapped_column(nullable=False, default=0)
