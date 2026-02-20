"""
Database initialization script for application startup - Async version
"""

from sqlalchemy import select

import os

from app.db.models import SystemSetting

from .manager import get_db_manager
from config.config import app_config, logger
from .migration.migrations_helper import MigrationHelper


async def init_database():
    """
    Initialize database for the application.
    This async function should be called during application startup.
    """
    logger.info("Initializing database...")

    try:
        # Get database manager
        db_manager = get_db_manager()

        # Initialize with connection URL from config
        database_url = app_config.get_db_connection()
        logger.info(f"Connecting to database: {database_url.split('://')[0]}")

        db_manager.initialize(
            database_url=database_url,
            pool_size=10,
            max_overflow=20,
            echo=False,  # Set to True to see SQL statements
            pool_pre_ping=True,  # Enable connection health check
        )

        # Check database health
        if not await db_manager.health_check():
            logger.error("Database health check failed!")
            return False

        # Create all tables (only creates new tables, doesn't modify existing)
        logger.info("Creating database tables...")
        await db_manager.create_all_tables()

        # 进行初始化
        await init_default_user()

        logger.info("Database initialization completed successfully")
        return True

    except Exception as e:
        logger.exception(f"Database initialization failed: {e}")
        return False


async def init_default_user():
    async with get_db_manager().session() as session:
        # 先获取设置

        system_settings = await session.scalar(
            select(SystemSetting).where(SystemSetting.key == "initialized_types")
        )
        types = system_settings.value if system_settings else []

        from .initializers import initializer_types

        for init_type in initializer_types:
            if init_type.__name__ not in types:
                initializer = init_type()
                await initializer.initialize(session)
                types.append(init_type.__name__)
                logger.info(f"Initialized database with {init_type.__name__}")

        # 更新设置
        if system_settings:
            system_settings.value = types
        else:
            system_settings = SystemSetting(key="initialized_types", value=types)
            session.add(system_settings)


def run_migrations():
    """
    Run pending database migrations using Alembic.
    """
    logger.info("Running database migrations...")

    try:
        migration_dir = os.path.join(os.path.dirname(__file__), "migration")

        helper = MigrationHelper(migration_dir)

        # Get current revision
        current = helper.get_current_revision()
        logger.info(f"Current database revision: {current}")

        # Run migrations to head
        if helper.upgrade("head"):
            logger.info("Migrations applied successfully")
            return True
        else:
            logger.error("Failed to apply migrations")
            return False

    except Exception as e:
        logger.error(f"Migration execution failed: {e}")
        return False


def create_migration(message: str, autogenerate: bool = True):
    """
    Create a new migration file.

    Args:
        message: Description of the migration
        autogenerate: Whether to auto-generate from model changes
    """
    logger.info(f"Creating migration: {message}")

    try:
        migration_dir = os.path.join(os.path.dirname(__file__), "migration")

        helper = MigrationHelper(migration_dir)

        if helper.create_migration(message, autogenerate=autogenerate):
            logger.info("Migration created successfully")
            helper.show_migrations()
            return True
        else:
            logger.error("Failed to create migration")
            return False

    except Exception as e:
        logger.error(f"Migration creation failed: {e}")
        return False
