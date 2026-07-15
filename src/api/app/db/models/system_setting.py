"""System-wide settings table definition."""

from sqlalchemy import JSON, String, false
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class SystemSetting(BaseModel):
    """Persist a uniquely keyed system setting."""

    __tablename__ = "system_settings"

    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[dict] = mapped_column(JSON, nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)
    readonly: Mapped[bool] = mapped_column(
        nullable=False, default=False, server_default=false()
    )
