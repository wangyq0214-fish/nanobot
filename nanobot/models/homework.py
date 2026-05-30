"""
Homework models.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import String, DateTime, Text, ForeignKey, Integer, Numeric, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from .base import Base


class Homework(Base):
    """
    Homework model.

    Represents an assignment given to students in a course.
    """

    __tablename__ = "homework"
    __table_args__ = (
        Index("idx_homework_course", "course_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[str] = mapped_column(String(12), ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(String(20), default="practice", index=True)
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    max_score: Mapped[int] = mapped_column(Integer, default=100)
    status: Mapped[str] = mapped_column(String(20), default="draft", index=True)
    teacher_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.user_id"), nullable=False)
    attachments: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    requirements: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    course: Mapped["Course"] = relationship(back_populates="homework")
    teacher: Mapped["User"] = relationship(foreign_keys=[teacher_id])
    questions: Mapped[list["Question"]] = relationship(back_populates="homework")
    submissions: Mapped[list["Submission"]] = relationship(back_populates="homework")

    def to_dict(self) -> Dict[str, Any]:
        """Convert homework to dictionary."""
        return {
            "id": self.id,
            "course_id": self.course_id,
            "title": self.title,
            "description": self.description,
            "type": self.type,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "max_score": self.max_score,
            "status": self.status,
            "teacher_id": self.teacher_id,
            "attachments": self.attachments,
            "requirements": self.requirements,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Homework(id={self.id}, title={self.title})>"


class Question(Base):
    """
    Question model.

    Represents a question within a homework assignment.
    """

    __tablename__ = "questions"
    __table_args__ = (
        Index("idx_questions_homework", "homework_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    homework_id: Mapped[int] = mapped_column(Integer, ForeignKey("homework.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[int] = mapped_column(Integer, default=10)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    extra_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    homework: Mapped["Homework"] = relationship(back_populates="questions")

    def to_dict(self) -> Dict[str, Any]:
        """Convert question to dictionary."""
        return {
            "id": self.id,
            "homework_id": self.homework_id,
            "type": self.type,
            "content": self.content,
            "options": self.options,
            "answer": self.answer,
            "score": self.score,
            "order_index": self.order_index,
            "metadata": self.extra_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<Question(id={self.id}, type={self.type})>"


class Submission(Base):
    """
    Submission model.

    Represents a student's submission for a homework assignment.
    """

    __tablename__ = "submissions"
    __table_args__ = (
        Index("idx_submissions_homework", "homework_id"),
        Index("idx_submissions_student", "student_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    homework_id: Mapped[int] = mapped_column(Integer, ForeignKey("homework.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    attachments: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="submitted", index=True)
    score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    graded_by: Mapped[str | None] = mapped_column(String(50), ForeignKey("users.user_id"), nullable=True)
    graded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    homework: Mapped["Homework"] = relationship(back_populates="submissions")
    student: Mapped["User"] = relationship(foreign_keys=[student_id], back_populates="submissions")
    grader: Mapped[Optional["User"]] = relationship(foreign_keys=[graded_by])

    def to_dict(self) -> Dict[str, Any]:
        """Convert submission to dictionary."""
        return {
            "id": self.id,
            "homework_id": self.homework_id,
            "student_id": self.student_id,
            "content": self.content,
            "attachments": self.attachments,
            "status": self.status,
            "score": float(self.score) if self.score is not None else None,
            "feedback": self.feedback,
            "graded_by": self.graded_by,
            "graded_at": self.graded_at.isoformat() if self.graded_at else None,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Submission(id={self.id}, homework_id={self.homework_id}, student_id={self.student_id})>"
