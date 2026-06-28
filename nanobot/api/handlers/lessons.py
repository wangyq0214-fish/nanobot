"""Lesson management handlers."""

from __future__ import annotations

from websockets.http11 import Request as WsRequest
from websockets.http11 import Response

from nanobot.storage.storage_wrapper import StorageWrapper

from ..utils import http_error, http_json_response


async def handle_lessons_list(
    request: WsRequest,
    storage: StorageWrapper,
    course_id: str,
    *,
    identity: dict[str, str],
) -> Response:
    course = await storage.get_course(course_id)
    if not course:
        return http_error(404, "Course not found")
    lessons = await storage.get_course_lessons(course_id)
    return http_json_response({"lessons": lessons})


async def handle_lesson_detail(
    request: WsRequest,
    storage: StorageWrapper,
    course_id: str,
    lesson_id: str,
    *,
    identity: dict[str, str],
) -> Response:
    course = await storage.get_course(course_id)
    if not course:
        return http_error(404, "Course not found")

    try:
        lesson_id_int = int(lesson_id)
        lesson = await storage.get_lesson(lesson_id_int)
    except ValueError:
        return http_error(400, "Invalid lesson ID")

    if not lesson:
        return http_error(404, "Lesson not found")
    return http_json_response({"lesson": lesson})
