"""
Database connection management.

Provides async session factory and connection utilities for PostgreSQL.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .schema import DatabaseConfig

logger = logging.getLogger(__name__)

# Global engine and session factory
_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def get_engine() -> AsyncEngine:
    """Get or create the global async engine."""
    global _engine
    if _engine is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the global session factory."""
    global _session_factory
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _session_factory


async def init_database(config: Optional[DatabaseConfig] = None) -> None:
    """
    Initialize database connection.

    Args:
        config: Database configuration. If None, uses default from schema.
    """
    global _engine, _session_factory

    if config is None:
        config = DatabaseConfig()

    logger.info(f"Connecting to database: {config.url}")

    _engine = create_async_engine(
        url=config.url,
        echo=config.echo,
        pool_size=config.pool_size,
        max_overflow=config.max_overflow,
        pool_pre_ping=True,  # Verify connections before use
    )

    _session_factory = async_sessionmaker(
        engine=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    # Test connection and create tables
    try:
        from sqlalchemy import text
        async with _engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection established successfully")

        # Auto-create tables if they don't exist
        from nanobot.models.base import Base
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            # Add annotations column if missing (migration for existing databases)
            try:
                await conn.execute(text("ALTER TABLE papers ADD COLUMN annotations TEXT DEFAULT '[]'"))
            except Exception:
                pass  # Column already exists
        logger.info("Database tables ensured")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


async def close_database() -> None:
    """Close database connection and cleanup."""
    global _engine, _session_factory

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Database connection closed")


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get an async database session.

    Usage:
        async with get_session() as session:
            # Use session for database operations
            await session.execute(...)
    """
    engine = get_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_database_health() -> dict:
    """
    Check database health status.

    Returns:
        Dictionary with health status information.
    """
    try:
        from sqlalchemy import text
        engine = get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()

            # Get connection pool stats
            pool = engine.pool
            pool_stats = {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
            }

            return {
                "status": "healthy",
                "version": version,
                "pool": pool_stats,
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }
