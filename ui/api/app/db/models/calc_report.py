from sqlalchemy import JSON, String, Text
from .base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column


class CalcReport(BaseModel):
    """system_settings table model"""

    __tablename__ = "calc_report"

    userId: Mapped[int] = mapped_column(nullable=False, index=True)
    categoryId: Mapped[int] = mapped_column(nullable=False, index=True)

    # 名称
    name: Mapped[str] = mapped_column(String(50))
    # 描述
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 封面
    cover: Mapped[str | None] = mapped_column(String(255), nullable=True)
