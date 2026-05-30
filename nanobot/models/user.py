"""User database model."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nanobot.config.schema import Base


class User(Base):
    """User model for database storage."""

    __tablename__ = "users"

    # Primary key: composite of role and user_id
    role: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(100))
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # Relationships
    created_courses: Mapped[List["Course"]] = relationship(  # noqa: F821
        back_populates="teacher",
        foreign_keys="[Course.teacher_id, Course.teacher_role]",
    )
    course_memberships: Mapped[List["CourseMember"]] = relationship(  # noqa: F821
        back_populates="student",
        foreign_keys="[CourseMember.user_id, CourseMember.user_role]",
    )
    submissions: Mapped[List["Submission"]] = relationship(  # noqa: F821
        back_populates="student",
        foreign_keys="[Submission.student_id, Submission.student_role]",
    )

    def __repr__(self) -> str:
        return f"<User(role={self.role!r}, user_id={self.user_id!r})>"

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "role": self.role,
            "userId": self.user_id,
            "displayName": self.display_name,
            "registeredAt": self.registered_at.isoformat() if self.registered_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Create User from existing file-based data."""
        return cls(
            role=data["role"],
            user_id=data["userId"],
            display_name=data.get("displayName", data["userId"]),
            registered_at=datetime.fromisoformat(data["registeredAt"]) if data.get("registeredAt") else None,
        )
