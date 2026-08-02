"""Course resource handlers — upload, list, delete."""

from __future__ import annotations

import os
from datetime import datetime

from loguru import logger
from websockets.http11 import Request as WsRequest
from websockets.http11 import Response

from nanobot.storage.storage_wrapper import StorageWrapper

from ..utils import generate_id, http_error, http_json_response, parse_mutation_data, parse_query


async def handle_resource_list(
    request: WsRequest,
    storage: StorageWrapper,
    course_id: str,
    *,
    identity: dict[str, str],
) -> Response:
    course = await storage.get_course(course_id)
    if not course:
        return http_error(404, "Course not found")
    query = parse_query(request.path)
    resource_type = query.get("type") or None
    resources = await storage.list_resources(course_id, resource_type)
    return http_json_response({"resources": resources})


async def handle_resource_create(
    request: WsRequest,
    storage: StorageWrapper,
    course_id: str,
    *,
    identity: dict[str, str],
) -> Response:
    role = identity.get("role", "")
    if role != "teacher":
        return http_error(403, "Only teachers can upload resources")
    course = await storage.get_course(course_id)
    if not course:
        return http_error(404, "Course not found")
    teacher_id = course.get("teacherId") or course.get("teacher_id", "")
    if teacher_id != identity.get("user_id", ""):
        return http_error(403, "Only the course owner can upload")

    query = parse_query(request.path)
    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload

    title = payload.get("title", "").strip()
    if not title:
        return http_error(400, "title is required")

    file_type = payload.get("type") or payload.get("fileType") or "other"
    resource_data = {
        "course_id": course_id,
        "resource_type": file_type,
        "title": title,
        "description": payload.get("description", ""),
        "url": payload.get("url", ""),
        "file_path": payload.get("filePath", ""),
        "file_size": payload.get("fileSize") or payload.get("size") or 0,
        "mime_type": payload.get("mimeType", ""),
    }
    resource = await storage.create_resource(resource_data)
    logger.info("Resource '{}' created in course {}", title, course_id)
    return http_json_response({"ok": True, "resource": resource})


async def handle_resource_delete(
    request: WsRequest,
    storage: StorageWrapper,
    course_id: str,
    resource_id: str,
    *,
    identity: dict[str, str],
) -> Response:
    role = identity.get("role", "")
    if role != "teacher":
        return http_error(403, "Only teachers can delete resources")
    success = await storage.delete_resource(int(resource_id))
    if success:
        return http_json_response({"ok": True})
    return http_error(404, "Resource not found")
