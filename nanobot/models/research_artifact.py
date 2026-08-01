"""Persistent researcher-generated artifacts."""

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class ResearchArtifact(Base):
    """A structured artifact generated from researcher-owned sources."""

    __tablename__ = "research_artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_role: Mapped[str] = mapped_column(String(20), nullable=False, default="researcher")
    project_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("research_projects.id"), nullable=True, index=True)
    artifact_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="draft")
    source_refs: Mapped[list] = mapped_column(JSON, default=list)
    content: Mapped[dict] = mapped_column(JSON, default=dict)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    error_message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "userId": self.user_id,
            "userRole": self.user_role,
            "projectId": self.project_id,
            "type": self.artifact_type,
            "title": self.title,
            "status": self.status,
            "sourceRefs": self.source_refs or [],
            "content": self.content or {},
            "metadata": self.metadata_ or {},
            "errorMessage": self.error_message or "",
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_summary_dict(self) -> Dict[str, Any]:
        value = self.to_dict()
        value.pop("content", None)
        return value
