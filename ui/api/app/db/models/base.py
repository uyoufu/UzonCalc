"""
Base Model Class - Common fields and functionality for all models

Converted to SQLAlchemy 2.0 style using `DeclarativeBase`, `Mapped`, and
`mapped_column` so IDEs and type-checkers can provide better type hints.
"""

import datetime
from typing import Any

from sqlalchemy import String, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .object_id import ObjectId


class BaseModel(DeclarativeBase):
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True, index=True
    )
    oid: Mapped[str] = mapped_column(
        String(24),
        nullable=False,
        index=True,
        default=lambda: ObjectId().to_hex(),
    )
    createdAt: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
        index=True,
    )
