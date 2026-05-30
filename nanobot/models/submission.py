"""Submission database model."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, DateTime, Integer, ForeignKey, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nanobot.config.schema import Base


class Submission(Base):
    """Student homework submission model."""

    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hw_id: Mapped[str] = mapped_column(String(15), ForeignKey("homework.hw_id"))
    student_id: Mapped[str] = mapped_column(String(64))
    student_role: Mapped[str] = mapped_column(String(20))
    course_id: Mapped[str] = mapped_column(String(12), ForeignKey("courses.course_id"))
    answers: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="submitted")  # "submitted" or "graded"
    score: Mapped[int] = mapped_column(Integer, default=0)
    total_score: Mapped[int] = mapped_column(Integer, default=0)
    feedback: Mapped[dict] = mapped_column(JSON, default=dict)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    graded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    graded_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    # Relationships
    homework: Mapped["Homework"] = relationship(back_populates="submissions")  # noqa: F821
    student: Mapped["User"] = relationship(  # noqa: F821
        back_populates="submissions",
        foreign_keys=[student_id, student_role],
        primaryjoin="and_(Submission.student_id == User.user_id, Submission.student_role == User.role)",
    )

    def __repr__(self) -> str:
        return f"<Submission(hw_id={self.hw_id!r}, student_id={self.student_id!r})>"

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "hwId": self.hw_id,
            "studentId": self.student_id,
            "courseId": self.course_id,
            "answers": self.answers,
            "submittedAt": self.submitted_at.isoformat() if self.submitted_at else None,
            "status": self.status,
            "score": self.score,
            "feedback": self.feedback,
            "totalScore": self.total_score,
            "gradedAt": self.graded_at.isoformat() if self.graded_at else None,
            "gradedBy": self.graded_by,
        }

    @classmethod
    def from_dict(cls, data: dict, course_id: str) -> "Submission":
        """Create Submission from existing file-based data."""
        return cls(
            hw_id=data["hwId"],
            student_id=data["studentId"],
            student_role="student",  # Default role
            course_id=course_id,
            answers=data.get("answers", {}),
            status=data.get("status", "submitted"),
            score=data.get("score", 0),
            total_score=data.get("totalScore", 0),
            feedback=data.get("feedback", {}),
            submitted_at=datetime.fromisoformat(data["submittedAt"]) if data.get("submittedAt") else None,
            graded_at=datetime.fromisoformat(data["gradedAt"]) if data.get("gradedAt") else None,
            graded_by=data.get("gradedBy"),
        )
