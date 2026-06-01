"""
Question Bank models.

Stores questions for reuse across homework assignments.
"""

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from .base import Base


class QuestionBank(Base):
    """
    Question Bank model.

    Stores questions for a course that can be reused in homework assignments.
    """

    __tablename__ = "question_bank"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[str] = mapped_column(String(12), ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[str] = mapped_column(String(20), nullable=False)
    question_type: Mapped[str] = mapped_column(String(30), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=10)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    options: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # Tags for categorization
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)  # 'manual', 'ai', etc.
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert question to dictionary."""
        return {
            "id": self.id,
            "course_id": self.course_id,
            "question_id": self.question_id,
            "question_type": self.question_type,
            "content": self.content,
            "points": self.points,
            "answer": self.answer,
            "options": self.options,
            "explanation": self.explanation,
            "tags": self.tags,
            "source": self.source,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<QuestionBank(id={self.id}, type={self.question_type})>"
