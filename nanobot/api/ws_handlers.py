"""WebSocket envelope dispatch handlers.

Extracted from ``WebSocketChannel._dispatch_envelope`` to keep the
channel class focused on connection plumbing.  Each handler receives
the channel instance so it can call ``_send_event``, ``_attach``, etc.
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any

from loguru import logger


def _get_conn_meta(channel: Any, connection: Any) -> dict[str, Any]:
    """Return connection metadata dict (role, user_id, etc.)."""
    return getattr(channel, "_conn_metadata", {}).get(connection, {})


async def _err(channel: Any, connection: Any, detail: str, **kw: Any) -> None:
    """Shorthand for sending an error event."""
    await channel._send_event(connection, "error", detail=detail, **kw)


# -- Individual envelope handlers ------------------------------------------


async def handle_new_chat(channel: Any, connection: Any, _envelope: dict[str, Any]) -> None:
    new_id = str(uuid.uuid4())
    channel._attach(connection, new_id)
    await channel._send_event(connection, "attached", chat_id=new_id)


async def handle_attach(channel: Any, connection: Any, envelope: dict[str, Any]) -> None:
    from nanobot.channels.websocket import _is_valid_chat_id

    cid = envelope.get("chat_id")
    if not _is_valid_chat_id(cid):
        await _err(channel, connection, "invalid chat_id")
        return
    channel._attach(connection, cid)
    await channel._send_event(connection, "attached", chat_id=cid)


async def handle_message(
    channel: Any,
    connection: Any,
    envelope: dict[str, Any],
    *,
    client_id: str,
) -> None:
    from nanobot.channels.websocket import _is_valid_chat_id

    cid = envelope.get("chat_id")
    content = envelope.get("content")
    if not _is_valid_chat_id(cid):
        await _err(channel, connection, "invalid chat_id")
        return
    if not isinstance(content, str):
        await _err(channel, connection, "missing content")
        return

    raw_media = envelope.get("media")
    media_paths: list[str] = []
    if raw_media is not None:
        if not isinstance(raw_media, list):
            await _err(channel, connection, "image_rejected", reason="malformed")
            return
        media_paths, reason = channel._save_envelope_media(raw_media)
        if reason is not None:
            await _err(channel, connection, "image_rejected", reason=reason)
            return

    # Allow image-only turns (content may be empty when media is attached).
    if not content.strip() and not media_paths:
        await _err(channel, connection, "missing content")
        return

    # Auto-attach on first use so clients can one-shot without a separate attach.
    channel._attach(connection, cid)
    msg_meta: dict[str, Any] = {"remote": getattr(connection, "remote_address", None)}
    conn_meta = _get_conn_meta(channel, connection)
    msg_meta.update(conn_meta)
    logger.debug("WS message: conn_meta={}, msg_meta={}", conn_meta, msg_meta)
    await channel._handle_message(
        sender_id=client_id,
        chat_id=cid,
        content=content,
        media=media_paths or None,
        metadata=msg_meta,
    )


async def handle_save_source(
    channel: Any,
    connection: Any,
    envelope: dict[str, Any],
) -> None:
    path = envelope.get("path")
    content = envelope.get("content")
    if not path or not isinstance(path, str):
        await _err(channel, connection, "missing path")
        return
    if not isinstance(content, str):
        await _err(channel, connection, "missing content")
        return
    conn_meta = _get_conn_meta(channel, connection)
    role = conn_meta.get("role", "")
    user_id = conn_meta.get("user_id", "")
    if not role or not user_id:
        await _err(channel, connection, "not authenticated")
        return
    if ".." in path:
        await _err(channel, connection, "invalid path")
        return
    source_dir = Path.home() / ".nanobot" / "users" / role / user_id / "source"
    target = (source_dir / path).resolve()
    if not str(target).startswith(str(source_dir.resolve())):
        await _err(channel, connection, "access denied")
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    await channel._send_event(connection, "source_saved", path=path)


async def handle_ai_grade_question_ws(
    channel: Any,
    connection: Any,
    envelope: dict[str, Any],
) -> None:
    from nanobot.api.ai_grade import grade_single_question

    request_id = envelope.get("request_id", "")
    content = envelope.get("content", "")
    max_score = envelope.get("max_score", 10)
    reference_answer = envelope.get("reference_answer", "")
    student_answer = envelope.get("student_answer", "")
    if not content:
        await channel._send_event(
            connection, "ai_grade_question_result",
            request_id=request_id, error="missing content",
        )
        return

    conn_meta = _get_conn_meta(channel, connection)
    role = conn_meta.get("role") or envelope.get("role", "")
    if role != "teacher":
        await channel._send_event(
            connection, "ai_grade_question_result",
            request_id=request_id, error="Only teachers can use AI grading",
        )
        return

    try:
        result = await grade_single_question(
            question_content=content,
            max_score=max_score,
            reference_answer=reference_answer,
            student_answer=student_answer,
        )
        await channel._send_event(
            connection, "ai_grade_question_result",
            request_id=request_id,
            score=result["score"],
            comment=result["comment"],
        )
    except Exception as e:
        logger.error("[ws] ai_grade_question failed: {}", e)
        await channel._send_event(
            connection, "ai_grade_question_result",
            request_id=request_id, error=str(e),
        )


async def handle_ai_grade_submission_ws(
    channel: Any,
    connection: Any,
    envelope: dict[str, Any],
) -> None:
    from datetime import datetime, timezone

    from nanobot.api.ai_grade import grade_submission

    request_id = envelope.get("request_id", "")
    course_id = envelope.get("course_id", "")
    hw_id = envelope.get("hw_id", "")
    student_id = envelope.get("student_id", "")
    if not all([course_id, hw_id, student_id]):
        await channel._send_event(
            connection, "ai_grade_submission_result",
            request_id=request_id, error="missing parameters",
        )
        return

    try:
        conn_meta = _get_conn_meta(channel, connection)
        user_id = conn_meta.get("user_id") or envelope.get("user_id", "")

        course = await channel.storage.get_course(course_id)
        if not course:
            await channel._send_event(
                connection, "ai_grade_submission_result",
                request_id=request_id, error="Course not found",
            )
            return
        teacher_id = course.get("teacherId") or course.get("teacher_id", "")
        if teacher_id != user_id:
            await channel._send_event(
                connection, "ai_grade_submission_result",
                request_id=request_id, error="Only the course owner can AI grade",
            )
            return

        submission = await channel.storage.get_submission(hw_id, student_id)
        if not submission:
            await channel._send_event(
                connection, "ai_grade_submission_result",
                request_id=request_id, error="Submission not found",
            )
            return

        hw = await channel.storage.get_homework(hw_id)
        if not hw:
            await channel._send_event(
                connection, "ai_grade_submission_result",
                request_id=request_id, error="Homework not found",
            )
            return

        settings = hw.get("settings") or {}
        questions = settings.get("questions") or hw.get("questions") or []
        answers = submission.get("answers") or {}

        if not questions:
            await channel._send_event(
                connection, "ai_grade_submission_result",
                request_id=request_id, error="No questions found",
            )
            return

        result = await grade_submission(questions, answers)

        feedback_data = {
            "overall": result.get("feedback", ""),
            "questions": {q["id"]: q.get("comment", "") for q in result.get("questions", [])},
        }
        submission_update = {
            "status": "graded",
            "score": result["score"],
            "feedback": feedback_data,
            "graded_at": datetime.now(timezone.utc),
            "graded_by": "ai",
        }
        await channel.storage.update_submission(submission["id"], submission_update)

        await channel._send_event(
            connection, "ai_grade_submission_result",
            request_id=request_id,
            score=result["score"],
            feedback=result.get("feedback", ""),
            rubric=result.get("rubric", []),
            strengths=result.get("strengths", []),
            improvements=result.get("improvements", []),
            questions=result.get("questions", []),
        )
    except Exception as e:
        logger.error("[ws] ai_grade_submission failed: {}", e)
        await channel._send_event(
            connection, "ai_grade_submission_result",
            request_id=request_id, error=str(e),
        )


async def handle_ai_generate_questions_ws(
    channel: Any,
    connection: Any,
    envelope: dict[str, Any],
) -> None:
    from nanobot.api.ai_generate_questions import generate_questions

    request_id = envelope.get("request_id", "")
    content = envelope.get("content", "")
    num_questions = envelope.get("num_questions", 10)
    type_distribution = envelope.get("type_distribution", {})

    if not content:
        await channel._send_event(
            connection, "ai_generate_questions_result",
            request_id=request_id, error="missing content",
        )
        return

    try:
        conn_meta = _get_conn_meta(channel, connection)
        # Fallback: use role/user_id from envelope if connection metadata is empty
        user_id = conn_meta.get("user_id") or envelope.get("user_id", "")
        role = conn_meta.get("role") or envelope.get("role", "")

        logger.info(
            "[ws] ai_generate_questions: conn_meta={}, envelope_role={}, resolved_role={}",
            conn_meta, envelope.get("role"), role,
        )

        if role != "teacher":
            logger.warning("[ws] ai_generate_questions rejected: role={!r} is not teacher", role)
            await channel._send_event(
                connection, "ai_generate_questions_result",
                request_id=request_id, error="Only teachers can generate questions",
            )
            return

        logger.info(
            "[ws] ai_generate_questions: user={}, num_questions={}, types={}",
            user_id, num_questions, type_distribution,
        )

        result = await generate_questions(
            content=content,
            num_questions=num_questions,
            type_distribution=type_distribution if type_distribution else None,
        )

        await channel._send_event(
            connection, "ai_generate_questions_result",
            request_id=request_id,
            questions=result["questions"],
            total_points=result["total_points"],
        )
    except Exception as e:
        logger.error("[ws] ai_generate_questions failed: {}", e)
        await channel._send_event(
            connection, "ai_generate_questions_result",
            request_id=request_id, error=str(e),
        )


async def handle_create_homework_ws(
    channel: Any,
    connection: Any,
    envelope: dict[str, Any],
) -> None:
    """Create homework via WebSocket (avoids HTTP 431 from large URL query params)."""
    from nanobot.api.utils import generate_id

    request_id = envelope.get("request_id", "")
    course_id = envelope.get("course_id", "")
    payload = envelope.get("data", {})

    conn_meta = _get_conn_meta(channel, connection)
    role = conn_meta.get("role") or envelope.get("role", "")
    user_id = conn_meta.get("user_id") or envelope.get("user_id", "")

    if role != "teacher":
        await channel._send_event(
            connection, "create_homework_result",
            request_id=request_id, error="Only teachers can create homework",
        )
        return

    if not course_id:
        await channel._send_event(
            connection, "create_homework_result",
            request_id=request_id, error="missing course_id",
        )
        return

    try:
        course = await channel.storage.get_course(course_id)
        if not course:
            await channel._send_event(
                connection, "create_homework_result",
                request_id=request_id, error="Course not found",
            )
            return

        teacher_id = course.get("teacherId") or course.get("teacher_id", "")
        if teacher_id != user_id:
            await channel._send_event(
                connection, "create_homework_result",
                request_id=request_id, error="Only the course owner can create homework",
            )
            return

        title = payload.get("title", "").strip()
        if not title:
            await channel._send_event(
                connection, "create_homework_result",
                request_id=request_id, error="title is required",
            )
            return

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
        homework = await channel.storage.create_homework(hw_data)
        logger.info("Homework created via WS: {} in course {} by {} (status={})", title, course_id, user_id, status)

        await channel._send_event(
            connection, "create_homework_result",
            request_id=request_id,
            ok=True,
            homework=homework,
        )
    except Exception as e:
        logger.error("[ws] create_homework failed: {}", e)
        await channel._send_event(
            connection, "create_homework_result",
            request_id=request_id, error=str(e),
        )


# -- Dispatch table --------------------------------------------------------

#: Maps envelope ``type`` to its handler function.
_ENVELOPE_HANDLERS: dict[str, Any] = {
    "new_chat": handle_new_chat,
    "attach": handle_attach,
    "message": handle_message,
    "save_source": handle_save_source,
    "ai_grade_question": handle_ai_grade_question_ws,
    "ai_grade_submission": handle_ai_grade_submission_ws,
    "ai_generate_questions": handle_ai_generate_questions_ws,
    "create_homework": handle_create_homework_ws,
}


async def dispatch_envelope(
    channel: Any,
    connection: Any,
    client_id: str,
    envelope: dict[str, Any],
) -> None:
    """Route one typed inbound envelope to the appropriate handler.

    This is the main entry point called by ``WebSocketChannel._dispatch_envelope``.
    """
    t = envelope.get("type")
    handler = _ENVELOPE_HANDLERS.get(t)
    if handler is None:
        await channel._send_event(connection, "error", detail=f"unknown type: {t!r}")
        return

    # ``handle_message`` needs the extra client_id kwarg.
    if t == "message":
        await handler(channel, connection, envelope, client_id=client_id)
    else:
        await handler(channel, connection, envelope)
