"""
Course models.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import String, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from .base import Base


class Course(Base):
    """
    Course model.

    Represents a course created by a teacher.
    """

    __tablename__ = "courses"

    course_id: Mapped[str] = mapped_column(String(12), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    grade_level: Mapped[str] = mapped_column(String(50), nullable=False)
    teacher_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.user_id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)
    invite_code: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    teacher: Mapped["User"] = relationship(foreign_keys=[teacher_id])
    members: Mapped[list["CourseMember"]] = relationship(back_populates="course")
    lessons: Mapped[list["CourseLesson"]] = relationship(back_populates="course")
    homework: Mapped[list["Homework"]] = relationship(back_populates="course")
    resources: Mapped[list["CourseResource"]] = relationship(back_populates="course")

    def to_dict(self) -> Dict[str, Any]:
        """Convert course to dictionary."""
        return {
            "course_id": self.course_id,
            "name": self.name,
            "description": self.description,
            "subject": self.subject,
            "grade_level": self.grade_level,
            "teacher_id": self.teacher_id,
            "status": self.status,
            "invite_code": self.invite_code,
            "settings": self.settings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Course(course_id={self.course_id}, name={self.name})>"


class CourseMember(Base):
    """
    Course membership model.

    Tracks which users are members of which courses.
    """

    __tablename__ = "course_members"
    __table_args__ = (
        Index("idx_course_members_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[str] = mapped_column(String(12), ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="student")
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    course: Mapped["Course"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="course_memberships")

    def to_dict(self) -> Dict[str, Any]:
        """Convert course member to dictionary."""
        return {
            "id": self.id,
            "course_id": self.course_id,
            "user_id": self.user_id,
            "role": self.role,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
        }

    def __repr__(self) -> str:
        return f"<CourseMember(course_id={self.course_id}, user_id={self.user_id}, role={self.role})>"
