"""
PDF text extraction and chunking service.

Uses pdfplumber for reliable text extraction with proper whitespace handling.
Adapted from ScholarMind's pdf_service for the nanobot architecture.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _normalize_text(text: str) -> str:
    """Clean whitespace noise from extracted PDF text."""
    if not text:
        return ""
    # Collapse runs of spaces/tabs (but not newlines)
    text = re.sub(r"[^\S\n]+", " ", text)
    # Reduce triple+ newlines to double
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf_text(file_path: str | Path) -> Dict[str, Any]:
    """
    Extract text from a PDF file.

    Returns:
        {
            "title": str,
            "page_count": int,
            "full_text": str,
            "pages": [{"page_num": int, "text": str}, ...]
        }
    """
    import pdfplumber

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    pages: List[Dict[str, Any]] = []
    full_text_parts: List[str] = []

    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            raw = page.extract_text() or ""
            text = _normalize_text(raw)
            pages.append({"page_num": i + 1, "text": text})
            if text:
                full_text_parts.append(text)

    full_text = "\n\n".join(full_text_parts)

    # Infer title from first non-trivial line of page 1
    title = "未命名论文"
    if pages and pages[0]["text"]:
        for line in pages[0]["text"].split("\n"):
            line = line.strip()
            if len(line) > 2:
                title = line[:200]
                break

    return {
        "title": title,
        "page_count": len(pages),
        "full_text": full_text,
        "pages": pages,
    }


def chunk_text(
    text: str,
    chunk_size: int = 800,
    overlap: int = 100,
) -> List[str]:
    """
    Split text into overlapping chunks with natural break points.

    Attempts to break at paragraph boundaries, sentence endings, or newlines.
    """
    if not text or not text.strip():
        return []

    text = text.strip()
    if len(text) <= chunk_size:
        return [text]

    chunks: List[str] = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        if end < len(text):
            # Try to find a natural break point
            best_break = end
            search_start = start + int(chunk_size * 0.5)

            # Priority 1: paragraph break
            para_break = text.rfind("\n\n", search_start, end)
            if para_break > search_start:
                best_break = para_break + 2
            else:
                # Priority 2: sentence ending
                for sep in ["。", ". ", "? ", "! ", "；", "\n"]:
                    sent_break = text.rfind(sep, search_start, end)
                    if sent_break > search_start:
                        candidate = sent_break + len(sep)
                        if candidate > best_break or best_break == end:
                            best_break = candidate
                        break

            end = best_break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move start forward, accounting for overlap
        start = max(start + 1, end - overlap)

    return chunks


def chunk_pages(
    pages: List[Dict[str, Any]],
    chunk_size: int = 800,
    overlap: int = 100,
) -> List[Dict[str, Any]]:
    """
    Generate page-aware text chunks.

    Each chunk records which page it came from, enabling evidence tracing.

    Returns:
        [{"page_number": int, "chunk_index": int, "content": str}, ...]
    """
    all_chunks: List[Dict[str, Any]] = []
    global_index = 0

    for page in pages:
        page_num = page.get("page_num", 0)
        text = page.get("text", "")
        if not text:
            continue

        page_chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        for chunk in page_chunks:
            all_chunks.append({
                "page_number": page_num,
                "chunk_index": global_index,
                "content": chunk,
            })
            global_index += 1

    # Fallback: if page-level chunking produced nothing, chunk the full text
    if not all_chunks:
        full_text = "\n\n".join(p.get("text", "") for p in pages if p.get("text"))
        if full_text:
            for i, chunk in enumerate(chunk_text(full_text, chunk_size, overlap)):
                all_chunks.append({
                    "page_number": 1,
                    "chunk_index": i,
                    "content": chunk,
                })

    return all_chunks
