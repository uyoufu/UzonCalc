from sqlalchemy import JSON, String
from .base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column


class SystemSetting(BaseModel):
    """system_settings table model"""

    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    value: Mapped[dict] = mapped_column(JSON, nullable=False)
    description: Mapped[str | None]
    readonly: Mapped[bool] = mapped_column(default=False)
