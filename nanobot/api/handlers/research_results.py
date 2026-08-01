"""Research result CRUD handlers for researcher saved AI outputs."""

from __future__ import annotations

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


async def handle_list_research_results(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    identity: dict[str, str],
) -> Response:
    """List all research results for the current user."""
    user_id = identity.get("user_id", "")
    role = identity.get("role", "researcher")

    if role != "researcher":
        return http_error(403, "Only researchers can access research results")

    results = await storage.list_research_results(user_id, role)
    return http_json_response({"ok": True, "data": results})


async def handle_create_research_result(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    identity: dict[str, str],
) -> Response:
    """Create a new research result from AI chat output."""
    user_id = identity.get("user_id", "")
    role = identity.get("role", "researcher")

    if role != "researcher":
        return http_error(403, "Only researchers can save research results")

    query = parse_query(request.path)
    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload

    content = str(payload.get("content", "")).strip()
    if not content:
        return http_error(400, "content is required")

    project_id = _optional_int(payload.get("projectId"))
    if project_id is not None and await storage.get_research_project(project_id, user_id, role) is None:
        return http_error(403, "Project does not belong to the current researcher")
    result_data = {
        "user_id": user_id,
        "user_role": role,
        "title": str(payload.get("title") or _extract_title(content)).strip(),
        "content": content,
        "chat_id": payload.get("chatId", ""),
        "session_title": payload.get("sessionTitle", ""),
        "source_message_id": payload.get("sourceMessageId", ""),
        "project_id": project_id,
        "project_name": str(payload.get("projectName", "")).strip(),
        "status": payload.get("status", "saved"),
        "sections": _ensure_list(payload.get("sections")),
        "citations": _ensure_list(payload.get("citations")),
        "attachments": _ensure_list(payload.get("attachments")),
        "resources": _ensure_list(payload.get("resources")),
        "tags": payload.get("tags", []),
        "metadata": payload.get("metadata", {}),
    }

    result = await storage.create_research_result(result_data)

    logger.info(f"User {user_id} saved research result: {result.get('id')}")
    return http_json_response({"ok": True, "data": result})


async def handle_get_research_result(
    request: WsRequest,
    storage: StorageWrapper,
    result_id: str,
    *,
    identity: dict[str, str],
) -> Response:
    """Get a single research result by ID with full content."""
    user_id = identity.get("user_id", "")
    role = identity.get("role", "researcher")

    if role != "researcher":
        return http_error(403, "Only researchers can access research results")

    result = await storage.get_research_result(int(result_id))
    if not result:
        return http_error(404, "Research result not found")

    # Check ownership
    if not _owns(result, identity):
        return http_error(403, "Access denied")

    return http_json_response({"ok": True, "data": result})


async def handle_delete_research_result(
    request: WsRequest,
    storage: StorageWrapper,
    result_id: str,
    *,
    identity: dict[str, str],
) -> Response:
    """Delete a research result."""
    user_id = identity.get("user_id", "")
    role = identity.get("role", "researcher")

    if role != "researcher":
        return http_error(403, "Only researchers can delete research results")

    # Check ownership before deleting
    result = await storage.get_research_result(int(result_id))
    if not result:
        return http_error(404, "Research result not found")

    owner_id = result.get("userId") or result.get("user_id")
    if owner_id != user_id or (result.get("userRole") or result.get("user_role") or "researcher") != role:
        return http_error(403, "Access denied")

    deleted = await storage.delete_research_result(int(result_id))
    if not deleted:
        return http_error(500, "Failed to delete research result")

    logger.info(f"User {user_id} deleted research result: {result_id}")
    return http_json_response({"ok": True})


def _ensure_list(value: object) -> list:
    """Normalize structured payload fields to lists."""
    return value if isinstance(value, list) else []


def _optional_int(value: object) -> int | None:
    """Parse an optional integer field."""
    if value in (None, ""):
        return None
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


async def handle_update_research_result(
    request: WsRequest,
    storage: StorageWrapper,
    result_id: str,
    *,
    identity: dict[str, str],
) -> Response:
    """Update a research result (title, tags)."""
    user_id = identity.get("user_id", "")
    role = identity.get("role", "researcher")

    if role != "researcher":
        return http_error(403, "Only researchers can update research results")

    # Check ownership
    result = await storage.get_research_result(int(result_id))
    if not result:
        return http_error(404, "Research result not found")

    owner_id = result.get("userId") or result.get("user_id")
    if owner_id != user_id or (result.get("userRole") or result.get("user_role") or "researcher") != role:
        return http_error(403, "Access denied")

    query = parse_query(request.path)
    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload

    if "projectId" in payload:
        project_id = _optional_int(payload.get("projectId"))
        if project_id is not None and await storage.get_research_project(project_id, user_id, role) is None:
            return http_error(403, "Project does not belong to the current researcher")
        payload = {**payload, "project_id": project_id}
    updated = await storage.update_research_result(int(result_id), payload)
    if not updated:
        return http_error(500, "Failed to update research result")

    return http_json_response({"ok": True})


def _extract_title(content: str, max_len: int = 60) -> str:
    """Extract a title from AI content.

    Takes the first meaningful line or first N characters.
    """
    # Try to find first heading
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("#"):
            title = line.lstrip("#").strip()
            if title:
                return title[:max_len]

    # Try to find first non-empty line
    for line in content.split("\n"):
        line = line.strip()
        if line and len(line) > 5:
            # Remove markdown formatting
            title = line.replace("**", "").replace("*", "").replace("`", "")
            return title[:max_len] + ("..." if len(title) > max_len else "")

    # Fallback: first N characters
    clean = content.replace("\n", " ").strip()
    return clean[:max_len] + ("..." if len(clean) > max_len else "")


def _owns(result: dict | None, identity: dict[str, str]) -> bool:
    return bool(result and (result.get("userId") or result.get("user_id")) == identity.get("user_id") and (result.get("userRole") or result.get("user_role") or "researcher") == identity.get("role", "researcher"))
