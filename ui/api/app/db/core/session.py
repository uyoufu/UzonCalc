"""
SQLAlchemy Async Session Management - Context Manager for Database Sessions
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from typing import AsyncGenerator, Optional, Callable
from contextlib import asynccontextmanager
from config import logger

# Session factory will be initialized by db manager
SessionLocal: Optional[Callable[..., AsyncSession]] = None


def init_session_factory(session_factory: async_sessionmaker):
    """
    Initialize the global async session factory.
    Should be called during application startup.

    Args:
        session_factory: async_sessionmaker instance
    """
    global SessionLocal
    SessionLocal = session_factory
    logger.info("Async session factory initialized")


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions with automatic cleanup.

    Usage:
        async with get_db_session() as session:
            # do something
            pass

    Yields:
        AsyncSession instance
    """
    if SessionLocal is None:
        raise RuntimeError(
            "Session factory not initialized. Call init_session_factory() first."
        )

    session: AsyncSession = SessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"Session error: {e}")
        raise
    finally:
        await session.close()


def get_async_session() -> AsyncSession:
    """
    Get a new asynchronous database session (not as context manager).
    You are responsible for closing the session.

    Returns:
        AsyncSession instance
    """
    if SessionLocal is None:
        raise RuntimeError(
            "Session factory not initialized. Call init_session_factory() first."
        )

    return SessionLocal()  # type: ignore
