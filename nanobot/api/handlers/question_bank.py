"""Question bank management handlers."""

from __future__ import annotations

from typing import Callable

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


async def handle_question_bank_list(
    request: WsRequest,
    storage: StorageWrapper,
    course_id: str,
    *,
    check_token: Callable[[WsRequest], bool],
) -> Response:
    """List questions in the question bank for a course."""
    if not check_token(request):
        return http_error(401, "Unauthorized")
    query = parse_query(request.path)
    _role = query_first(query, "role") or ""
    _user_id = query_first(query, "user_id") or ""

    course = await storage.get_course(course_id)
    if not course:
        return http_error(404, "Course not found")

    question_type = query_first(query, "type") or None
    questions = await storage.list_question_bank(course_id, question_type)
    return http_json_response({"questions": questions})


async def handle_question_bank_add(
    request: WsRequest,
    storage: StorageWrapper,
    course_id: str,
    *,
    check_token: Callable[[WsRequest], bool],
) -> Response:
    """Add a question to the question bank."""
    if not check_token(request):
        return http_error(401, "Unauthorized")
    query = parse_query(request.path)
    role = query_first(query, "role") or ""
    user_id = query_first(query, "user_id") or ""

    if role != "teacher":
        return http_error(403, "Only teachers can add to question bank")

    course = await storage.get_course(course_id)
    if not course:
        return http_error(404, "Course not found")
    teacher_id = course.get("teacherId") or course.get("teacher_id", "")
    if teacher_id != user_id:
        return http_error(403, "Only the course owner can add to question bank")

    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload

    content = payload.get("content", "").strip()
    if not content:
        return http_error(400, "content is required")

    question_data = {
        "course_id": course_id,
        "question_type": payload.get("type", "short_answer"),
        "content": content,
        "points": payload.get("points", 10),
        "answer": payload.get("answer", ""),
        "options": payload.get("options", []),
        "explanation": payload.get("explanation", ""),
        "tags": payload.get("tags", []),
        "source": payload.get("source", "manual"),
        "created_by": user_id,
    }

    question = await storage.add_to_question_bank(question_data)
    logger.info("Question added to bank in course {} by {}", course_id, user_id)
    return http_json_response({"ok": True, "question": question})


async def handle_question_bank_batch_add(
    request: WsRequest,
    storage: StorageWrapper,
    course_id: str,
    *,
    check_token: Callable[[WsRequest], bool],
) -> Response:
    """Add multiple questions to the question bank."""
    if not check_token(request):
        return http_error(401, "Unauthorized")
    query = parse_query(request.path)
    role = query_first(query, "role") or ""
    user_id = query_first(query, "user_id") or ""

    if role != "teacher":
        return http_error(403, "Only teachers can add to question bank")

    course = await storage.get_course(course_id)
    if not course:
        return http_error(404, "Course not found")
    teacher_id = course.get("teacherId") or course.get("teacher_id", "")
    if teacher_id != user_id:
        return http_error(403, "Only the course owner can add to question bank")

    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload

    questions = payload.get("questions", [])
    if not questions:
        return http_error(400, "questions array is required")

    questions_data = []
    for q in questions:
        questions_data.append({
            "course_id": course_id,
            "question_type": q.get("type", "short_answer"),
            "content": q.get("content", ""),
            "points": q.get("points", 10),
            "answer": q.get("answer", ""),
            "options": q.get("options", []),
            "explanation": q.get("explanation", ""),
            "tags": q.get("tags", []),
            "source": q.get("source", "ai"),
            "created_by": user_id,
        })

    results = await storage.batch_add_to_question_bank(questions_data)
    logger.info("Batch added {} questions to bank in course {} by {}", len(results), course_id, user_id)
    return http_json_response({"ok": True, "questions": results, "count": len(results)})


async def handle_question_bank_delete(
    request: WsRequest,
    storage: StorageWrapper,
    course_id: str,
    question_id: str,
    *,
    check_token: Callable[[WsRequest], bool],
) -> Response:
    """Delete a question from the question bank."""
    if not check_token(request):
        return http_error(401, "Unauthorized")
    query = parse_query(request.path)
    role = query_first(query, "role") or ""
    user_id = query_first(query, "user_id") or ""

    if role != "teacher":
        return http_error(403, "Only teachers can delete from question bank")

    course = await storage.get_course(course_id)
    if not course:
        return http_error(404, "Course not found")
    teacher_id = course.get("teacherId") or course.get("teacher_id", "")
    if teacher_id != user_id:
        return http_error(403, "Only the course owner can delete from question bank")

    try:
        qid = int(question_id)
    except ValueError:
        return http_error(400, "Invalid question ID")

    success = await storage.delete_from_question_bank(qid)
    if success:
        logger.info("Question {} deleted from bank in course {} by {}", qid, course_id, user_id)
        return http_json_response({"ok": True})
    return http_error(404, "Question not found")


async def handle_question_bank_update(
    request: WsRequest,
    storage: StorageWrapper,
    course_id: str,
    question_id: str,
    *,
    check_token: Callable[[WsRequest], bool],
) -> Response:
    """Update a question in the question bank."""
    if not check_token(request):
        return http_error(401, "Unauthorized")
    query = parse_query(request.path)
    role = query_first(query, "role") or ""
    user_id = query_first(query, "user_id") or ""

    if role != "teacher":
        return http_error(403, "Only teachers can update question bank")

    course = await storage.get_course(course_id)
    if not course:
        return http_error(404, "Course not found")
    teacher_id = course.get("teacherId") or course.get("teacher_id", "")
    if teacher_id != user_id:
        return http_error(403, "Only the course owner can update question bank")

    try:
        qid = int(question_id)
    except ValueError:
        return http_error(400, "Invalid question ID")

    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload

    update_data = {}
    if "type" in payload:
        update_data["question_type"] = payload["type"]
    if "content" in payload:
        update_data["content"] = payload["content"]
    if "points" in payload:
        update_data["points"] = payload["points"]
    if "answer" in payload:
        update_data["answer"] = payload["answer"]
    if "options" in payload:
        update_data["options"] = payload["options"]
    if "explanation" in payload:
        update_data["explanation"] = payload["explanation"]
    if "tags" in payload:
        update_data["tags"] = payload["tags"]

    if not update_data:
        return http_error(400, "No fields to update")

    question = await storage.update_question_bank(qid, update_data)
    if question:
        logger.info("Question {} updated in bank in course {} by {}", qid, course_id, user_id)
        return http_json_response({"ok": True, "question": question})
    return http_error(404, "Question not found")
