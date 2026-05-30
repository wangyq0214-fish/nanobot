"""Course and CourseMember database models."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import String, DateTime, Boolean, Integer, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nanobot.config.schema import Base


class Course(Base):
    """Course model for database storage."""

    __tablename__ = "courses"

    course_id: Mapped[str] = mapped_column(String(12), primary_key=True)
    course_name: Mapped[str] = mapped_column(String(200))
    subject: Mapped[str] = mapped_column(String(50))
    grade: Mapped[str] = mapped_column(String(20))
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    teacher_id: Mapped[str] = mapped_column(String(64))
    teacher_role: Mapped[str] = mapped_column(String(20))
    teacher_name: Mapped[str] = mapped_column(String(100))
    join_code: Mapped[str] = mapped_column(String(6), unique=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    member_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    teacher: Mapped["User"] = relationship(  # noqa: F821
        back_populates="created_courses",
        foreign_keys=[teacher_id, teacher_role],
        primaryjoin="and_(Course.teacher_id == User.user_id, Course.teacher_role == User.role)",
    )
    members: Mapped[List["CourseMember"]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
    )
    lessons: Mapped[List["Lesson"]] = relationship(  # noqa: F821
        back_populates="course",
        cascade="all, delete-orphan",
    )
    homework_assignments: Mapped[List["Homework"]] = relationship(  # noqa: F821
        back_populates="course",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Course(course_id={self.course_id!r}, name={self.course_name!r})>"

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "courseId": self.course_id,
            "courseName": self.course_name,
            "subject": self.subject,
            "grade": self.grade,
            "description": self.description,
            "teacherId": self.teacher_id,
            "teacherName": self.teacher_name,
            "joinCode": self.join_code,
            "isPublic": self.is_public,
            "memberCount": self.member_count,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_index_dict(self) -> dict:
        """Convert to dictionary for course index."""
        return {
            "courseId": self.course_id,
            "courseName": self.course_name,
            "subject": self.subject,
            "grade": self.grade,
            "teacherId": self.teacher_id,
            "teacherName": self.teacher_name,
            "joinCode": self.join_code,
            "isPublic": self.is_public,
            "memberCount": self.member_count,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Course":
        """Create Course from existing file-based data."""
        return cls(
            course_id=data["courseId"],
            course_name=data["courseName"],
            subject=data["subject"],
            grade=data["grade"],
            description=data.get("description"),
            teacher_id=data["teacherId"],
            teacher_role="teacher",  # Default role
            teacher_name=data["teacherName"],
            join_code=data["joinCode"],
            is_public=data.get("isPublic", False),
            member_count=data.get("memberCount", 0),
            created_at=datetime.fromisoformat(data["createdAt"]) if data.get("createdAt") else None,
            updated_at=datetime.fromisoformat(data["updatedAt"]) if data.get("updatedAt") else None,
        )


class CourseMember(Base):
    """Course membership model."""

    __tablename__ = "course_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[str] = mapped_column(String(12), ForeignKey("courses.course_id"))
    user_id: Mapped[str] = mapped_column(String(64))
    user_role: Mapped[str] = mapped_column(String(20))
    display_name: Mapped[str] = mapped_column(String(100))
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # Relationships
    course: Mapped["Course"] = relationship(back_populates="members")
    student: Mapped["User"] = relationship(  # noqa: F821
        back_populates="course_memberships",
        foreign_keys=[user_id, user_role],
        primaryjoin="and_(CourseMember.user_id == User.user_id, CourseMember.user_role == User.role)",
    )

    # Ensure a user can only join a course once
    __table_args__ = (
        UniqueConstraint("course_id", "user_id", "user_role", name="uq_course_member"),
    )

    def __repr__(self) -> str:
        return f"<CourseMember(course_id={self.course_id!r}, user_id={self.user_id!r})>"

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "userId": self.user_id,
            "displayName": self.display_name,
            "joinedAt": self.joined_at.isoformat() if self.joined_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict, course_id: str) -> "CourseMember":
        """Create CourseMember from existing file-based data."""
        return cls(
            course_id=course_id,
            user_id=data["userId"],
            user_role="student",  # Default role for members
            display_name=data.get("displayName", data["userId"]),
            joined_at=datetime.fromisoformat(data["joinedAt"]) if data.get("joinedAt") else None,
        )
