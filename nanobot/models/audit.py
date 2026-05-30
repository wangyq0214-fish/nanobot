"""
Audit log model.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import String, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from .base import Base


class AuditLog(Base):
    """
    Audit log model.

    Records user actions for security and compliance.
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    table_name: Mapped[str] = mapped_column(String(50), nullable=False)
    record_id: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    old_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    new_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    user_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_role: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert audit log to dictionary."""
        return {
            "id": self.id,
            "table_name": self.table_name,
            "record_id": self.record_id,
            "action": self.action,
            "old_data": self.old_data,
            "new_data": self.new_data,
            "user_id": self.user_id,
            "user_role": self.user_role,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action}, table_name={self.table_name})>"
