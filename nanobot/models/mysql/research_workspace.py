"""
Structured researcher workspace models.

These tables keep uploaded context and project metadata in the database so the
researcher workspace does not depend on Markdown blobs or browser-only state.
"""

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class ResearchProject(Base):
    """A researcher-owned project/topic bucket."""

    __tablename__ = "research_projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_role: Mapped[str] = mapped_column(String(20), nullable=False, default="researcher")
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(30), default="active")
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "userId": self.user_id,
            "userRole": self.user_role,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "metadata": self.metadata_ or {},
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


class ResearchAttachment(Base):
    """A file uploaded into a researcher workspace session."""

    __tablename__ = "research_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_role: Mapped[str] = mapped_column(String(20), nullable=False, default="researcher")
    project_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("research_projects.id"), nullable=True)
    chat_id: Mapped[str] = mapped_column(String(100), default="")
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(80), default="")
    file_path: Mapped[str] = mapped_column(String(1000), default="")
    parse_status: Mapped[str] = mapped_column(String(30), default="pending")
    summary: Mapped[str] = mapped_column(Text, default="")
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "userId": self.user_id,
            "userRole": self.user_role,
            "projectId": self.project_id,
            "chatId": self.chat_id,
            "fileName": self.file_name,
            "fileType": self.file_type,
            "filePath": self.file_path,
            "parseStatus": self.parse_status,
            "summary": self.summary,
            "metadata": self.metadata_ or {},
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


class ResearchAttachmentChunk(Base):
    """Searchable text chunk extracted from a workspace attachment."""

    __tablename__ = "research_attachment_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attachment_id: Mapped[int] = mapped_column(Integer, ForeignKey("research_attachments.id"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    page_number: Mapped[int] = mapped_column(Integer, default=0)
    sheet_name: Mapped[str] = mapped_column(String(200), default="")
    content: Mapped[str] = mapped_column(Text, default="")
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "attachmentId": self.attachment_id,
            "chunkIndex": self.chunk_index,
            "pageNumber": self.page_number,
            "sheetName": self.sheet_name,
            "content": self.content,
            "metadata": self.metadata_ or {},
        }


class LatexDraft(Base):
    """A database-backed LaTeX writing assistant draft."""

    __tablename__ = "latex_drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    user_role: Mapped[str] = mapped_column(String(20), nullable=False, default="researcher")
    project_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("research_projects.id"), nullable=True)
    chat_id: Mapped[str] = mapped_column(String(100), default="")
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="")
    current_version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "userId": self.user_id,
            "userRole": self.user_role,
            "projectId": self.project_id,
            "chatId": self.chat_id,
            "title": self.title,
            "fileName": self.file_name,
            "content": self.content,
            "currentVersion": self.current_version,
            "status": self.status,
            "tags": self.tags or [],
            "metadata": self.metadata_ or {},
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }


class LatexDraftVersion(Base):
    """A saved version of a LaTeX draft."""

    __tablename__ = "latex_draft_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    draft_id: Mapped[int] = mapped_column(Integer, ForeignKey("latex_drafts.id"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, default="")
    change_source: Mapped[str] = mapped_column(String(50), default="autosave")
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "draftId": self.draft_id,
            "versionNumber": self.version_number,
            "content": self.content,
            "changeSource": self.change_source,
            "metadata": self.metadata_ or {},
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }


class LatexCompileRecord(Base):
    """A compile attempt associated with a LaTeX draft/version."""

    __tablename__ = "latex_compile_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    draft_id: Mapped[int] = mapped_column(Integer, ForeignKey("latex_drafts.id"), nullable=False, index=True)
    version_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("latex_draft_versions.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")
    engine: Mapped[str] = mapped_column(String(50), default="xelatex")
    log: Mapped[str] = mapped_column(Text, default="")
    output_name: Mapped[str] = mapped_column(String(500), default="")
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "draftId": self.draft_id,
            "versionId": self.version_id,
            "status": self.status,
            "engine": self.engine,
            "log": self.log,
            "outputName": self.output_name,
            "metadata": self.metadata_ or {},
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }


class LatexDraftAttachment(Base):
    """Relationship between a LaTeX draft and uploaded workspace attachments."""

    __tablename__ = "latex_draft_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    draft_id: Mapped[int] = mapped_column(Integer, ForeignKey("latex_drafts.id"), nullable=False, index=True)
    attachment_id: Mapped[int] = mapped_column(Integer, ForeignKey("research_attachments.id"), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(50), default="context")
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "draftId": self.draft_id,
            "attachmentId": self.attachment_id,
            "relationType": self.relation_type,
            "metadata": self.metadata_ or {},
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }
