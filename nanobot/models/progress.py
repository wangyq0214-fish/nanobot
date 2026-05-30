"""
Learning progress model.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import String, DateTime, Integer, ForeignKey, Numeric, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from .base import Base


class LearningProgress(Base):
    """
    Learning progress model.

    Tracks student progress on individual lessons.
    """

    __tablename__ = "learning_progress"
    __table_args__ = (
        UniqueConstraint("student_id", "lesson_id", name="uq_student_lesson"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[str] = mapped_column(String(64), nullable=False)
    student_role: Mapped[str] = mapped_column(String(20), nullable=False, default="student")
    course_id: Mapped[str] = mapped_column(String(12), ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False)
    lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey("course_lessons.id", ondelete="CASCADE"), nullable=False)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="not_started")
    time_spent: Mapped[int] = mapped_column(Integer, default=0)
    metadata_extra: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_accessed: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    lesson: Mapped["CourseLesson"] = relationship(back_populates="progress")

    def to_dict(self) -> Dict[str, Any]:
        """Convert learning progress to dictionary."""
        return {
            "id": self.id,
            "student_id": self.student_id,
            "student_role": self.student_role,
            "course_id": self.course_id,
            "lesson_id": self.lesson_id,
            "progress_percent": self.progress_percent,
            "status": self.status,
            "time_spent": self.time_spent,
            "metadata": self.metadata_extra,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
        }

    def __repr__(self) -> str:
        return f"<LearningProgress(student_id={self.student_id}, lesson_id={self.lesson_id}, status={self.status})>"
