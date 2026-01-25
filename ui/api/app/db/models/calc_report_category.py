from sqlalchemy import JSON, String, Text
from .base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column


class CalcReportCategory(BaseModel):
    """system_settings table model"""

    __tablename__ = "calc_report_category"

    userId: Mapped[int] = mapped_column(nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    # 状态： 0-删除，1-正常
    status: Mapped[int] = mapped_column(nullable=False, default=1)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover: Mapped[str | None] = mapped_column(String(255), nullable=True)
    order: Mapped[int] = mapped_column(nullable=False)
    # 关联的计算书数量
    total: Mapped[int] = mapped_column(nullable=False, default=0)
