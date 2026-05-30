"""
User model.
"""

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import String, DateTime, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from .base import Base


class User(Base):
    """
    User model.

    Stores user information including authentication credentials.
    Uses composite primary key (role, user_id).
    """

    __tablename__ = "users"

    # Composite primary key
    role: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)

    # Basic info
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Authentication
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    password_salt: Mapped[str] = mapped_column(String(64), nullable=False)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Security
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_login_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    login_attempts: Mapped[int] = mapped_column(default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Extended data
    profile: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary."""
        return {
            "user_id": self.user_id,
            "role": self.role,
            "display_name": self.display_name,
            "email": self.email,
            "profile": self.profile,
            "settings": self.settings,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "registered_at": self.registered_at.isoformat() if self.registered_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }

    def __repr__(self) -> str:
        return f"<User(user_id={self.user_id}, role={self.role}, display_name={self.display_name})>"
