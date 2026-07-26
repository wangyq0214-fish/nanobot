"""
Student resource model.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import String, DateTime, Text, Integer, BigInteger, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from .base import Base


class StudentResource(Base):
    """
    Student resource model.

    Stores questions, files, and notes that students save to their personal resource library.
    """

    __tablename__ = "student_resources"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'question', 'file', 'note'
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)  # Question content or note content
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Uploaded file path
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # 'manual', 'course', 'homework'
    source_id: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Source ID (course question bank ID, etc.)
    category_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("student_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    metadata_extra: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Composite index for efficient queries
    __table_args__ = (
        Index("ix_student_resources_student_type", "student_id", "resource_type"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert resource to dictionary."""
        return {
            "id": self.id,
            "student_id": self.student_id,
            "resource_type": self.resource_type,
            "title": self.title,
            "content": self.content,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "category_id": self.category_id,
            "metadata": self.metadata_extra,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<StudentResource(id={self.id}, student_id={self.student_id}, type={self.resource_type})>"
