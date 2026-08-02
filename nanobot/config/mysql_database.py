"""
MySQL database connection management.

Provides async session factory and connection utilities for MySQL.
Mirrors database.py but uses asyncmy driver and MySQL-compatible models.
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

_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def get_mysql_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        raise RuntimeError("MySQL database not initialized. Call init_mysql_database() first.")
    return _engine


def get_mysql_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        raise RuntimeError("MySQL database not initialized. Call init_mysql_database() first.")
    return _session_factory


async def init_mysql_database(config: Optional[DatabaseConfig] = None) -> None:
    global _engine, _session_factory

    if config is None:
        config = DatabaseConfig()

    # Use MySQL URL
    import os
    mysql_url = os.environ.get("MYSQL_DATABASE_URL", config.url)
    if not mysql_url or "mysql" not in mysql_url:
        mysql_url = "mysql+asyncmy://root@localhost:3306/cropgpt"

    logger.info(f"Connecting to MySQL: {mysql_url}")

    _engine = create_async_engine(
        url=mysql_url,
        echo=config.echo,
        pool_size=config.pool_size,
        max_overflow=config.max_overflow,
        pool_pre_ping=True,
    )

    _session_factory = async_sessionmaker(
        engine=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    try:
        from sqlalchemy import text
        async with _engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("MySQL connection established successfully")

        # Use MySQL-compatible models
        from nanobot.models.mysql import Base
        import nanobot.models.mysql  # register all models
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Ensure raw-SQL tables exist (not ORM-mapped)
        async with _engine.begin() as conn:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS exams (
                    exam_id VARCHAR(15) PRIMARY KEY,
                    course_id VARCHAR(12) NOT NULL,
                    title VARCHAR(200) NOT NULL,
                    description TEXT,
                    start_time DATETIME,
                    end_time DATETIME,
                    duration INT DEFAULT 60,
                    total_points INT DEFAULT 100,
                    status VARCHAR(20) DEFAULT 'draft',
                    created_by VARCHAR(64) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_exams_course (course_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """))
        logger.info("MySQL tables ensured")
    except Exception as e:
        logger.error(f"Failed to connect to MySQL: {e}")
        raise


async def close_mysql_database() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("MySQL connection closed")


@asynccontextmanager
async def get_mysql_session() -> AsyncGenerator[AsyncSession, None]:
    engine = get_mysql_engine()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
