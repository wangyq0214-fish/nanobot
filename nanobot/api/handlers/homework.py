"""Homework CRUD and submission handlers."""

from __future__ import annotations

import time
from datetime import datetime

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
)


async def handle_homework_list(
    request: WsRequest,
    storage: StorageWrapper,
    course_id: str,
    *,
    identity: dict[str, str],
) -> Response:
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
    identity: dict[str, str],
) -> Response:
    role = identity.get("role", "")
    user_id = identity.get("user_id", "")
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
    query = parse_query(request.path)
    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload
    title = payload.get("title", "").strip()
    if not title:
        return http_error(400, "title is required")

    hw_id = f"hw{generate_id()}"
    now = datetime.utcnow()
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
    identity: dict[str, str],
) -> Response:
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
    identity: dict[str, str],
) -> Response:
    role = identity.get("role", "")
    user_id = identity.get("user_id", "")
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

    query = parse_query(request.path)
    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload

    answers = payload.get("answers", {})
    now = datetime.utcnow()

    if existing:
        submission_data = {
            "answers": answers,
            "status": "resubmitted",
            "submitted_at": now,
        }
        submission = await storage.update_submission(existing["id"], submission_data)
    else:
        submission_data = {
            "hw_id": hw_id,
            "course_id": course_id,
            "student_id": user_id,
            "answers": answers,
            "status": "submitted",
            "submitted_at": now,
        }
        submission = await storage.create_submission(submission_data)

    logger.info("Homework {} submitted by student {} in course {}", hw_id, user_id, course_id)
    return http_json_response({"ok": True, "submission": submission})


async def handle_homework_submissions(
    request: WsRequest,
    storage: StorageWrapper,
    course_id: str,
    hw_id: str,
    *,
    identity: dict[str, str],
) -> Response:
    role = identity.get("role", "")
    user_id = identity.get("user_id", "")
    course = await storage.get_course(course_id)
    if not course:
        return http_error(404, "Course not found")
    teacher_id = course.get("teacherId") or course.get("teacher_id", "")
    if role == "teacher" and teacher_id == user_id:
        submissions = await storage.list_submissions(hw_id)
    elif role == "student":
        sub = await storage.get_submission(hw_id, user_id)
        submissions = [sub] if sub else []
    else:
        return http_error(403, "Access denied")
    return http_json_response({"submissions": submissions})


async def handle_submission_detail(
    request: WsRequest,
    storage: StorageWrapper,
    course_id: str,
    hw_id: str,
    student_id: str,
    *,
    identity: dict[str, str],
) -> Response:
    role = identity.get("role", "")
    user_id = identity.get("user_id", "")
    if role == "student" and user_id != student_id:
        return http_error(403, "Students can only view their own submissions")
    submission = await storage.get_submission(hw_id, student_id)
    if not submission:
        return http_error(404, "Submission not found")
    return http_json_response({"submission": submission})
