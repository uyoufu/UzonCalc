"""
Database Manager - Central management of async database operations and initialization
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker
import logging

from .core.engine import (
    get_engine,
    get_session_factory,
    dispose_engine,
    reset_session_factory,
)
from .core.session import init_session_factory, get_db_session, get_async_session
from .models import BaseModel

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Centralized async database management.
    Handles initialization, migration, and session management.
    """

    _instance: Optional["DatabaseManager"] = None
    _engine: Optional[AsyncEngine] = None
    _session_factory: Optional[async_sessionmaker] = None
    _initialized: bool = False

    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(
        self,
        database_url: str,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_recycle: int = 3600,
        echo: bool = False,
        pool_pre_ping: bool = True,
    ) -> None:
        """
        Initialize database manager with connection parameters.
        Must be called before any database operations.

        Args:
            database_url: Database connection URL
            pool_size: Connection pool size
            max_overflow: Max overflow connections
            pool_recycle: Connection recycle time in seconds
            echo: Enable SQL logging
            pool_pre_ping: Enable connection health check
        """
        if self._initialized:
            logger.warning("Database manager already initialized")
            return

        try:
            # Initialize engine
            self._engine = get_engine(
                database_url,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_recycle=pool_recycle,
                echo=echo,
                pool_pre_ping=pool_pre_ping,
            )

            # Initialize session factory
            self._session_factory = get_session_factory(
                database_url,
                pool_size=pool_size,
                max_overflow=max_overflow,
                echo=echo,
            )

            # Initialize global session factory
            init_session_factory(self._session_factory)

            self._initialized = True
            logger.info("DatabaseManager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize DatabaseManager: {e}")
            raise

    @property
    def engine(self) -> AsyncEngine:
        """Get the async SQLAlchemy engine"""
        if self._engine is None:
            raise RuntimeError(
                "DatabaseManager not initialized. Call initialize() first."
            )
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker:
        """Get the async session factory"""
        if self._session_factory is None:
            raise RuntimeError(
                "DatabaseManager not initialized. Call initialize() first."
            )
        return self._session_factory

    async def create_all_tables(self) -> None:
        """
        Create all tables defined in models.
        Should only be called during initial setup or migrations.
        """
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(BaseModel.metadata.create_all)
            logger.info("All tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise

    async def drop_all_tables(self) -> None:
        """
        Drop all tables.
        WARNING: This will delete all data! Use with caution.
        """
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(BaseModel.metadata.drop_all)
            logger.info("All tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            raise

    async def health_check(self) -> bool:
        """
        Check if database connection is healthy.

        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            from sqlalchemy import text

            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                logger.info("Database health check passed")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    def get_session(self):
        """
        Get a new async database session.
        Remember to close it after use or use context manager.

        Returns:
            AsyncSession instance
        """
        return get_async_session()

    def session(self):
        """
        Async context manager for database sessions.

        Usage:
            async with db_manager.session() as session:
                # do something
                pass

        Returns:
            Async context manager yielding an AsyncSession
        """
        return get_db_session()

    async def shutdown(self) -> None:
        """
        Shutdown database manager and cleanup resources.
        Should be called during application shutdown.
        """
        try:
            await dispose_engine()
            reset_session_factory()
            self._engine = None
            self._session_factory = None
            self._initialized = False
            logger.info("DatabaseManager shutdown successfully")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            raise

    @classmethod
    def get_instance(cls) -> "DatabaseManager":
        """Get the singleton instance"""
        return cls()


# Convenience function for getting the manager
def get_db_manager() -> DatabaseManager:
    """Get the DatabaseManager singleton instance"""
    return DatabaseManager.get_instance()
