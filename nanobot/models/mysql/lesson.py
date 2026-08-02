"""
Lesson models.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import String, DateTime, Text, ForeignKey, Integer, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import JSON

from .base import Base


class CourseLesson(Base):
    """
    Course lesson model.

    Represents a lesson within a course.
    """

    __tablename__ = "course_lessons"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[str] = mapped_column(String(12), ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False)
    lesson_id: Mapped[str | None] = mapped_column(String(12), ForeignKey("teacher_lessons.lesson_id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0)
    content_type: Mapped[str] = mapped_column(String(20), default="markdown")
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_extra: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    course: Mapped["Course"] = relationship(back_populates="lessons")
    teacher_lesson: Mapped[Optional["TeacherLesson"]] = relationship(back_populates="course_lessons")
    progress: Mapped[list["LearningProgress"]] = relationship(back_populates="lesson")

    def to_dict(self) -> Dict[str, Any]:
        """Convert lesson to dictionary."""
        return {
            "id": self.id,
            "course_id": self.course_id,
            "lesson_id": self.lesson_id,
            "title": self.title,
            "description": self.description,
            "order": self.order,
            "content_type": self.content_type,
            "content": self.content,
            "content_hash": self.content_hash,
            "is_custom": self.is_custom,
            "metadata": self.metadata_extra,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<CourseLesson(id={self.id}, title={self.title})>"


class TeacherLesson(Base):
    """
    Teacher lesson library model.

    Stores teacher's personal lesson templates that can be reused across courses.
    """

    __tablename__ = "teacher_lessons"

    lesson_id: Mapped[str] = mapped_column(String(12), primary_key=True)
    teacher_id: Mapped[str] = mapped_column(String(64), nullable=False)
    teacher_role: Mapped[str] = mapped_column(String(20), nullable=False, default="teacher")
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_type: Mapped[str] = mapped_column(String(20), default="markdown")
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(50), nullable=True)
    grade: Mapped[str | None] = mapped_column(String(20), nullable=True)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    use_count: Mapped[int] = mapped_column(Integer, default=0)
    metadata_extra: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    course_lessons: Mapped[list["CourseLesson"]] = relationship(back_populates="teacher_lesson")

    def to_dict(self) -> Dict[str, Any]:
        """Convert teacher lesson to dictionary."""
        return {
            "lesson_id": self.lesson_id,
            "teacher_id": self.teacher_id,
            "teacher_role": self.teacher_role,
            "title": self.title,
            "description": self.description,
            "content_type": self.content_type,
            "content": self.content,
            "content_hash": self.content_hash,
            "subject": self.subject,
            "grade": self.grade,
            "tags": self.tags,
            "is_public": self.is_public,
            "use_count": self.use_count,
            "metadata": self.metadata_extra,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<TeacherLesson(lesson_id={self.lesson_id}, title={self.title})>"
