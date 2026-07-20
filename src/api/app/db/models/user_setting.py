"""Per-user settings table definition."""

from sqlalchemy import ForeignKey, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class UserSetting(BaseModel):
    """Persist one named setting value for a user."""

    __tablename__ = "user_settings"
    __table_args__ = (
        UniqueConstraint("userId", "key", name="uq_user_settings_user_key"),
    )

    userId: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[dict] = mapped_column(JSON, nullable=False)
    description: Mapped[str | None] = mapped_column(nullable=True)
