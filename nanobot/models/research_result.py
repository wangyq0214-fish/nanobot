"""
ResearchResult model for storing saved AI research outputs.
"""

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import String, DateTime, Integer, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class ResearchResult(Base):
    """
    ResearchResult model for storing AI-generated research content
    saved by researchers from the workspace chat.
    """

    __tablename__ = "research_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_role: Mapped[str] = mapped_column(String(20), nullable=False, default="researcher")

    # Content. `content` is retained for backwards compatibility and display
    # fallback; structured data lives in sections/citations/attachments.
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Source tracking
    chat_id: Mapped[str] = mapped_column(String(100), default="")
    session_title: Mapped[str] = mapped_column(String(200), default="")
    source_message_id: Mapped[str] = mapped_column(String(100), default="")

    # Project and structured research data
    project_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    project_name: Mapped[str] = mapped_column(String(200), default="")
    status: Mapped[str] = mapped_column(String(30), default="saved")
    sections: Mapped[list] = mapped_column(JSON, default=list)
    citations: Mapped[list] = mapped_column(JSON, default=list)
    attachments: Mapped[list] = mapped_column(JSON, default=list)

    # Metadata
    tags: Mapped[dict] = mapped_column(JSON, default=list)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with camelCase keys."""
        return {
            "id": self.id,
            "userId": self.user_id,
            "userRole": self.user_role,
            "title": self.title,
            "content": self.content,
            "chatId": self.chat_id,
            "sessionTitle": self.session_title,
            "sourceMessageId": self.source_message_id,
            "projectId": self.project_id,
            "projectName": self.project_name,
            "status": self.status,
            "sections": self.sections or [],
            "citations": self.citations or [],
            "attachments": self.attachments or [],
            "tags": self.tags or [],
            "metadata": self.metadata_ or {},
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_summary_dict(self) -> Dict[str, Any]:
        """Convert to summary dictionary (without full content)."""
        d = self.to_dict()
        # Truncate content for list view
        content = d.get("content", "")
        d["contentPreview"] = content[:150] + "..." if len(content) > 150 else content
        d.pop("content", None)
        return d

    def __repr__(self) -> str:
        return f"<ResearchResult(id={self.id}, title={self.title[:30]}...)>"
