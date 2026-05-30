"""
Lesson models.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import String, DateTime, Text, ForeignKey, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from .base import Base


class CourseLesson(Base):
    """
    Course lesson model.

    Represents a lesson within a course.
    """

    __tablename__ = "course_lessons"
    __table_args__ = (
        Index("idx_course_lessons_course", "course_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[str] = mapped_column(String(12), ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    grade_level: Mapped[str] = mapped_column(String(50), nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False, default=45)
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    plan_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    objectives: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    activities: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    assessment: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    resources: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    tags: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    teacher_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.user_id"), nullable=False)
    teacher_lesson_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("teacher_lessons.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    course: Mapped["Course"] = relationship(back_populates="lessons")
    teacher: Mapped["User"] = relationship(foreign_keys=[teacher_id])
    teacher_lesson: Mapped[Optional["TeacherLesson"]] = relationship(back_populates="course_lessons")
    progress: Mapped[list["LearningProgress"]] = relationship(back_populates="lesson")

    def to_dict(self) -> Dict[str, Any]:
        """Convert lesson to dictionary."""
        return {
            "id": self.id,
            "course_id": self.course_id,
            "title": self.title,
            "description": self.description,
            "subject": self.subject,
            "grade_level": self.grade_level,
            "duration": self.duration,
            "status": self.status,
            "order_index": self.order_index,
            "plan_content": self.plan_content,
            "objectives": self.objectives,
            "activities": self.activities,
            "assessment": self.assessment,
            "resources": self.resources,
            "tags": self.tags,
            "version": self.version,
            "teacher_id": self.teacher_id,
            "teacher_lesson_id": self.teacher_lesson_id,
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
    __table_args__ = (
        Index("idx_teacher_lessons_teacher", "teacher_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    teacher_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.user_id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    grade_level: Mapped[str] = mapped_column(String(50), nullable=False)
    duration: Mapped[int] = mapped_column(Integer, nullable=False, default=45)
    plan_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    objectives: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    activities: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    assessment: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    resources: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    tags: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    teacher: Mapped["User"] = relationship(foreign_keys=[teacher_id])
    course_lessons: Mapped[list["CourseLesson"]] = relationship(back_populates="teacher_lesson")

    def to_dict(self) -> Dict[str, Any]:
        """Convert teacher lesson to dictionary."""
        return {
            "id": self.id,
            "teacher_id": self.teacher_id,
            "title": self.title,
            "description": self.description,
            "subject": self.subject,
            "grade_level": self.grade_level,
            "duration": self.duration,
            "plan_content": self.plan_content,
            "objectives": self.objectives,
            "activities": self.activities,
            "assessment": self.assessment,
            "resources": self.resources,
            "tags": self.tags,
            "version": self.version,
            "usage_count": self.usage_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<TeacherLesson(id={self.id}, title={self.title})>"
