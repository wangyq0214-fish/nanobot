"""
Paper and PaperChunk models for researcher paper management.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import String, DateTime, Integer, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class Paper(Base):
    """
    Paper model for storing academic papers.

    Supports both uploaded PDFs and imported papers from external sources.
    """

    __tablename__ = "papers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    authors: Mapped[str] = mapped_column(String(1000), default="")
    abstract: Mapped[str] = mapped_column(Text, default="")
    year: Mapped[int] = mapped_column(Integer, default=0)
    doi: Mapped[str] = mapped_column(String(200), default="")
    citation_count: Mapped[int] = mapped_column(Integer, default=0)
    venue: Mapped[str] = mapped_column(String(300), default="")

    # File storage
    file_path: Mapped[str] = mapped_column(String(1000), default="")
    file_name: Mapped[str] = mapped_column(String(500), default="")
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    full_text: Mapped[str] = mapped_column(Text, default="")

    # Source tracking
    source: Mapped[str] = mapped_column(String(50), default="upload")
    source_id: Mapped[str] = mapped_column(String(200), default="")
    pdf_url: Mapped[str] = mapped_column(String(1000), default="")
    url: Mapped[str] = mapped_column(String(1000), default="")

    # AI-generated content
    ai_summary: Mapped[str] = mapped_column(Text, default="")

    # User metadata
    user_id: Mapped[str] = mapped_column(String(64), default="")
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    tags: Mapped[str] = mapped_column(Text, default="[]")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    def to_dict(self) -> Dict[str, Any]:
        """Convert paper to dictionary."""
        import json
        tags = []
        try:
            tags = json.loads(self.tags) if self.tags else []
        except (json.JSONDecodeError, TypeError):
            pass

        return {
            "id": self.id,
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "year": self.year,
            "doi": self.doi,
            "citationCount": self.citation_count,
            "venue": self.venue,
            "filePath": self.file_path,
            "fileName": self.file_name,
            "pageCount": self.page_count,
            "source": self.source,
            "sourceId": self.source_id,
            "pdfUrl": self.pdf_url,
            "url": self.url,
            "aiSummary": self.ai_summary,
            "userId": self.user_id,
            "isFavorite": self.is_favorite,
            "tags": tags,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_summary_dict(self) -> Dict[str, Any]:
        """Convert paper to summary dictionary (without full_text)."""
        d = self.to_dict()
        return d

    def __repr__(self) -> str:
        return f"<Paper(id={self.id}, title={self.title[:30]}...)>"


class PaperChunk(Base):
    """
    Paper chunk model for storing text chunks with page references.

    Used for RAG retrieval and evidence tracing.
    """

    __tablename__ = "paper_chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    paper_id: Mapped[int] = mapped_column(Integer, ForeignKey("papers.id"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    page_number: Mapped[int] = mapped_column(Integer, default=0)
    content: Mapped[str] = mapped_column(Text, default="")

    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary."""
        return {
            "id": self.id,
            "paperId": self.paper_id,
            "chunkIndex": self.chunk_index,
            "pageNumber": self.page_number,
            "content": self.content,
        }

    def __repr__(self) -> str:
        return f"<PaperChunk(paper_id={self.paper_id}, page={self.page_number})>"
