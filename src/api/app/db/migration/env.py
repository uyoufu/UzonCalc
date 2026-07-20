"""
Alembic 迁移环境
"""

from __future__ import annotations

import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

current_dir = Path(__file__).resolve().parent
api_dir = current_dir.parents[2]
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from app.db.models import Base  # noqa: E402
from app.db.migration.migrations_helper import _convert_url_to_async  # noqa: E402
from config import app_config  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option(
    "sqlalchemy.url",
    _convert_url_to_async(
        config.get_main_option("sqlalchemy.url") or app_config.get_db_connection()
    ),
)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式输出 SQL。"""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """在同步连接上执行迁移。"""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """为 CLI 场景创建异步引擎并执行迁移。"""
    configuration = config.get_section(config.config_ini_section)
    if configuration is None:
        raise RuntimeError("Unable to get Alembic configuration section")

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """在线模式执行迁移。"""
    connection = config.attributes.get("connection")
    if connection is not None:
        do_run_migrations(connection)
        return

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
