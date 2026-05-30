"""
Resource model.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import String, DateTime, Text, ForeignKey, Integer, BigInteger, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from .base import Base


class CourseResource(Base):
    """
    Course resource model.

    Stores files, links, and other resources associated with courses.
    """

    __tablename__ = "course_resources"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[str] = mapped_column(String(12), ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    metadata_extra: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    course: Mapped["Course"] = relationship(back_populates="resources")

    def to_dict(self) -> Dict[str, Any]:
        """Convert resource to dictionary."""
        return {
            "id": self.id,
            "course_id": self.course_id,
            "resource_type": self.resource_type,
            "title": self.title,
            "description": self.description,
            "url": self.url,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "metadata": self.metadata_extra,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<CourseResource(id={self.id}, title={self.title}, resource_type={self.resource_type})>"
