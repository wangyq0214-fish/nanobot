"""Question bank management handlers."""

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


async def handle_question_bank_list(
    request: WsRequest,
    storage: StorageWrapper,
    course_id: str,
    *,
    identity: dict[str, str],
) -> Response:
    """List questions in the question bank for a course."""
    query = parse_query(request.path)

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
    identity: dict[str, str],
) -> Response:
    """Add a question to the question bank."""
    role = identity.get("role", "")
    user_id = identity.get("user_id", "")

    if role != "teacher":
        return http_error(403, "Only teachers can add to question bank")

    course = await storage.get_course(course_id)
    if not course:
        return http_error(404, "Course not found")
    teacher_id = course.get("teacherId") or course.get("teacher_id", "")
    if teacher_id != user_id:
        return http_error(403, "Only the course owner can add to question bank")

    query = parse_query(request.path)
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
    identity: dict[str, str],
) -> Response:
    """Add multiple questions to the question bank."""
    role = identity.get("role", "")
    user_id = identity.get("user_id", "")

    if role != "teacher":
        return http_error(403, "Only teachers can add to question bank")

    course = await storage.get_course(course_id)
    if not course:
        return http_error(404, "Course not found")
    teacher_id = course.get("teacherId") or course.get("teacher_id", "")
    if teacher_id != user_id:
        return http_error(403, "Only the course owner can add to question bank")

    query = parse_query(request.path)
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
    identity: dict[str, str],
) -> Response:
    """Delete a question from the question bank."""
    role = identity.get("role", "")
    user_id = identity.get("user_id", "")

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
    identity: dict[str, str],
) -> Response:
    """Update a question in the question bank."""
    role = identity.get("role", "")
    user_id = identity.get("user_id", "")

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

    query = parse_query(request.path)
    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload

    update_data = {}
    for field in ("content", "type", "points", "answer", "options", "explanation", "tags"):
        if field in payload:
            update_data[field] = payload[field]

    if not update_data:
        return http_error(400, "No fields to update")

    question = await storage.update_question_bank(qid, update_data)
    if question:
        logger.info("Question {} updated in bank in course {} by {}", qid, course_id, user_id)
        return http_json_response({"ok": True, "question": question})
    return http_error(404, "Question not found")
