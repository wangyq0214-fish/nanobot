"""
Storage layer for nanobot.

Provides abstract interfaces and implementations for data persistence.
Supports both file-based and database storage backends.
"""

from .base import BaseStorage
from .database_storage import DatabaseStorage
from .file_storage import FileStorage
from .storage_wrapper import StorageWrapper
from .factory import get_storage, init_storage

__all__ = [
    "BaseStorage",
    "DatabaseStorage",
    "FileStorage",
    "StorageWrapper",
    "get_storage",
    "init_storage",
]
