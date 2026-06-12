"""Course CRUD handlers."""

from __future__ import annotations

import secrets
import time
from typing import Callable

from loguru import logger
from websockets.http11 import Request as WsRequest
from websockets.http11 import Response

from nanobot.storage.storage_wrapper import StorageWrapper

from ..utils import (
    generate_id,
    http_error,
    http_json_response,
    parse_mutation_data,
    parse_query,
    query_first,
)


async def _generate_join_code(storage: StorageWrapper) -> str:
    """Generate a unique 6-digit join code, checking DB for collisions."""
    for _ in range(100):
        code = f"{secrets.randbelow(1_000_000):06d}"
        existing = await storage.get_course_by_join_code(code)
        if existing is None:
            return code
    raise RuntimeError("Failed to generate unique join code")


async def handle_courses_list(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    check_token: Callable[[WsRequest], bool],
) -> Response:
    if not check_token(request):
        return http_error(401, "Unauthorized")
    query = parse_query(request.path)
    role = query_first(query, "role") or ""
    user_id = query_first(query, "user_id") or ""

    if role == "teacher":
        courses = await storage.get_teacher_courses(user_id)
    elif role == "student":
        courses = await storage.get_student_courses(user_id)
    else:
        all_courses = await storage.list_courses()
        courses = [c for c in all_courses if c.get("is_public")]
    return http_json_response({"courses": courses})


async def handle_courses_create(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    check_token: Callable[[WsRequest], bool],
) -> Response:
    if not check_token(request):
        return http_error(401, "Unauthorized")
    query = parse_query(request.path)
    role = query_first(query, "role") or ""
    user_id = query_first(query, "user_id") or ""
    logger.info("[courses_create] role={!r} user_id={!r}", role, user_id)
    if role != "teacher":
        return http_error(403, "Only teachers can create courses")
    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload
    course_name = payload.get("courseName", "").strip()
    subject = payload.get("subject", "").strip()
    grade = payload.get("grade", "").strip()
    if not course_name:
        return http_error(400, "courseName is required")

    teacher_courses = await storage.get_teacher_courses(user_id)
    if len(teacher_courses) >= 100:
        return http_error(400, "Course limit reached (max 100)")

    course_id = generate_id()
    join_code = await _generate_join_code(storage)
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    display_name = payload.get("teacherName") or user_id

    course_data = {
        "course_id": course_id,
        "course_name": course_name,
        "subject": subject,
        "grade": grade,
        "description": payload.get("description", ""),
        "teacher_id": user_id,
        "teacher_role": "teacher",
        "teacher_name": display_name,
        "join_code": join_code,
        "is_public": payload.get("isPublic", True),
        "max_members": payload.get("maxMembers", 50),
        "created_at": now,
        "updated_at": now,
    }
    course = await storage.create_course(course_data)

    await storage.add_course_member(course_id, user_id, "teacher", display_name)

    logger.info("Course created: {} ({}) by {}", course_name, course_id, user_id)
    return http_json_response({"ok": True, "course": course})


async def handle_courses_join(
    request: WsRequest,
    storage: StorageWrapper,
    *,
    check_token: Callable[[WsRequest], bool],
) -> Response:
    if not check_token(request):
        return http_error(401, "Unauthorized")
    query = parse_query(request.path)
    role = query_first(query, "role") or ""
    user_id = query_first(query, "user_id") or ""
    if role != "student":
        return http_error(403, "Only students can join courses")
    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload
    join_code = payload.get("joinCode", "").strip()
    if not join_code:
        return http_error(400, "joinCode is required")

    course = await storage.get_course_by_join_code(join_code)
    if not course:
        return http_error(404, "Invalid join code")

    course_id = course["courseId"]

    if await storage.is_course_member(course_id, user_id):
        return http_json_response({"ok": True, "course": course, "message": "Already a member"})

    members_count = await storage.get_course_members_count(course_id)
    max_members = course.get("max_members", 50)
    if members_count >= max_members:
        return http_error(400, "Course is full")

    display_name = payload.get("displayName") or user_id
    await storage.add_course_member(course_id, user_id, "student", display_name)

    logger.info("Student {} joined course {} ({})", user_id, course.get("courseName"), course_id)
    return http_json_response({"ok": True, "course": course})


async def handle_course_detail(
    request: WsRequest,
    storage: StorageWrapper,
    course_id: str,
    *,
    check_token: Callable[[WsRequest], bool],
) -> Response:
    if not check_token(request):
        return http_error(401, "Unauthorized")
    course = await storage.get_course(course_id)
    if not course:
        return http_error(404, "Course not found")
    return http_json_response({"course": course})


async def handle_course_members(
    request: WsRequest,
    storage: StorageWrapper,
    course_id: str,
    *,
    check_token: Callable[[WsRequest], bool],
) -> Response:
    if not check_token(request):
        return http_error(401, "Unauthorized")
    course = await storage.get_course(course_id)
    if not course:
        return http_error(404, "Course not found")
    members = await storage.get_course_members(course_id)
    return http_json_response({"members": members})
