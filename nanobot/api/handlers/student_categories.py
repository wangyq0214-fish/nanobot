"""Student category management handlers."""

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
    query_first,
)


async def handle_student_categories_list(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    identity: dict[str, str],
) -> Response:
    """List all categories for a student."""
    user_id = identity.get("user_id", "")
    role = identity.get("role", "")

    if role != "student":
        return http_error(403, "Only students can access their categories")

    categories = await storage.list_student_categories(user_id)
    return http_json_response({"categories": categories})


async def handle_student_category_create(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    identity: dict[str, str],
) -> Response:
    """Create a new student category."""
    user_id = identity.get("user_id", "")
    role = identity.get("role", "")

    if role != "student":
        return http_error(403, "Only students can create categories")

    query = parse_query(request.path)
    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload

    name = payload.get("name", "").strip()
    if not name:
        return http_error(400, "Category name is required")

    # Check for duplicate name
    existing_categories = await storage.list_student_categories(user_id)
    for cat in existing_categories:
        if cat.get("name") == name:
            return http_error(409, "Category with this name already exists")

    category_data = {
        "student_id": user_id,
        "name": name,
        "description": payload.get("description", ""),
        "color": payload.get("color"),
    }

    category = await storage.create_student_category(category_data)
    logger.info("Student category created: {} by {}", category.get("id"), user_id)
    return http_json_response({"ok": True, "category": category})


async def handle_student_category_update(
    request: WsRequest,
    storage: StorageWrapper,
    category_id: str,
    *,
    identity: dict[str, str],
) -> Response:
    """Update a student category."""
    user_id = identity.get("user_id", "")
    role = identity.get("role", "")

    if role != "student":
        return http_error(403, "Only students can update their categories")

    try:
        cid = int(category_id)
    except ValueError:
        return http_error(400, "Invalid category ID")

    query = parse_query(request.path)
    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload

    update_data = {}
    for field in ("name", "description", "color"):
        if field in payload:
            update_data[field] = payload[field]

    if not update_data:
        return http_error(400, "No fields to update")

    # Check for duplicate name if updating name
    if "name" in update_data:
        existing_categories = await storage.list_student_categories(user_id)
        for cat in existing_categories:
            if cat.get("name") == update_data["name"] and cat.get("id") != cid:
                return http_error(409, "Category with this name already exists")

    category = await storage.update_student_category(cid, user_id, update_data)
    if category:
        logger.info("Student category {} updated by {}", cid, user_id)
        return http_json_response({"ok": True, "category": category})
    return http_error(404, "Category not found")


async def handle_student_category_delete(
    request: WsRequest,
    storage: StorageWrapper,
    category_id: str,
    *,
    identity: dict[str, str],
) -> Response:
    """Delete a student category. Resources in this category will be set to uncategorized."""
    user_id = identity.get("user_id", "")
    role = identity.get("role", "")

    if role != "student":
        return http_error(403, "Only students can delete their categories")

    try:
        cid = int(category_id)
    except ValueError:
        return http_error(400, "Invalid category ID")

    success = await storage.delete_student_category(cid, user_id)
    if success:
        logger.info("Student category {} deleted by {}", cid, user_id)
        return http_json_response({"ok": True})
    return http_error(404, "Category not found")


async def handle_student_resource_categorize(
    request: WsRequest,
    storage: StorageWrapper,
    resource_id: str,
    *,
    identity: dict[str, str],
) -> Response:
    """Set or update the category for a student resource."""
    user_id = identity.get("user_id", "")
    role = identity.get("role", "")

    if role != "student":
        return http_error(403, "Only students can categorize their resources")

    try:
        rid = int(resource_id)
    except ValueError:
        return http_error(400, "Invalid resource ID")

    query = parse_query(request.path)
    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload

    category_id = payload.get("category_id")

    # Validate category exists and belongs to the student
    if category_id is not None:
        try:
            cid = int(category_id)
        except ValueError:
            return http_error(400, "Invalid category ID")

        category = await storage.get_student_category(cid)
        if not category or category.get("student_id") != user_id:
            return http_error(404, "Category not found")

        category_id = cid

    # Update the resource
    resource = await storage.update_student_resource(rid, user_id, {"category_id": category_id})
    if not resource:
        return http_error(404, "Resource not found")

    # Update category question counts
    old_category_id = resource.get("category_id")
    if old_category_id:
        await storage.update_category_question_count(old_category_id)
    if category_id:
        await storage.update_category_question_count(category_id)

    logger.info("Student resource {} categorized to {} by {}", rid, category_id, user_id)
    return http_json_response({"ok": True, "resource": resource})
