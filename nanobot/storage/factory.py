"""
Storage factory for managing storage backends.

Provides initialization and access to the active storage backend.
"""

import logging
import os
from pathlib import Path
from typing import Optional

from .base import BaseStorage
from .database_storage import DatabaseStorage
from .file_storage import FileStorage

logger = logging.getLogger(__name__)

# Load .env file if it exists
def _load_env_file():
    """Load .env file from project root."""
    env_file = Path(__file__).parent.parent.parent / ".env"
    if env_file.exists():
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key and key not in os.environ:
                            os.environ[key] = value
            logger.debug(f"Loaded .env file: {env_file}")
        except Exception as e:
            logger.debug(f"Failed to load .env file: {e}")

# Load .env on module import
_load_env_file()

# Global storage instance
_storage: Optional[BaseStorage] = None


async def init_storage(backend: str = "file", **kwargs) -> None:
    """
    Initialize the storage backend.

    Args:
        backend: Storage backend type ("file" or "database")
        **kwargs: Additional arguments for the storage backend
    """
    global _storage

    if backend == "file":
        from pathlib import Path
        base_path = kwargs.get("base_path")
        if base_path:
            base_path = Path(base_path)
        _storage = FileStorage(base_path=base_path)
        logger.info(f"Initialized file storage at {_storage.base_path}")

    elif backend == "database":
        from ..config.database import init_database, DatabaseConfig

        # Initialize database connection
        db_config = kwargs.get("db_config")
        if db_config is None:
            db_config = DatabaseConfig()
        await init_database(db_config)

        _storage = DatabaseStorage()
        logger.info("Initialized database storage (PostgreSQL)")

    elif backend == "mysql":
        from ..config.mysql_database import init_mysql_database, DatabaseConfig

        db_config = kwargs.get("db_config")
        if db_config is None:
            db_config = DatabaseConfig()
        await init_mysql_database(db_config)

        from .mysql_storage import MySQLStorage
        _storage = MySQLStorage()
        logger.info("Initialized MySQL database storage")

    else:
        raise ValueError(f"Unknown storage backend: {backend}")


def get_storage() -> BaseStorage:
    """
    Get the active storage backend.

    Returns:
        The active storage backend instance

    Raises:
        RuntimeError: If storage has not been initialized
    """
    global _storage
    if _storage is None:
        # Storage not initialized yet
        # If DATABASE_URL is configured, return a temporary FileStorage
        # The actual database initialization happens in auto_init_storage()
        if is_database_configured():
            logger.debug("DATABASE_URL set but storage not async-initialized yet. Using temporary file storage.")
        else:
            logger.debug("No DATABASE_URL, using file storage")
        _storage = FileStorage()
    return _storage


def is_database_configured() -> bool:
    """Check if DATABASE_URL or MYSQL_DATABASE_URL is configured."""
    import os
    return bool(os.environ.get("DATABASE_URL", "") or os.environ.get("MYSQL_DATABASE_URL", ""))

def is_mysql_configured() -> bool:
    """Check if MYSQL_DATABASE_URL is configured."""
    import os
    return bool(os.environ.get("MYSQL_DATABASE_URL", ""))


async def auto_init_storage() -> None:
    """
    Auto-initialize storage based on environment variables.
    Priority: MYSQL_DATABASE_URL > DATABASE_URL > file storage
    """
    if is_mysql_configured():
        try:
            await init_storage("mysql")
            logger.info("Auto-initialized MySQL database storage")
        except Exception as e:
            logger.warning(f"Failed to init MySQL: {e}, trying PostgreSQL...")
            if is_database_configured():
                try:
                    await init_storage("database")
                    logger.info("Falling back to PostgreSQL database storage")
                except Exception as e2:
                    logger.warning(f"Failed to init PostgreSQL: {e2}, falling back to file storage")
                    await init_storage("file")
            else:
                await init_storage("file")
    elif is_database_configured():
        try:
            await init_storage("database")
            logger.info("Auto-initialized database storage (PostgreSQL)")
        except Exception as e:
            logger.warning(f"Failed to init database: {e}, falling back to file storage")
            await init_storage("file")
    else:
        await init_storage("file")
        logger.info("Auto-initialized file storage (no DATABASE_URL)")


async def close_storage() -> None:
    """Close the storage backend and cleanup resources."""
    global _storage

    if _storage is not None:
        if isinstance(_storage, DatabaseStorage):
            from ..config.database import close_database
            await close_database()
        elif hasattr(_storage, '__class__') and _storage.__class__.__name__ == 'MySQLStorage':
            from ..config.mysql_database import close_mysql_database
            await close_mysql_database()

        _storage = None
        logger.info("Storage closed")


def get_storage_info() -> dict:
    """
    Get information about the current storage backend.

    Returns:
        Dictionary with storage backend information
    """
    storage = get_storage()
    return {
        "backend": type(storage).__name__,
        "is_database": isinstance(storage, DatabaseStorage),
        "is_file": isinstance(storage, FileStorage),
    }
