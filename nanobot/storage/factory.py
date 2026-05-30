"""
Storage factory for managing storage backends.

Provides initialization and access to the active storage backend.
"""

import logging
from typing import Optional

from .base import BaseStorage
from .database_storage import DatabaseStorage
from .file_storage import FileStorage

logger = logging.getLogger(__name__)

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
        logger.info("Initialized database storage")

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
        # Default to file storage if not initialized
        logger.warning("Storage not initialized, defaulting to file storage")
        _storage = FileStorage()
    return _storage


async def close_storage() -> None:
    """Close the storage backend and cleanup resources."""
    global _storage

    if _storage is not None:
        if isinstance(_storage, DatabaseStorage):
            from ..config.database import close_database
            await close_database()

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
