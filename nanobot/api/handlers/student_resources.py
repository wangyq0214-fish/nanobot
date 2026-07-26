"""Student resource management handlers."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Optional

from loguru import logger
from websockets.http11 import Request as WsRequest
from websockets.http11 import Response

from nanobot.storage.storage_wrapper import StorageWrapper

from ..utils import (
    http_error,
    http_json_response,
    parse_mutation_data,
    parse_query,
    query_first,
)

# File upload configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.ppt', '.pptx', '.txt', '.md', '.jpg', '.jpeg', '.png', '.gif'}


async def handle_student_resources_list(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    identity: dict[str, str],
) -> Response:
    """List all resources for a student."""
    user_id = identity.get("user_id", "")
    role = identity.get("role", "")

    if role != "student":
        return http_error(403, "Only students can access their resources")

    query = parse_query(request.path)
    resource_type = query_first(query, "type") or None

    resources = await storage.list_student_resources(user_id, resource_type)
    return http_json_response({"resources": resources})


async def handle_student_resource_create(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    identity: dict[str, str],
) -> Response:
    """Create a new student resource (question favorite or note)."""
    user_id = identity.get("user_id", "")
    role = identity.get("role", "")

    if role != "student":
        return http_error(403, "Only students can create resources")

    query = parse_query(request.path)
    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload

    resource_type = payload.get("resource_type", "").strip()
    title = payload.get("title", "").strip()
    content = payload.get("content", "").strip()

    if not resource_type:
        return http_error(400, "resource_type is required")
    if resource_type not in ("question", "note", "file"):
        return http_error(400, "resource_type must be 'question', 'note', or 'file'")
    if not title:
        return http_error(400, "title is required")

    resource_data = {
        "student_id": user_id,
        "resource_type": resource_type,
        "title": title,
        "content": content,
        "source_type": payload.get("source_type", "manual"),
        "source_id": payload.get("source_id"),
        "metadata_extra": payload.get("metadata", {}),
    }

    resource = await storage.create_student_resource(resource_data)
    logger.info("Student resource created: {} by {}", resource.get("id"), user_id)
    return http_json_response({"ok": True, "resource": resource})


async def handle_student_resource_favorite(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    identity: dict[str, str],
) -> Response:
    """Favorite a question from course question bank to student resources."""
    user_id = identity.get("user_id", "")
    role = identity.get("role", "")

    if role != "student":
        return http_error(403, "Only students can favorite questions")

    query = parse_query(request.path)
    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload

    course_id = payload.get("course_id", "").strip()
    question_id = payload.get("question_id")

    if not course_id:
        return http_error(400, "course_id is required")
    if not question_id:
        return http_error(400, "question_id is required")

    # Get the question from course question bank
    try:
        qid = int(question_id)
    except ValueError:
        return http_error(400, "Invalid question ID")

    question = await storage.get_question_bank(qid)
    if not question:
        return http_error(404, "Question not found in course question bank")

    # Check if already favorited
    existing_resources = await storage.list_student_resources(user_id, "question")
    for res in existing_resources:
        if res.get("source_id") == str(qid) and res.get("source_type") == "course":
            return http_json_response({"ok": True, "resource": res, "message": "Already favorited"})

    # Create student resource from question
    resource_data = {
        "student_id": user_id,
        "resource_type": "question",
        "title": question.get("content", "")[:100],  # Use first 100 chars as title
        "content": question.get("content", ""),
        "source_type": "course",
        "source_id": str(qid),
        "metadata_extra": {
            "course_id": course_id,
            "question_type": question.get("question_type", ""),
            "options": question.get("options", []),
            "answer": question.get("answer", ""),
            "explanation": question.get("explanation", ""),
            "tags": question.get("tags", []),
        },
    }

    resource = await storage.create_student_resource(resource_data)
    logger.info("Question {} favorited by student {}", qid, user_id)
    return http_json_response({"ok": True, "resource": resource})


async def handle_student_resource_delete(
    request: WsRequest,
    storage: StorageWrapper,
    resource_id: str,
    *,
    identity: dict[str, str],
) -> Response:
    """Delete a student resource."""
    user_id = identity.get("user_id", "")
    role = identity.get("role", "")

    if role != "student":
        return http_error(403, "Only students can delete their resources")

    try:
        rid = int(resource_id)
    except ValueError:
        return http_error(400, "Invalid resource ID")

    success = await storage.delete_student_resource(rid, user_id)
    if success:
        logger.info("Student resource {} deleted by {}", rid, user_id)
        return http_json_response({"ok": True})
    return http_error(404, "Resource not found")


async def handle_student_resource_update(
    request: WsRequest,
    storage: StorageWrapper,
    resource_id: str,
    *,
    identity: dict[str, str],
) -> Response:
    """Update a student resource."""
    user_id = identity.get("user_id", "")
    role = identity.get("role", "")

    if role != "student":
        return http_error(403, "Only students can update their resources")

    try:
        rid = int(resource_id)
    except ValueError:
        return http_error(400, "Invalid resource ID")

    query = parse_query(request.path)
    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload

    update_data = {}
    for field in ("title", "content", "metadata"):
        if field in payload:
            if field == "metadata":
                update_data["metadata_extra"] = payload[field]
            else:
                update_data[field] = payload[field]

    if not update_data:
        return http_error(400, "No fields to update")

    resource = await storage.update_student_resource(rid, user_id, update_data)
    if resource:
        logger.info("Student resource {} updated by {}", rid, user_id)
        return http_json_response({"ok": True, "resource": resource})
    return http_error(404, "Resource not found")


async def handle_student_resource_upload(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    identity: dict[str, str],
) -> Response:
    """Upload a file to student resources."""
    user_id = identity.get("user_id", "")
    role = identity.get("role", "")

    if role != "student":
        return http_error(403, "Only students can upload files")

    # Parse multipart form data
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" not in content_type:
        return http_error(400, "Request must be multipart/form-data")

    # Extract boundary
    boundary = None
    for part in content_type.split(";"):
        part = part.strip()
        if part.startswith("boundary="):
            boundary = part[9:].strip('"')
            break

    if not boundary:
        return http_error(400, "Missing boundary in content-type")

    # Parse multipart body
    body = request.body if hasattr(request, 'body') else b""
    if isinstance(body, str):
        body = body.encode()

    # Simple multipart parser
    parts = body.split(f"--{boundary}".encode())
    file_data = None
    filename = None

    for part in parts:
        if b"Content-Disposition" not in part:
            continue
        if b'name="file"' not in part:
            continue

        # Extract filename
        header_end = part.find(b"\r\n\r\n")
        if header_end == -1:
            continue

        header = part[:header_end].decode(errors="ignore")
        for line in header.split("\r\n"):
            if "filename=" in line:
                filename = line.split("filename=")[1].strip('"')
                break

        # Extract file data
        file_data = part[header_end + 4:]
        if file_data.endswith(b"\r\n"):
            file_data = file_data[:-2]
        break

    if not file_data or not filename:
        return http_error(400, "No file provided")

    # Validate file extension
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return http_error(400, f"File type {ext} not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    # Validate file size
    if len(file_data) > MAX_FILE_SIZE:
        return http_error(400, f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB")

    # Generate unique filename
    unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
    upload_dir = Path("uploads") / "student_resources" / user_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / unique_filename

    # Save file
    with open(file_path, "wb") as f:
        f.write(file_data)

    # Create resource record
    resource_data = {
        "student_id": user_id,
        "resource_type": "file",
        "title": filename,
        "content": None,
        "file_path": str(file_path),
        "file_size": len(file_data),
        "mime_type": _get_mime_type(ext),
        "source_type": "upload",
        "source_id": None,
        "metadata_extra": {},
    }

    resource = await storage.create_student_resource(resource_data)
    logger.info("File uploaded: {} by student {}", filename, user_id)
    return http_json_response({"ok": True, "resource": resource})


def _get_mime_type(ext: str) -> str:
    """Get MIME type from file extension."""
    mime_types = {
        ".pdf": "application/pdf",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".ppt": "application/vnd.ms-powerpoint",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
    }
    return mime_types.get(ext, "application/octet-stream")
