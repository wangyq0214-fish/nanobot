"""
Learning progress model.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import String, DateTime, Integer, ForeignKey, Numeric, Index
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
        Index("idx_progress_user", "user_id"),
        Index("idx_progress_user_lesson", "user_id", "lesson_id", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey("course_lessons.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="not_started", index=True)
    progress: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0)
    score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    time_spent: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_activity: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    extra_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship(foreign_keys=[user_id])
    lesson: Mapped["CourseLesson"] = relationship(back_populates="progress")

    def to_dict(self) -> Dict[str, Any]:
        """Convert learning progress to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "lesson_id": self.lesson_id,
            "status": self.status,
            "progress": float(self.progress) if self.progress is not None else 0.0,
            "score": float(self.score) if self.score is not None else None,
            "time_spent": self.time_spent,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "metadata": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<LearningProgress(user_id={self.user_id}, lesson_id={self.lesson_id}, status={self.status})>"
