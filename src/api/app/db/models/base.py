"""Shared SQLAlchemy declarative bases and common entity columns."""

import datetime

from sqlalchemy import CHAR, DateTime, Integer, MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from .object_id import ObjectId

# 它用于自动生成数据库对象的默认名称
# 可以避免不同数据库或迁移工具中因自动生成名不一致而导致的问题
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Own the single metadata registry used by every database table."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class BaseModel(Base):
    """Provide identity and creation fields for independently addressed entities."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    oid: Mapped[str] = mapped_column(
        CHAR(24),
        nullable=False,
        unique=True,
        default=lambda: ObjectId().to_hex(),
        comment="Global 24-character hexadecimal object identifier",
    )
    createdAt: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )
