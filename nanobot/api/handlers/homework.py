"""Homework CRUD and submission handlers."""

from __future__ import annotations

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


async def handle_homework_list(
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
    homework = await storage.get_course_homework(course_id)
    return http_json_response({"homework": homework})


async def handle_homework_create(
    request: WsRequest,
    storage: StorageWrapper,
    course_id: str,
    *,
    check_token: Callable[[WsRequest], bool],
) -> Response:
    if not check_token(request):
        return http_error(401, "Unauthorized")
    query = parse_query(request.path)
    role = query_first(query, "role") or ""
    user_id = query_first(query, "user_id") or ""
    if role != "teacher":
        return http_error(403, "Only teachers can create homework")
    logger.info("[homework_create] role={!r} user_id={!r} course_id={!r}", role, user_id, course_id)
    course = await storage.get_course(course_id)
    if not course:
        return http_error(404, "Course not found")
    teacher_id = course.get("teacherId") or course.get("teacher_id", "")
    logger.info("[homework_create] teacher_id={!r}", teacher_id)
    if teacher_id != user_id:
        return http_error(403, "Only the course owner can create homework")
    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload
    title = payload.get("title", "").strip()
    if not title:
        return http_error(400, "title is required")

    hw_id = f"hw{generate_id()}"
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    status = payload.get("status", "draft")

    hw_data = {
        "hw_id": hw_id,
        "course_id": course_id,
        "title": title,
        "description": payload.get("description", ""),
        "questions": payload.get("questions", []),
        "total_points": payload.get("totalPoints", 0),
        "deadline": payload.get("deadline", ""),
        "status": status,
        "created_at": now,
        "created_by": user_id,
        "created_by_role": "teacher",
    }
    homework = await storage.create_homework(hw_data)
    logger.info("Homework created: {} in course {} by {} (status={})", title, course_id, user_id, status)
    return http_json_response({"ok": True, "homework": homework})


async def handle_homework_detail(
    request: WsRequest,
    storage: StorageWrapper,
    course_id: str,
    hw_id: str,
    *,
    check_token: Callable[[WsRequest], bool],
) -> Response:
    if not check_token(request):
        return http_error(401, "Unauthorized")
    hw = await storage.get_homework(hw_id)
    if not hw:
        return http_error(404, "Homework not found")
    return http_json_response({"homework": hw})


async def handle_homework_submit(
    request: WsRequest,
    storage: StorageWrapper,
    course_id: str,
    hw_id: str,
    *,
    check_token: Callable[[WsRequest], bool],
) -> Response:
    if not check_token(request):
        return http_error(401, "Unauthorized")
    query = parse_query(request.path)
    role = query_first(query, "role") or ""
    user_id = query_first(query, "user_id") or ""
    if role != "student":
        return http_error(403, "Only students can submit homework")
    course = await storage.get_course(course_id)
    if not course:
        return http_error(404, "Course not found")
    if not await storage.is_course_member(course_id, user_id):
        return http_error(403, "You must be enrolled in this course to submit homework")
    hw = await storage.get_homework(hw_id)
    if not hw:
        return http_error(404, "Homework not found")
    existing = await storage.get_submission(hw_id, user_id)
    if existing:
        return http_error(409, "You have already submitted this homework")

    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    submission_data = {
        "hw_id": hw_id,
        "student_id": user_id,
        "student_role": "student",
        "course_id": course_id,
        "answers": payload.get("answers", {}),
        "submitted_at": now,
        "status": "submitted",
        "score": 0,
        "feedback": {},
        "graded_at": None,
        "graded_by": None,
    }
    await storage.create_submission(submission_data)
    logger.info("Homework {} submitted by student {} in course {}", hw_id, user_id, course_id)
    return http_json_response({"ok": True})


async def handle_homework_submissions(
    request: WsRequest,
    storage: StorageWrapper,
    course_id: str,
    hw_id: str,
    *,
    check_token: Callable[[WsRequest], bool],
) -> Response:
    if not check_token(request):
        return http_error(401, "Unauthorized")
    course = await storage.get_course(course_id)
    if not course:
        return http_error(404, "Course not found")
    submissions = await storage.get_homework_submissions(hw_id)
    logger.info(
        "[homework_submissions] storage_type={}, hw_id={}, count={}, first_keys={}",
        type(storage).__name__,
        hw_id,
        len(submissions),
        list(submissions[0].keys()) if submissions else [],
    )
    return http_json_response({"submissions": submissions})


async def handle_submission_detail(
    request: WsRequest,
    storage: StorageWrapper,
    course_id: str,
    hw_id: str,
    student_id: str,
    *,
    check_token: Callable[[WsRequest], bool],
) -> Response:
    if not check_token(request):
        return http_error(401, "Unauthorized")
    submission = await storage.get_submission(hw_id, student_id)
    if not submission:
        return http_error(404, "Submission not found")
    return http_json_response({"submission": submission})
