"""
Alembic 数据库迁移工具
"""

from __future__ import annotations

import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine

from config import app_config, logger


def _convert_url_to_async(database_url: str) -> str:
    """
    将项目配置中的同步数据库 URL 转为 Alembic async env 可用的 URL。
    """
    if database_url.startswith("sqlite+aiosqlite://"):
        return database_url
    if database_url.startswith("sqlite://"):
        return database_url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return database_url


class MigrationHelper:
    """管理 Alembic 迁移。"""

    def __init__(self, migration_dir: str | None = None):
        if migration_dir is None:
            migration_dir = os.path.dirname(os.path.abspath(__file__))

        self.migration_dir = str(Path(migration_dir).resolve())
        self.alembic_ini = os.path.join(self.migration_dir, "alembic.ini")

    def _make_config(self, database_url: str | None = None) -> Config:
        config = Config(self.alembic_ini)
        config.set_main_option("script_location", self.migration_dir)
        config.set_main_option(
            "sqlalchemy.url",
            _convert_url_to_async(database_url or app_config.get_db_connection()),
        )
        return config

    def create_migration(self, message: str, autogenerate: bool = False) -> bool:
        """
        创建迁移文件。默认生成空迁移，后续手动补充 upgrade/downgrade。
        """
        try:
            command.revision(
                self._make_config(),
                message=message,
                autogenerate=autogenerate,
            )
            logger.info(f"Migration created: {message}")
            return True
        except Exception as e:
            logger.error(f"Failed to create migration: {e}")
            return False

    async def upgrade_to_head(self, engine: AsyncEngine) -> None:
        """使用现有异步引擎将数据库迁移到 head。"""
        await self.upgrade_async(engine, "head")

    async def upgrade_async(self, engine: AsyncEngine, revision: str = "head") -> None:
        """使用现有异步引擎执行迁移。"""
        async with engine.begin() as connection:
            await connection.run_sync(self._upgrade_with_connection, revision)

    def _upgrade_with_connection(
        self, connection: Connection, revision: str = "head"
    ) -> None:
        config = self._make_config()
        config.attributes["connection"] = connection
        command.upgrade(config, revision)

    def upgrade(self, revision: str = "head") -> bool:
        """
        同步入口，供命令行脚本或临时维护任务调用。
        """
        try:
            command.upgrade(self._make_config(), revision)
            logger.info(f"Migrated to {revision}")
            return True
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False

    def downgrade(self, revision: str) -> bool:
        """回滚迁移。"""
        try:
            command.downgrade(self._make_config(), revision)
            logger.info(f"Rolled back to {revision}")
            return True
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    def get_heads(self) -> list[str]:
        """获取当前迁移脚本 head。"""
        script = ScriptDirectory.from_config(self._make_config())
        return list(script.get_heads())

    def get_migration_history(self) -> list[str]:
        """获取迁移文件历史。"""
        script = ScriptDirectory.from_config(self._make_config())
        return [revision.revision for revision in script.walk_revisions()]

    def show_migrations(self) -> None:
        """显示迁移文件。"""
        versions_dir = Path(self.migration_dir) / "versions"
        if not versions_dir.exists():
            logger.info("No migrations yet")
            return

        for migration in sorted(versions_dir.glob("*.py")):
            print(f"  {migration.name}")
