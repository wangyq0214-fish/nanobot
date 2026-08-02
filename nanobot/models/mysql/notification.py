"""
Notification model.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import String, DateTime, Text, Boolean, ForeignKey, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import JSON

from .base import Base


class Notification(Base):
    """
    Notification model.

    Stores notifications for users.
    """

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    user_role: Mapped[str] = mapped_column(String(20), nullable=False)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    related_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_extra: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_role": self.user_role,
            "notification_type": self.notification_type,
            "title": self.title,
            "content": self.content,
            "related_type": self.related_type,
            "related_id": self.related_id,
            "is_read": self.is_read,
            "metadata": self.metadata_extra,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, notification_type={self.notification_type}, is_read={self.is_read})>"
