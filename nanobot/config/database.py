"""Database configuration and connection management for PostgreSQL."""

from __future__ import annotations

import os
from pathlib import Path
from typing import AsyncGenerator

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from nanobot.config.schema import Base, DatabaseConfig


# Default database URL - can be overridden via environment variable
DEFAULT_DATABASE_URL = "postgresql+asyncpg://nanobot:nanobot@localhost:5432/nanobot"


def get_database_url() -> str:
    """Get database URL from environment or use default."""
    url = os.getenv("NANOBOT_DATABASE_URL", DEFAULT_DATABASE_URL)
    logger.info("Database URL: {}", url)
    return url


def get_database_config() -> DatabaseConfig:
    """Get database configuration from environment or config file."""
    # Try to load from config file
    try:
        from nanobot.config.loader import load_config
        config = load_config()
        if config.database:
            return config.database
    except Exception:
        pass

    # Fallback to environment variables or defaults
    return DatabaseConfig(
        url=os.getenv("NANOBOT_DATABASE_URL", DEFAULT_DATABASE_URL),
        echo=os.getenv("NANOBOT_DB_ECHO", "false").lower() == "true",
        pool_size=int(os.getenv("NANOBOT_DB_POOL_SIZE", "5")),
        max_overflow=int(os.getenv("NANOBOT_DB_MAX_OVERFLOW", "10")),
    )


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self, database_url: str | None = None, config: DatabaseConfig | None = None):
        self.config = config or get_database_config()
        self.database_url = database_url or self.config.url
        self.engine = None
        self.async_session_factory = None

    async def initialize(self) -> None:
        """Initialize database engine and session factory."""
        if self.engine is not None:
            return

        self.engine = create_async_engine(
            self.database_url,
            echo=self.config.echo,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            pool_pre_ping=True,  # Verify connections before using
        )

        self.async_session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        logger.info("Database engine initialized")

    async def close(self) -> None:
        """Close database engine."""
        if self.engine is not None:
            await self.engine.dispose()
            self.engine = None
            self.async_session_factory = None
            logger.info("Database engine closed")

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session."""
        if self.async_session_factory is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def create_tables(self) -> None:
        """Create all database tables."""
        if self.engine is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")

    async def drop_tables(self) -> None:
        """Drop all database tables (use with caution!)."""
        if self.engine is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped")


# Global database manager instance
db_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database sessions."""
    async for session in db_manager.get_session():
        yield session
