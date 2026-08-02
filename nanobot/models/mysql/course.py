"""
Course models.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import String, DateTime, Text, ForeignKey, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import JSON

from .base import Base


class Course(Base):
    """
    Course model.

    Represents a course created by a teacher.
    """

    __tablename__ = "courses"

    course_id: Mapped[str] = mapped_column(String(12), primary_key=True)
    course_name: Mapped[str] = mapped_column(String(200), nullable=False)
    subject: Mapped[str] = mapped_column(String(50), nullable=False)
    grade: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Teacher info (composite foreign key)
    teacher_id: Mapped[str] = mapped_column(String(64), nullable=False)
    teacher_role: Mapped[str] = mapped_column(String(20), nullable=False, default="teacher")
    teacher_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Course settings
    join_code: Mapped[str] = mapped_column(String(6), unique=True, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    member_count: Mapped[int] = mapped_column(default=0)
    max_members: Mapped[int] = mapped_column(default=50)

    # Extended data
    metadata_extra: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    settings: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    members: Mapped[list["CourseMember"]] = relationship(back_populates="course")
    lessons: Mapped[list["CourseLesson"]] = relationship(back_populates="course")
    homework: Mapped[list["Homework"]] = relationship(back_populates="course")
    resources: Mapped[list["CourseResource"]] = relationship(back_populates="course")

    def to_dict(self) -> Dict[str, Any]:
        """Convert course to dictionary."""
        return {
            "course_id": self.course_id,
            "course_name": self.course_name,
            "subject": self.subject,
            "grade": self.grade,
            "description": self.description,
            "teacher_id": self.teacher_id,
            "teacher_role": self.teacher_role,
            "teacher_name": self.teacher_name,
            "join_code": self.join_code,
            "is_public": self.is_public,
            "member_count": self.member_count,
            "max_members": self.max_members,
            "metadata": self.metadata_extra,
            "settings": self.settings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Course(course_id={self.course_id}, course_name={self.course_name})>"


class CourseMember(Base):
    """
    Course membership model.

    Tracks which users are members of which courses.
    """

    __tablename__ = "course_members"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[str] = mapped_column(String(12), ForeignKey("courses.course_id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    user_role: Mapped[str] = mapped_column(String(20), nullable=False, default="student")
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    metadata_extra: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    course: Mapped["Course"] = relationship(back_populates="members")

    def to_dict(self) -> Dict[str, Any]:
        """Convert course member to dictionary."""
        return {
            "id": self.id,
            "course_id": self.course_id,
            "user_id": self.user_id,
            "user_role": self.user_role,
            "display_name": self.display_name,
            "metadata": self.metadata_extra,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
        }

    def __repr__(self) -> str:
        return f"<CourseMember(course_id={self.course_id}, user_id={self.user_id}, role={self.user_role})>"
