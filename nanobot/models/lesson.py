"""Lesson database model."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, DateTime, Integer, ForeignKey, func, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nanobot.config.schema import Base


class Lesson(Base):
    """Lesson model for database storage.

    Lesson plan content is stored directly in the database (content field).
    This allows unified management and backup.
    """

    __tablename__ = "lessons"

    lesson_id: Mapped[str] = mapped_column(String(12), primary_key=True)
    course_id: Mapped[str] = mapped_column(String(12), ForeignKey("courses.course_id"))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0)
    content_type: Mapped[str] = mapped_column(String(20), default="markdown")  # markdown/video/pdf
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 教案内容
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # 内容hash
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 扩展数据JSON
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    course: Mapped["Course"] = relationship(back_populates="lessons")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Lesson(lesson_id={self.lesson_id!r}, title={self.title!r})>"

    def to_dict(self, include_content: bool = False) -> dict:
        """Convert to dictionary for API responses."""
        result = {
            "lessonId": self.lesson_id,
            "courseId": self.course_id,
            "title": self.title,
            "description": self.description,
            "order": self.order,
            "contentType": self.content_type,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_content:
            result["content"] = self.content
            result["contentHash"] = self.content_hash
        return result

    @classmethod
    def from_dict(cls, data: dict, course_id: str) -> "Lesson":
        """Create Lesson from existing file-based data."""
        return cls(
            lesson_id=data.get("lessonId", data.get("id")),
            course_id=course_id,
            title=data.get("title", data.get("name", "")),
            description=data.get("description"),
            order=data.get("order", 0),
            content_type=data.get("contentType", "markdown"),
            content=data.get("content"),
            content_hash=data.get("contentHash"),
            metadata_json=data.get("metadataJson"),
            created_at=datetime.fromisoformat(data["createdAt"]) if data.get("createdAt") else None,
            updated_at=datetime.fromisoformat(data["updatedAt"]) if data.get("updatedAt") else None,
        )
