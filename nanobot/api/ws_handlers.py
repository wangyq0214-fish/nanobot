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


async def handle_ai_tutor_evaluate_ws(
    channel: Any,
    connection: Any,
    envelope: dict[str, Any],
) -> None:
    """Evaluate a student's answer in tutor mode with learning profile update."""
    from nanobot.api.ai_tutor import evaluate_student_answer

    request_id = envelope.get("request_id", "")
    question = envelope.get("question", "")
    student_answer = envelope.get("student_answer", "")
    reference_answer = envelope.get("reference_answer", "")

    if not question:
        await channel._send_event(
            connection, "ai_tutor_evaluate_result",
            request_id=request_id, error="missing question",
        )
        return

    conn_meta = _get_conn_meta(channel, connection)
    role = conn_meta.get("role") or envelope.get("role", "")
    user_id = conn_meta.get("user_id") or envelope.get("user_id", "")

    if role != "student":
        await channel._send_event(
            connection, "ai_tutor_evaluate_result",
            request_id=request_id, error="Only students can use tutor evaluation",
        )
        return

    try:
        # Load existing tutor profile for context
        # Note: StorageWrapper returns camelCase keys
        profile = await channel.storage.get_tutor_profile(user_id)
        profile_context = ""
        if profile:
            kps = profile.get("knowledgePoints", [])
            if kps:
                kp_summary = ", ".join(
                    f"{kp['title']}(掌握度:{kp.get('mastery', 0):.0%})"
                    for kp in kps[:5]
                )
                profile_context = f"已学知识点: {kp_summary}"

        # Call AI evaluation
        result = await evaluate_student_answer(
            question=question,
            student_answer=student_answer,
            profile_context=profile_context,
            reference_answer=reference_answer,
        )

        # Update tutor profile — use snake_case for storage layer
        if profile is None:
            profile = {
                "knowledgePoints": [],
                "errorRecords": [],
                "strategies": [],
                "totalSubmissions": 0,
            }

        # Update knowledge points (camelCase from StorageWrapper)
        kps = profile.get("knowledgePoints") or []
        for new_kp in result.get("knowledge_points", []):
            existing = next((k for k in kps if k["title"] == new_kp["title"]), None)
            if existing:
                existing["mastery"] = max(0, min(1, existing.get("mastery", 0.5) + new_kp["mastery_delta"]))
                existing["attempts"] = existing.get("attempts", 0) + 1
                if result["is_correct"]:
                    existing["correct"] = existing.get("correct", 0) + 1
                existing["last_attempt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            else:
                kps.append({
                    "id": f"kp_{len(kps) + 1}",
                    "title": new_kp["title"],
                    "formula": new_kp.get("formula", ""),
                    "mastery": max(0, min(1, 0.5 + new_kp["mastery_delta"])),
                    "attempts": 1,
                    "correct": 1 if result["is_correct"] else 0,
                    "last_attempt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                })

        # Add error record if incorrect (camelCase from StorageWrapper)
        errors = profile.get("errorRecords") or []
        if not result["is_correct"] and result.get("error_type"):
            errors.append({
                "id": f"err_{len(errors) + 1}",
                "knowledge_point_id": "",
                "type": result["error_type"],
                "title": question[:50],
                "detail": result.get("error_detail", ""),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            })

        # Add strategy (camelCase from StorageWrapper)
        strategies = profile.get("strategies") or []
        if result.get("strategy"):
            strategies.append({
                "id": f"strat_{len(strategies) + 1}",
                "content": result["strategy"],
                "related_kp": result["knowledge_points"][0]["title"] if result["knowledge_points"] else "",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            })

        # Save updated profile (snake_case for storage layer)
        profile_update = {
            "knowledge_points": kps,
            "error_records": errors,
            "strategies": strategies,
            "total_submissions": (profile.get("totalSubmissions") or 0) + 1,
        }
        await channel.storage.update_tutor_profile(user_id, profile_update)

        await channel._send_event(
            connection, "ai_tutor_evaluate_result",
            request_id=request_id,
            is_correct=result["is_correct"],
            score=result["score"],
            analysis=result["analysis"],
            knowledge_points=result["knowledge_points"],
            error_type=result.get("error_type", ""),
            error_detail=result.get("error_detail", ""),
            strategy=result.get("strategy", ""),
            total_submissions=profile_update["total_submissions"],
        )
    except Exception as e:
        logger.error("[ws] ai_tutor_evaluate failed: {}", e)
        await channel._send_event(
            connection, "ai_tutor_evaluate_result",
            request_id=request_id, error=str(e),
        )


async def handle_ai_generate_derivation_ws(
    channel: Any,
    connection: Any,
    envelope: dict[str, Any],
) -> None:
    """Generate a derivation chain for a given topic via AI."""
    from nanobot.api.ai_derivation import generate_derivation_chain

    request_id = envelope.get("request_id", "")
    topic = envelope.get("topic", "")
    mode = envelope.get("mode", "formula")

    if not topic:
        await channel._send_event(
            connection, "ai_generate_derivation_result",
            request_id=request_id, error="missing topic",
        )
        return

    if mode not in ("formula", "code", "concept"):
        mode = "formula"

    try:
        logger.info("[ws] ai_generate_derivation: topic={!r}, mode={!r}", topic, mode)
        result = await generate_derivation_chain(topic=topic, mode=mode)

        await channel._send_event(
            connection, "ai_generate_derivation_result",
            request_id=request_id,
            steps=result["steps"],
        )
    except Exception as e:
        logger.error("[ws] ai_generate_derivation failed: {}", e)
        await channel._send_event(
            connection, "ai_generate_derivation_result",
            request_id=request_id, error=str(e),
        )


async def handle_ai_tutor_recommend_ws(
    channel: Any,
    connection: Any,
    envelope: dict[str, Any],
) -> None:
    """Generate AI-recommended practice questions based on the student's tutor profile."""
    from nanobot.api.ai_generate_questions import generate_questions

    request_id = envelope.get("request_id", "")
    num_questions = envelope.get("num_questions", 5)
    type_distribution = envelope.get("type_distribution", {})
    custom_content = envelope.get("content", "")

    conn_meta = _get_conn_meta(channel, connection)
    role = conn_meta.get("role") or envelope.get("role", "")
    user_id = conn_meta.get("user_id") or envelope.get("user_id", "")

    if role != "student":
        await channel._send_event(
            connection, "ai_tutor_recommend_result",
            request_id=request_id, error="Only students can use tutor recommend",
        )
        return

    logger.info("[ws] ai_tutor_recommend: received request from user={}", user_id)

    try:
        # Build content from tutor profile or use custom content
        if custom_content.strip():
            content = custom_content.strip()
        else:
            profile = await channel.storage.get_tutor_profile(user_id)
            if not profile:
                await channel._send_event(
                    connection, "ai_tutor_recommend_result",
                    request_id=request_id,
                    error="暂无学习数据，请先完成一些练习后再使用智能推题",
                )
                return

            # Extract weak knowledge points (mastery < 0.7)
            # Note: StorageWrapper returns camelCase keys
            kps = profile.get("knowledgePoints") or []
            weak_kps = sorted(
                [kp for kp in kps if kp.get("mastery", 0) < 0.7],
                key=lambda x: x.get("mastery", 0.5),
            )[:5]

            # Extract recent error records
            errors = profile.get("errorRecords") or []
            recent_errors = errors[-3:] if errors else []

            if not weak_kps and not recent_errors:
                await channel._send_event(
                    connection, "ai_tutor_recommend_result",
                    request_id=request_id,
                    error="你的知识点掌握情况良好，暂无薄弱点需要强化。可以切换到「指定知识点」模式练习。",
                )
                return

            # Build content string for question generation
            parts = []
            if weak_kps:
                kp_desc = []
                for kp in weak_kps:
                    mastery_pct = round(kp.get("mastery", 0) * 100)
                    formula = kp.get("formula", "")
                    desc = f"{kp['title']}(当前掌握度:{mastery_pct}%"
                    if formula:
                        desc += f",相关公式:{formula}"
                    desc += ")"
                    kp_desc.append(desc)
                parts.append("## 需要巩固的知识点\n" + "\n".join(f"- {d}" for d in kp_desc))

            if recent_errors:
                err_desc = []
                for err in recent_errors:
                    err_desc.append(f"{err.get('type', '未知')}错误: {err.get('title', '')} — {err.get('detail', '')}")
                parts.append("## 最近的错误记录\n" + "\n".join(f"- {d}" for d in err_desc))

            parts.append("## 出题要求\n请针对以上薄弱知识点和错误类型，生成有针对性的练习题，帮助学生巩固薄弱环节。")
            content = "\n\n".join(parts)

        logger.info(
            "[ws] ai_tutor_recommend: user={}, num_questions={}, types={}, has_custom_content={}",
            user_id, num_questions, type_distribution, bool(custom_content),
        )

        result = await generate_questions(
            content=content,
            num_questions=num_questions,
            type_distribution=type_distribution if type_distribution else None,
        )

        # Persist recommended questions to tutor profile as a new batch
        from datetime import datetime
        profile = await channel.storage.get_tutor_profile(user_id) or {}
        existing_batches = profile.get("recommendedQuestions") or []
        new_batch = {
            "id": f"b_{int(datetime.utcnow().timestamp())}_{len(existing_batches)}",
            "mode": "custom" if custom_content.strip() else "auto",
            "content": custom_content.strip()[:100] if custom_content.strip() else "",
            "createdAt": datetime.utcnow().isoformat() + "Z",
            "questions": result["questions"],
        }
        existing_batches.append(new_batch)
        profile_update = {
            "recommended_questions": existing_batches,
            "recommended_at": datetime.utcnow(),
        }
        await channel.storage.update_tutor_profile(user_id, profile_update)

        await channel._send_event(
            connection, "ai_tutor_recommend_result",
            request_id=request_id,
            questions=result["questions"],
            total_points=result["total_points"],
        )
    except Exception as e:
        logger.error("[ws] ai_tutor_recommend failed: {}", e)
        await channel._send_event(
            connection, "ai_tutor_recommend_result",
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
    "ai_tutor_evaluate": handle_ai_tutor_evaluate_ws,
    "ai_generate_derivation": handle_ai_generate_derivation_ws,
    "ai_tutor_recommend": handle_ai_tutor_recommend_ws,
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
