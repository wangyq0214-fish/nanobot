"""
Homework models.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import String, DateTime, Text, ForeignKey, Integer, Numeric, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import JSON

from .base import Base


class Homework(Base):
    """
    Homework model.

    Represents an assignment given to students in a course.
    """

    __tablename__ = "homework"

    hw_id: Mapped[str] = mapped_column(String(15), primary_key=True)
    course_id: Mapped[str] = mapped_column(String(12), ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_points: Mapped[int] = mapped_column(Integer, default=0)
    deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft or published
    settings: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    course: Mapped["Course"] = relationship(back_populates="homework")
    questions: Mapped[list["Question"]] = relationship(back_populates="homework")
    submissions: Mapped[list["Submission"]] = relationship(back_populates="homework")

    def to_dict(self) -> Dict[str, Any]:
        """Convert homework to dictionary."""
        settings = self.settings or {}
        return {
            "hw_id": self.hw_id,
            "course_id": self.course_id,
            "title": self.title,
            "description": self.description,
            "total_points": self.total_points,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "created_by": self.created_by,
            "status": self.status,
            "questions": settings.get("questions", []),
            "settings": settings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<Homework(hw_id={self.hw_id}, title={self.title})>"


class Question(Base):
    """
    Question model.

    Represents a question within a homework assignment.
    """

    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    hw_id: Mapped[str] = mapped_column(String(15), ForeignKey("homework.hw_id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[str] = mapped_column(String(20), nullable=False)
    question_type: Mapped[str] = mapped_column(String(30), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=0)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    options: Mapped[list | None] = mapped_column(JSON, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_extra: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    # Relationships
    homework: Mapped["Homework"] = relationship(back_populates="questions")

    def to_dict(self) -> Dict[str, Any]:
        """Convert question to dictionary."""
        return {
            "id": self.id,
            "hw_id": self.hw_id,
            "question_id": self.question_id,
            "question_type": self.question_type,
            "content": self.content,
            "points": self.points,
            "answer": self.answer,
            "options": self.options,
            "explanation": self.explanation,
            "metadata": self.metadata_extra,
        }

    def __repr__(self) -> str:
        return f"<Question(id={self.id}, question_type={self.question_type})>"


class Submission(Base):
    """
    Submission model.

    Represents a student's submission for a homework assignment.
    """

    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    hw_id: Mapped[str] = mapped_column(String(15), ForeignKey("homework.hw_id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[str] = mapped_column(String(64), nullable=False)
    student_role: Mapped[str] = mapped_column(String(20), nullable=False, default="student")
    course_id: Mapped[str] = mapped_column(String(12), ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    answers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="submitted")
    score: Mapped[int] = mapped_column(Integer, default=0)
    feedback: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    graded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    graded_by: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Relationships
    homework: Mapped["Homework"] = relationship(back_populates="submissions")

    def to_dict(self) -> Dict[str, Any]:
        """Convert submission to dictionary."""
        return {
            "id": self.id,
            "hw_id": self.hw_id,
            "student_id": self.student_id,
            "student_role": self.student_role,
            "course_id": self.course_id,
            "attempt_number": self.attempt_number,
            "answers": self.answers,
            "status": self.status,
            "score": self.score,
            "feedback": self.feedback,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "graded_at": self.graded_at.isoformat() if self.graded_at else None,
            "graded_by": self.graded_by,
        }

    def __repr__(self) -> str:
        return f"<Submission(id={self.id}, hw_id={self.hw_id}, student_id={self.student_id})>"
