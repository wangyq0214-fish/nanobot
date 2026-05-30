"""
Storage layer for nanobot.

Provides abstract interfaces and implementations for data persistence.
Supports both file-based and database storage backends.
"""

from .base import BaseStorage
from .database_storage import DatabaseStorage
from .file_storage import FileStorage
from .factory import get_storage, init_storage

__all__ = [
    "BaseStorage",
    "DatabaseStorage",
    "FileStorage",
    "get_storage",
    "init_storage",
]
