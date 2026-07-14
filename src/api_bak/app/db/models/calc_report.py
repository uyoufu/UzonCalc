import datetime

from sqlalchemy import JSON, DateTime, String, Text
from .base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column


class CalcReport(BaseModel):
    """system_settings table model"""

    __tablename__ = "calc_report"

    userId: Mapped[int] = mapped_column(nullable=False, index=True)
    categoryId: Mapped[int] = mapped_column(nullable=False, index=True)

    # 报告类型
    type: Mapped[int] = mapped_column(
        nullable=False,
        default=1,
        comment="报告类型：1-用户报告模板，11-报告实例",
    )
    # 状态： 0-删除，1-正常
    status: Mapped[int] = mapped_column(
        nullable=False, default=1, comment="状态：0-删除，1-正常"
    )

    # 名称
    name: Mapped[str] = mapped_column(String(100))
    # 描述
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 封面
    cover: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # 版本号，每次更新时，自动加 1
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    # 复制来源报告 ID，默认为 0，表示非复制创建
    copyFromId: Mapped[int] = mapped_column(nullable=False, default=0)

    # 最近一次修改时间，自动更新
    lastModified: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
        index=True,
        comment="最近一次修改时间，自动更新",
    )

    # 是否已审核通过，默认为 False
    # 仅通过审核的报告才能被分享
    isApproved: Mapped[bool] = mapped_column(
        nullable=False, default=False, comment="是否已审核通过"
    )

    shareType: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
        comment="分享类型：0-私密，1-公开，2-指定用户",
    )
    shareToUserIds: Mapped[list[int] | None] = mapped_column(
        JSON, nullable=True, comment="当 shareType=2 时，指定可以访问的用户 ID 列表"
    )
