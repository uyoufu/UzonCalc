from sqlalchemy import JSON, String
from .base import BaseModel
from sqlalchemy.orm import Mapped, mapped_column


class FavoriteCalcReport(BaseModel):
    """favorite_calc_reports table model"""

    __tablename__ = "favorite_calc_reports"

    userId: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    