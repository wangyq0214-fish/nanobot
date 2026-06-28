"""Paper CRUD handlers for researcher paper management."""

from __future__ import annotations

from pathlib import Path

from loguru import logger
from websockets.http11 import Request as WsRequest
from websockets.http11 import Response

from nanobot.storage.storage_wrapper import StorageWrapper

from ..utils import (
    http_error,
    http_json_response,
    parse_mutation_data,
    parse_query,
)

# Upload directory for PDF files
UPLOAD_DIR = Path.home() / ".nanobot" / "uploads" / "papers"


async def handle_list_papers(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    identity: dict[str, str],
) -> Response:
    """List all papers for the current user."""
    user_id = identity.get("user_id", "")

    papers = await storage.list_papers(user_id=user_id)
    return http_json_response({"papers": papers})


async def handle_upload_paper(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    identity: dict[str, str],
) -> Response:
    """Upload a PDF paper. Expects multipart/form-data or JSON with base64."""
    user_id = identity.get("user_id", "")
    query = parse_query(request.path)

    # Parse the data parameter (JSON with base64-encoded file)
    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload

    file_data = payload.get("fileData")  # base64-encoded PDF
    file_name = payload.get("fileName", "paper.pdf")
    title = payload.get("title", "")

    if not file_data:
        return http_error(400, "fileData is required (base64-encoded PDF)")

    try:
        import base64

        pdf_bytes = base64.b64decode(file_data)
    except Exception:
        return http_error(400, "Invalid base64 file data")

    # Save file
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    import uuid

    safe_name = f"{uuid.uuid4().hex[:12]}_{file_name}"
    file_path = UPLOAD_DIR / safe_name
    file_path.write_bytes(pdf_bytes)

    # Extract text
    try:
        from nanobot.services.pdf_service import chunk_pages, extract_pdf_text

        pdf_data = extract_pdf_text(file_path)
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        file_path.unlink(missing_ok=True)
        return http_error(500, f"PDF extraction failed: {str(e)}")

    if not title:
        title = pdf_data["title"]

    # Create paper record
    paper = await storage.create_paper({
        "title": title,
        "authors": "",
        "file_path": str(file_path),
        "file_name": file_name,
        "page_count": pdf_data["page_count"],
        "full_text": pdf_data["full_text"],
        "source": "upload",
        "user_id": user_id,
    })

    # Create chunks
    chunks = chunk_pages(pdf_data["pages"])
    chunk_dicts = [
        {"chunk_index": c["chunk_index"], "page_number": c["page_number"], "content": c["content"]}
        for c in chunks
    ]
    chunk_count = await storage.create_paper_chunks(paper["id"], chunk_dicts)

    logger.info(f"Uploaded paper {paper['id']}: {title} ({pdf_data['page_count']} pages, {chunk_count} chunks)")
    return http_json_response({
        "success": True,
        "paper": paper,
        "pageCount": pdf_data["page_count"],
        "chunkCount": chunk_count,
    })


async def handle_get_paper(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    identity: dict[str, str],
    paper_id: str,
) -> Response:
    """Get paper detail by ID."""
    try:
        pid = int(paper_id)
    except ValueError:
        return http_error(400, "Invalid paper ID")

    paper = await storage.get_paper(pid)
    if not paper:
        return http_error(404, "Paper not found")

    return http_json_response({"paper": paper})


async def handle_get_paper_pdf(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    identity: dict[str, str],
    paper_id: str,
) -> Response:
    """Serve the PDF file for a paper."""
    from websockets.datastructures import Headers as WsHeaders

    try:
        pid = int(paper_id)
    except ValueError:
        return http_error(400, "Invalid paper ID")

    paper = await storage.get_paper(pid)
    if not paper:
        return http_error(404, "Paper not found")

    file_path = paper.get("filePath", "")
    if not file_path or not Path(file_path).exists():
        return http_error(404, "PDF file not found on disk")

    pdf_bytes = Path(file_path).read_bytes()
    headers = WsHeaders([
        ("Content-Type", "application/pdf"),
        ("Content-Disposition", f'inline; filename="{paper.get("fileName", "paper.pdf")}"'),
        ("Content-Length", str(len(pdf_bytes))),
    ])
    return Response(200, "OK", headers, pdf_bytes)


async def handle_get_paper_chunks(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    identity: dict[str, str],
    paper_id: str,
) -> Response:
    """Get text chunks for a paper."""
    try:
        pid = int(paper_id)
    except ValueError:
        return http_error(400, "Invalid paper ID")

    chunks = await storage.get_paper_chunks(pid)
    return http_json_response({"chunks": chunks})


async def handle_delete_paper(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    identity: dict[str, str],
    paper_id: str,
) -> Response:
    """Delete a paper."""
    try:
        pid = int(paper_id)
    except ValueError:
        return http_error(400, "Invalid paper ID")

    # Get paper to find file path
    paper = await storage.get_paper(pid)
    if not paper:
        return http_error(404, "Paper not found")

    # Delete file if exists
    file_path = paper.get("filePath", "")
    if file_path:
        Path(file_path).unlink(missing_ok=True)

    success = await storage.delete_paper(pid)
    if success:
        return http_json_response({"success": True, "message": "Paper deleted"})
    return http_error(500, "Failed to delete paper")


async def handle_toggle_favorite(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    identity: dict[str, str],
    paper_id: str,
) -> Response:
    """Toggle paper favorite status."""
    try:
        pid = int(paper_id)
    except ValueError:
        return http_error(400, "Invalid paper ID")

    paper = await storage.get_paper(pid)
    if not paper:
        return http_error(404, "Paper not found")

    new_favorite = not paper.get("isFavorite", False)
    await storage.update_paper(pid, {"is_favorite": new_favorite})
    return http_json_response({"isFavorite": new_favorite})


async def handle_update_tags(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    identity: dict[str, str],
    paper_id: str,
) -> Response:
    """Update paper tags."""
    try:
        pid = int(paper_id)
    except ValueError:
        return http_error(400, "Invalid paper ID")

    query = parse_query(request.path)
    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload

    tags = payload.get("tags", [])
    if not isinstance(tags, list):
        return http_error(400, "tags must be a list")

    await storage.update_paper(pid, {"tags": tags})
    return http_json_response({"tags": tags})


async def handle_update_annotations(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    identity: dict[str, str],
    paper_id: str,
) -> Response:
    """Update paper annotations (highlights)."""
    try:
        pid = int(paper_id)
    except ValueError:
        return http_error(400, "Invalid paper ID")

    query = parse_query(request.path)
    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload

    annotations = payload.get("annotations", [])
    if not isinstance(annotations, list):
        return http_error(400, "annotations must be a list")

    await storage.update_paper(pid, {"annotations": annotations})
    return http_json_response({"annotations": annotations})
