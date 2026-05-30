"""Homework and Question database models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import String, DateTime, Integer, ForeignKey, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nanobot.config.schema import Base


class Homework(Base):
    """Homework assignment model."""

    __tablename__ = "homework"

    hw_id: Mapped[str] = mapped_column(String(15), primary_key=True)  # "hw" + 12 hex chars
    course_id: Mapped[str] = mapped_column(String(12), ForeignKey("courses.course_id"))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    total_points: Mapped[int] = mapped_column(Integer, default=0)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # Relationships
    course: Mapped["Course"] = relationship(back_populates="homework_assignments")  # noqa: F821
    questions: Mapped[List["Question"]] = relationship(
        back_populates="homework",
        cascade="all, delete-orphan",
    )
    submissions: Mapped[List["Submission"]] = relationship(  # noqa: F821
        back_populates="homework",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Homework(hw_id={self.hw_id!r}, title={self.title!r})>"

    def to_dict(self, include_questions: bool = True) -> dict:
        """Convert to dictionary for API responses."""
        result = {
            "hwId": self.hw_id,
            "courseId": self.course_id,
            "title": self.title,
            "description": self.description,
            "totalPoints": self.total_points,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "createdBy": self.created_by,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }
        if include_questions:
            result["questions"] = [q.to_dict() for q in self.questions]
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "Homework":
        """Create Homework from existing file-based data."""
        return cls(
            hw_id=data["hwId"],
            course_id=data["courseId"],
            title=data["title"],
            description=data.get("description"),
            total_points=data.get("totalPoints", 0),
            deadline=datetime.fromisoformat(data["deadline"]) if data.get("deadline") else None,
            created_by=data.get("createdBy", ""),
            created_at=datetime.fromisoformat(data["createdAt"]) if data.get("createdAt") else None,
        )


class Question(Base):
    """Question model for homework assignments."""

    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hw_id: Mapped[str] = mapped_column(String(15), ForeignKey("homework.hw_id"))
    question_id: Mapped[str] = mapped_column(String(20))  # e.g., "q1", "q2"
    question_type: Mapped[str] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(String(5000))
    points: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    homework: Mapped["Homework"] = relationship(back_populates="questions")

    def __repr__(self) -> str:
        return f"<Question(hw_id={self.hw_id!r}, question_id={self.question_id!r})>"

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.question_id,
            "type": self.question_type,
            "content": self.content,
            "points": self.points,
        }

    @classmethod
    def from_dict(cls, data: dict, hw_id: str) -> "Question":
        """Create Question from existing file-based data."""
        return cls(
            hw_id=hw_id,
            question_id=data["id"],
            question_type=data.get("type", "short_answer"),
            content=data["content"],
            points=data.get("points", 0),
        )
