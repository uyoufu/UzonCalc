"""
数据库迁移模块测试
"""

import asyncio
import sqlite3
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.db.migration import migrations_helper
from app.db.migration.migrations_helper import MigrationHelper


def _table_names(db_path: Path) -> set[str]:
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "select name from sqlite_master where type='table'"
        ).fetchall()
        return {row[0] for row in rows}
    finally:
        conn.close()


def test_upgrade_to_head_creates_sqlite_schema(tmp_path: Path):
    """空 SQLite 数据库应能通过 Alembic 创建业务表和版本表。"""

    async def run_migration(db_path: Path) -> None:
        engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
        try:
            helper = MigrationHelper()
            await helper.upgrade_to_head(engine)
        finally:
            await engine.dispose()

    db_path = tmp_path / "app.sqlite3"

    asyncio.run(run_migration(db_path))

    tables = _table_names(db_path)
    assert {
        "alembic_version",
        "users",
        "system_settings",
        "user_settings",
        "calc_report",
        "calc_report_category",
        "calc_report_archive",
        "calc_report_instance",
        "calc_report_instance_category",
        "tmp_files",
        "favorite_calc_reports",
    }.issubset(tables)


def test_upgrade_to_head_is_idempotent_for_sqlite(tmp_path: Path):
    """迁移重复执行应保持幂等。"""

    async def run_migration_twice(db_path: Path) -> str | None:
        engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
        try:
            helper = MigrationHelper()
            await helper.upgrade_to_head(engine)
            await helper.upgrade_to_head(engine)
            async with engine.connect() as conn:
                result = await conn.execute(
                    text("select version_num from alembic_version")
                )
                return result.scalar_one_or_none()
        finally:
            await engine.dispose()

    revision = asyncio.run(run_migration_twice(tmp_path / "app.sqlite3"))

    assert revision == "002_calc_report_instance"


def test_upgrade_to_head_skips_alembic_when_database_is_current(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """数据库版本已是 head 时应快速返回，不再调用 Alembic upgrade。"""

    db_path = tmp_path / "app.sqlite3"

    async def migrate_once() -> None:
        engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
        try:
            helper = MigrationHelper()
            await helper.upgrade_to_head(engine)
        finally:
            await engine.dispose()

    async def run_current_database_check() -> str | None:
        engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
        try:
            helper = MigrationHelper()
            await helper.upgrade_to_head(engine)
            async with engine.connect() as conn:
                result = await conn.execute(
                    text("select version_num from alembic_version")
                )
                return result.scalar_one_or_none()
        finally:
            await engine.dispose()

    def fail_if_called(*args, **kwargs):
        raise AssertionError("Alembic upgrade should be skipped for current database")

    asyncio.run(migrate_once())
    monkeypatch.setattr(migrations_helper.command, "upgrade", fail_if_called)

    revision = asyncio.run(run_current_database_check())

    assert revision == "002_calc_report_instance"


def test_upgrade_to_head_fails_when_legacy_table_exists_without_revision(
    tmp_path: Path,
):
    """已有业务表但没有版本记录时应严格失败，不自动 stamp。"""

    db_path = tmp_path / "legacy.sqlite3"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("create table users (id integer primary key)")
        conn.commit()
    finally:
        conn.close()

    async def run_migration() -> None:
        engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
        try:
            helper = MigrationHelper()
            await helper.upgrade_to_head(engine)
        finally:
            await engine.dispose()

    with pytest.raises(Exception):
        asyncio.run(run_migration())
