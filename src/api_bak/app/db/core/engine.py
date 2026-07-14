"""
SQLAlchemy Async Engine Configuration - Connection Pool Management
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_sessionmaker
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
from sqlalchemy import event
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Global engine instance (singleton pattern)
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker] = None


def _convert_url_to_async(database_url: str) -> str:
    """
    Convert synchronous database URL to async driver.
    
    Args:
        database_url: Original database URL
        
    Returns:
        Async database URL
    """
    if "sqlite" in database_url:
        # sqlite:/// -> sqlite+aiosqlite:///
        return database_url.replace("sqlite://", "sqlite+aiosqlite://")
    elif "postgresql" in database_url:
        # postgresql:// -> postgresql+asyncpg://
        return database_url.replace("postgresql://", "postgresql+asyncpg://")
    return database_url


def get_engine(
    database_url: str,
    pool_size: int = 10,
    max_overflow: int = 20,
    pool_recycle: int = 3600,
    echo: bool = False,
    pool_pre_ping: bool = True,
) -> AsyncEngine:
    """
    Get or create async SQLAlchemy engine with connection pool.

    Args:
        database_url: Database connection URL
        pool_size: Number of connections to keep in the pool
        max_overflow: Maximum overflow connections
        pool_recycle: Recycle connections after N seconds (default 1 hour)
        echo: Enable SQL echo for debugging
        pool_pre_ping: Enable connection health check before using

    Returns:
        Async SQLAlchemy Engine instance
    """
    global _engine

    if _engine is not None:
        return _engine

    # Convert URL to async driver
    async_url = _convert_url_to_async(database_url)

    # Determine pool class and connect args based on database type
    if "sqlite" in database_url:
        # SQLite with NullPool for async
        pool_class = NullPool
        engine_kwargs = {
            "connect_args": {"check_same_thread": False},
        }
    else:
        # PostgreSQL or other databases with AsyncAdaptedQueuePool
        pool_class = AsyncAdaptedQueuePool
        engine_kwargs = {
            "pool_size": pool_size,
            "max_overflow": max_overflow,
            "pool_recycle": pool_recycle,
            "pool_pre_ping": pool_pre_ping,
        }

    _engine = create_async_engine(
        async_url,
        echo=echo,
        poolclass=pool_class,
        **engine_kwargs,
    )

    # SQLite specific event listener (for sync connection)
    if "sqlite" in database_url:
        from sqlalchemy import event as sync_event
        
        @sync_event.listens_for(_engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    logger.info(f"Async database engine created: {async_url.split('://')[0]}")
    return _engine


def get_session_factory(
    database_url: str,
    pool_size: int = 10,
    max_overflow: int = 20,
    echo: bool = False,
) -> async_sessionmaker:
    """
    Get or create async SQLAlchemy session factory.

    Args:
        database_url: Database connection URL
        pool_size: Number of connections in pool
        max_overflow: Maximum overflow connections
        echo: Enable SQL echo

    Returns:
        async_sessionmaker factory
    """
    global _session_factory

    if _session_factory is not None:
        return _session_factory

    engine = get_engine(
        database_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        echo=echo,
    )

    _session_factory = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autoflush=False,
    )

    logger.info("Async session factory created")
    return _session_factory


async def dispose_engine():
    """
    Dispose the async engine connection pool.
    Call this when shutting down the application.
    """
    global _engine

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        logger.info("Async engine disposed")


def reset_session_factory():
    """
    Reset the session factory.
    Useful for testing or reconfiguration.
    """
    global _session_factory
    _session_factory = None
