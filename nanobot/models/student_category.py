"""
Student category model.
"""

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import String, DateTime, Text, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class StudentCategory(Base):
    """
    Student category model.

    Stores categories for organizing student's questions.
    """

    __tablename__ = "student_categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    student_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)  # Category color (e.g., '#526e5a')
    question_count: Mapped[int] = mapped_column(Integer, default=0)  # Cached count of questions in this category
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index("ix_student_categories_student", "student_id"),
        Index("ix_student_categories_student_name", "student_id", "name", unique=True),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert category to dictionary."""
        return {
            "id": self.id,
            "student_id": self.student_id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "question_count": self.question_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<StudentCategory(id={self.id}, name={self.name}, student_id={self.student_id})>"
