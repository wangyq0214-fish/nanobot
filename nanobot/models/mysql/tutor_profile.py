"""
Tutor profile model for student tutoring assistant.

Stores per-student learning画像: knowledge points mastery, error records,
and personalized learning strategies.
"""

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class TutorProfile(Base):
    """
    Tutor profile model.

    Tracks a student's learning画像 across tutoring sessions:
    - knowledge_points: mastery levels for each concept
    - error_records: history of mistakes and error types
    - strategies: personalized learning recommendations
    """

    __tablename__ = "tutor_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    knowledge_points: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=list)
    error_records: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=list)
    strategies: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=list)
    total_submissions: Mapped[int] = mapped_column(Integer, default=0)
    last_active: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    recommended_questions: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=list)
    recommended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_tutor_profiles_student_id", "student_id"),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert tutor profile to dictionary."""
        return {
            "id": self.id,
            "student_id": self.student_id,
            "knowledge_points": self.knowledge_points or [],
            "error_records": self.error_records or [],
            "strategies": self.strategies or [],
            "total_submissions": self.total_submissions,
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "recommended_questions": self.recommended_questions or [],
            "recommended_at": self.recommended_at.isoformat() if self.recommended_at else None,
        }

    def __repr__(self) -> str:
        return f"<TutorProfile(student_id={self.student_id}, submissions={self.total_submissions})>"
