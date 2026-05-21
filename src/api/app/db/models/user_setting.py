from sqlalchemy import JSON, String
from .base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column


class UserSetting(BaseModel):
    """user_settings table model"""

    __tablename__ = "user_settings"

    userId: Mapped[int]
    key: Mapped[str]
    value: Mapped[dict] = mapped_column(JSON, nullable=False)
    description: Mapped[str | None]
