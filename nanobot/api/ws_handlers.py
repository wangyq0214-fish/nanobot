"""WebSocket envelope dispatch handlers.

Extracted from ``WebSocketChannel._dispatch_envelope`` to keep the
channel class focused on connection plumbing.  Each handler receives
the channel instance so it can call ``_send_event``, ``_attach``, etc.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger
from nanobot.config.paths import get_path_root


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
    # Merge envelope meta (e.g., mode: 'quick'/'deep')
    envelope_meta = envelope.get("meta")
    if isinstance(envelope_meta, dict):
        msg_meta.update(envelope_meta)
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
    if role == "researcher" and Path(path).suffix.lower() == ".tex":
        file_name = Path(path).name or "document.tex"
        draft = await channel.storage.save_latex_draft({
            "user_id": user_id,
            "user_role": role,
            "chat_id": envelope.get("chat_id", ""),
            "title": envelope.get("title") or Path(file_name).stem or "document",
            "file_name": file_name,
            "content": content,
            "status": envelope.get("status", "draft"),
            "metadata": {"legacyPath": path, "source": "save_source"},
            "change_source": envelope.get("change_source", "legacy-save-source"),
        })
        await channel._send_event(connection, "source_saved", path=path, draft=draft)
        return

    # Legacy non-LaTeX source saves still use the user directory.
    user_dir = get_path_root() / "users" / role / user_id
    target = (user_dir / path).resolve()
    if not str(target).startswith(str(user_dir.resolve())):
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
    role = conn_meta.get("role", "")
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
        user_id = conn_meta.get("user_id", "")

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
        user_id = conn_meta.get("user_id", "")
        role = conn_meta.get("role", "")

        logger.info(
            "[ws] ai_generate_questions: conn_meta={}, resolved_role={}",
            conn_meta, role,
        )

        # Allow both teachers and students to generate questions
        if role not in ("teacher", "student"):
            logger.warning("[ws] ai_generate_questions rejected: role={!r} is not teacher or student", role)
            await channel._send_event(
                connection, "ai_generate_questions_result",
                request_id=request_id, error="Only teachers and students can generate questions",
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


async def handle_ai_parse_questions_ws(
    channel: Any,
    connection: Any,
    envelope: dict[str, Any],
) -> None:
    """Parse user-pasted text into standardized questions via AI with streaming."""
    from nanobot.api.ai_generate_questions import parse_questions_streaming

    request_id = envelope.get("request_id", "")
    content = envelope.get("content", "")

    if not content:
        await channel._send_event(
            connection, "ai_parse_questions_result",
            request_id=request_id, error="missing content",
        )
        return

    conn_meta = _get_conn_meta(channel, connection)
    role = conn_meta.get("role", "")

    # Allow both teachers and students to parse questions
    if role not in ("teacher", "student"):
        await channel._send_event(
            connection, "ai_parse_questions_result",
            request_id=request_id, error="Only teachers and students can parse questions",
        )
        return

    try:
        logger.info("[ws] ai_parse_questions: content_len={}", len(content))

        # Callback to send each question as it's parsed
        async def on_question_parsed(question):
            await channel._send_event(
                connection, "ai_parse_question_item",
                request_id=request_id,
                question=question,
            )

        result = await parse_questions_streaming(content=content, callback=on_question_parsed)

        # Send final result
        await channel._send_event(
            connection, "ai_parse_questions_result",
            request_id=request_id,
            questions=result["questions"],
            total_points=result["total_points"],
        )
    except Exception as e:
        logger.error("[ws] ai_parse_questions failed: {}", e)
        await channel._send_event(
            connection, "ai_parse_questions_result",
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
    role = conn_meta.get("role", "")
    user_id = conn_meta.get("user_id", "")

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
    role = conn_meta.get("role", "")
    user_id = conn_meta.get("user_id", "")

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
                existing["last_attempt"] = datetime.utcnow()
            else:
                kps.append({
                    "id": f"kp_{len(kps) + 1}",
                    "title": new_kp["title"],
                    "formula": new_kp.get("formula", ""),
                    "mastery": max(0, min(1, 0.5 + new_kp["mastery_delta"])),
                    "attempts": 1,
                    "correct": 1 if result["is_correct"] else 0,
                    "last_attempt": datetime.utcnow(),
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
                "timestamp": datetime.utcnow(),
            })

        # Add strategy (camelCase from StorageWrapper)
        strategies = profile.get("strategies") or []
        if result.get("strategy"):
            strategies.append({
                "id": f"strat_{len(strategies) + 1}",
                "content": result["strategy"],
                "related_kp": result["knowledge_points"][0]["title"] if result["knowledge_points"] else "",
                "timestamp": datetime.utcnow(),
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
    role = conn_meta.get("role", "")
    user_id = conn_meta.get("user_id", "")

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


# -- Researcher handlers ---------------------------------------------------


# Pending chunked uploads: Map<upload_id, {chunks: list, file_name, title, user_id, role}]
_pending_uploads: dict[str, dict[str, Any]] = {}


async def handle_upload_paper_start_ws(
    channel: Any,
    connection: Any,
    envelope: dict[str, Any],
) -> None:
    """Start a chunked paper upload. Client sends this before chunks."""
    upload_id = envelope.get("upload_id", "")
    file_name = envelope.get("file_name", "paper.pdf")
    title = envelope.get("title", "")
    total_chunks = envelope.get("total_chunks", 0)

    if not upload_id:
        return

    conn_meta = _get_conn_meta(channel, connection)
    user_id = conn_meta.get("user_id", "")
    role = conn_meta.get("role", "")

    _pending_uploads[upload_id] = {
        "chunks": [],
        "file_name": file_name,
        "title": title,
        "user_id": user_id,
        "role": role,
        "total_chunks": total_chunks,
        "request_id": envelope.get("request_id", ""),
    }

    logger.info("[ws] upload_paper_start: id={}, file={}, total_chunks={}", upload_id, file_name, total_chunks)

    await channel._send_event(
        connection, "upload_paper_ack",
        upload_id=upload_id,
        status="ready",
    )


async def handle_upload_paper_chunk_ws(
    channel: Any,
    connection: Any,
    envelope: dict[str, Any],
) -> None:
    """Receive one chunk of base64 data."""
    upload_id = envelope.get("upload_id", "")
    chunk_data = envelope.get("chunk_data", "")
    chunk_index = envelope.get("chunk_index", 0)

    upload = _pending_uploads.get(upload_id)
    if not upload:
        logger.warning("[ws] upload_paper_chunk: unknown upload_id={}", upload_id)
        return

    upload["chunks"].append(chunk_data)
    logger.debug("[ws] upload_paper_chunk: id={}, chunk={}/{}", upload_id, chunk_index + 1, upload["total_chunks"])


async def handle_upload_paper_end_ws(
    channel: Any,
    connection: Any,
    envelope: dict[str, Any],
) -> None:
    """Finalize chunked upload — combine chunks, extract text, save to DB."""
    import base64
    import uuid
    from pathlib import Path

    from nanobot.services.pdf_service import chunk_pages, extract_pdf_text

    upload_id = envelope.get("upload_id", "")
    request_id = envelope.get("request_id", "")

    upload = _pending_uploads.pop(upload_id, None)
    if not upload:
        await channel._send_event(
            connection, "upload_paper_result",
            request_id=request_id, error="Unknown upload_id",
        )
        return

    request_id = request_id or upload["request_id"]
    file_name = upload["file_name"]
    title = upload["title"]
    user_id = upload["user_id"]

    try:
        # Combine chunks and decode base64
        combined = "".join(upload["chunks"])
        try:
            pdf_bytes = base64.b64decode(combined)
        except Exception:
            await channel._send_event(
                connection, "upload_paper_result",
                request_id=request_id, error="Invalid base64 file data",
            )
            return

        # Save file
        upload_dir = get_path_root() / "uploads" / "papers"
        upload_dir.mkdir(parents=True, exist_ok=True)
        safe_name = f"{uuid.uuid4().hex[:12]}_{file_name}"
        file_path = upload_dir / safe_name
        file_path.write_bytes(pdf_bytes)

        # Extract text
        try:
            pdf_data = extract_pdf_text(file_path)
        except Exception as e:
            logger.error("[ws] upload_paper PDF extraction failed: {}", e)
            file_path.unlink(missing_ok=True)
            await channel._send_event(
                connection, "upload_paper_result",
                request_id=request_id, error=f"PDF extraction failed: {e}",
            )
            return

        if not title:
            title = pdf_data["title"]

        # Create paper record
        paper = await channel.storage.create_paper({
            "title": title,
            "authors": "",
            "file_path": str(file_path),
            "file_name": file_name,
            "page_count": pdf_data["page_count"],
            "full_text": pdf_data["full_text"],
            "source": "upload",
            "user_id": user_id,
        })

        # Create chunks
        chunks = chunk_pages(pdf_data["pages"])
        chunk_dicts = [
            {"chunk_index": c["chunk_index"], "page_number": c["page_number"], "content": c["content"]}
            for c in chunks
        ]
        chunk_count = await channel.storage.create_paper_chunks(paper["id"], chunk_dicts)

        logger.info("[ws] upload_paper: id={}, title={}, pages={}, chunks={}",
                    paper["id"], title, pdf_data["page_count"], chunk_count)

        await channel._send_event(
            connection, "upload_paper_result",
            request_id=request_id,
            paper=paper,
            page_count=pdf_data["page_count"],
            chunk_count=chunk_count,
        )
    except Exception as e:
        logger.error("[ws] upload_paper failed: {}", e)
        await channel._send_event(
            connection, "upload_paper_result",
            request_id=request_id, error=str(e),
        )


# -- Researcher AI handlers ------------------------------------------------


async def handle_ai_polish_ws(
    channel: Any,
    connection: Any,
    envelope: dict[str, Any],
) -> None:
    """AI text polishing for the writing assistant."""
    from nanobot.api.ai_polish import polish_text

    request_id = envelope.get("request_id", "")
    text = envelope.get("text", "")
    mode = envelope.get("mode", "polish")

    if not text:
        await channel._send_event(
            connection, "ai_polish_result",
            request_id=request_id, error="missing text",
        )
        return

    try:
        conn_meta = _get_conn_meta(channel, connection)
        role = conn_meta.get("role", "")
        if role != "researcher":
            await channel._send_event(
                connection, "ai_polish_result",
                request_id=request_id, error="Only researchers can use AI polish",
            )
            return

        logger.info("[ws] ai_polish: mode={}, text_len={}", mode, len(text))
        result = await polish_text(text=text, mode=mode)

        await channel._send_event(
            connection, "ai_polish_result",
            request_id=request_id,
            polished_text=result["polished_text"],
            error=result.get("error"),
        )
    except Exception as e:
        logger.error("[ws] ai_polish failed: {}", e)
        await channel._send_event(
            connection, "ai_polish_result",
            request_id=request_id, error=str(e),
        )


async def handle_ai_paper_summary_ws(
    channel: Any,
    connection: Any,
    envelope: dict[str, Any],
) -> None:
    """AI paper summarization."""
    from nanobot.api.ai_paper_summary import generate_paper_summary

    request_id = envelope.get("request_id", "")
    paper_id = envelope.get("paper_id")

    if not paper_id:
        await channel._send_event(
            connection, "ai_paper_summary_result",
            request_id=request_id, error="missing paper_id",
        )
        return

    try:
        conn_meta = _get_conn_meta(channel, connection)
        role = conn_meta.get("role", "")
        if role != "researcher":
            await channel._send_event(
                connection, "ai_paper_summary_result",
                request_id=request_id, error="Only researchers can summarize papers",
            )
            return

        # Get paper from storage
        paper = await channel.storage.get_paper(int(paper_id))
        if not paper:
            await channel._send_event(
                connection, "ai_paper_summary_result",
                request_id=request_id, error="Paper not found",
            )
            return

        # Check cache: if ai_summary already exists, return it
        cached_summary = paper.get("aiSummary") or paper.get("ai_summary")
        if cached_summary:
            logger.info("[ws] ai_paper_summary: returning cached summary for paper {}", paper_id)
            await channel._send_event(
                connection, "ai_paper_summary_result",
                request_id=request_id,
                summary=cached_summary,
                cached=True,
            )
            return

        full_text = paper.get("fullText") or paper.get("full_text", "")
        if not full_text:
            await channel._send_event(
                connection, "ai_paper_summary_result",
                request_id=request_id, error="Paper has no extracted text",
            )
            return

        logger.info("[ws] ai_paper_summary: generating for paper {} ({} chars)", paper_id, len(full_text))
        result = await generate_paper_summary(full_text=full_text)

        # Cache the summary
        if result.get("summary") and not result.get("error"):
            try:
                await channel.storage.update_paper(int(paper_id), {"ai_summary": result["summary"]})
            except Exception as cache_err:
                logger.warning("[ws] ai_paper_summary: failed to cache summary: {}", cache_err)

        await channel._send_event(
            connection, "ai_paper_summary_result",
            request_id=request_id,
            summary=result["summary"],
            cached=False,
            error=result.get("error"),
        )
    except Exception as e:
        logger.error("[ws] ai_paper_summary failed: {}", e)
        await channel._send_event(
            connection, "ai_paper_summary_result",
            request_id=request_id, error=str(e),
        )


async def handle_researcher_clarify_ws(
    channel: Any,
    connection: Any,
    envelope: dict[str, Any],
) -> None:
    """Generate the deep-mode clarification schema without creating a chat turn."""
    from nanobot.api.researcher_clarification import generate_researcher_clarification

    request_id = envelope.get("request_id", "")
    chat_id = envelope.get("chat_id", "")
    question = envelope.get("question", "")

    if not isinstance(question, str) or not question.strip():
        await channel._send_event(
            connection,
            "researcher_clarification",
            request_id=request_id,
            chat_id=chat_id,
            error="missing question",
        )
        return

    try:
        conn_meta = _get_conn_meta(channel, connection)
        role = conn_meta.get("role", "")
        if role != "researcher":
            await channel._send_event(
                connection,
                "researcher_clarification",
                request_id=request_id,
                chat_id=chat_id,
                error="Only researchers can use deep clarification",
            )
            return

        result = await generate_researcher_clarification(question)
        await channel._send_event(
            connection,
            "researcher_clarification",
            request_id=request_id,
            chat_id=chat_id,
            analysis=result.get("analysis", ""),
            questions=result.get("questions", []),
            error=result.get("error"),
        )
    except Exception as e:
        logger.error("[ws] researcher_clarify failed: {}", e)
        await channel._send_event(
            connection,
            "researcher_clarification",
            request_id=request_id,
            chat_id=chat_id,
            error=str(e),
        )


async def handle_delete_session_ws(
    channel: Any,
    connection: Any,
    envelope: dict[str, Any],
) -> None:
    """Handle session deletion via WebSocket envelope."""
    from pathlib import Path
    from nanobot.session.manager import SessionManager

    key = envelope.get("key")
    if not key or not isinstance(key, str):
        await _err(channel, connection, "missing session key")
        return

    conn_meta = _get_conn_meta(channel, connection)
    role = conn_meta.get("role", "")
    user_id = conn_meta.get("user_id", "")

    if not role or not user_id:
        await _err(channel, connection, "not authenticated")
        return

    # Reconstruct full key with user prefix for user workspace
    full_key = f"{role}:{user_id}:{key}"
    user_sessions_dir = get_path_root() / "users" / role / user_id / "sessions"
    safe_key = SessionManager.safe_key(full_key)
    session_file = user_sessions_dir / f"{safe_key}.jsonl"

    if not session_file.exists():
        await channel._send_event(connection, "session_deleted", key=key, deleted=False)
        return

    try:
        session_file.unlink()
        await channel._send_event(connection, "session_deleted", key=key, deleted=True)
    except OSError as e:
        logger.warning("Failed to delete user session {}: {}", full_key, e)
        await _err(channel, connection, "Failed to delete session")


async def handle_save_research_result_ws(
    channel: Any,
    connection: Any,
    envelope: dict[str, Any],
) -> None:
    """Handle saving research result via WebSocket envelope."""
    from nanobot.storage.factory import get_storage

    request_id = envelope.get("request_id")
    content = envelope.get("content")
    if not content or not isinstance(content, str):
        await _err(channel, connection, "missing content")
        return

    conn_meta = _get_conn_meta(channel, connection)
    role = conn_meta.get("role", "")
    user_id = conn_meta.get("user_id", "")

    if not role or not user_id:
        await _err(channel, connection, "not authenticated")
        return

    if role != "researcher":
        await _err(channel, connection, "Only researchers can save research results")
        return

    chat_id = envelope.get("chat_id", "")
    session_title = envelope.get("session_title", "")

    title = str(envelope.get("title") or _extract_research_title(content)).strip()

    try:
        storage = get_storage()
        result = await storage.create_research_result({
            "user_id": user_id,
            "user_role": role,
            "title": title,
            "content": content,
            "chat_id": chat_id,
            "session_title": session_title,
            "source_message_id": envelope.get("source_message_id") or envelope.get("sourceMessageId", ""),
            "project_id": _optional_int(envelope.get("project_id") or envelope.get("projectId")),
            "project_name": str(envelope.get("project_name") or envelope.get("projectName", "")).strip(),
            "status": envelope.get("status", "saved"),
            "sections": envelope.get("sections") if isinstance(envelope.get("sections"), list) else [],
            "citations": envelope.get("citations") if isinstance(envelope.get("citations"), list) else [],
            "attachments": envelope.get("attachments") if isinstance(envelope.get("attachments"), list) else [],
            "resources": envelope.get("resources") if isinstance(envelope.get("resources"), list) else [],
            "tags": envelope.get("tags") if isinstance(envelope.get("tags"), list) else [],
            "metadata": envelope.get("metadata") if isinstance(envelope.get("metadata"), dict) else {},
        })
        logger.info(f"User {user_id} saved research result via WS: {result.get('id')}")
        await channel._send_event(
            connection,
            "research_result_saved",
            request_id=request_id,
            result=result,
        )
    except Exception as e:
        logger.error("Failed to save research result: {}", e)
        await _err(channel, connection, f"Failed to save: {str(e)}")


def _optional_int(value: Any) -> int | None:
    """Parse an optional integer field."""
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _extract_research_title(content: str, max_len: int = 60) -> str:
    """Extract a title from AI content."""
    # Try to find first heading
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("#"):
            title = line.lstrip("#").strip()
            if title:
                return title[:max_len]

    # Try to find first non-empty line
    for line in content.split("\n"):
        line = line.strip()
        if line and len(line) > 5:
            title = line.replace("**", "").replace("*", "").replace("`", "")
            return title[:max_len] + ("..." if len(title) > max_len else "")

    # Fallback
    clean = content.replace("\n", " ").strip()
    return clean[:max_len] + ("..." if len(clean) > max_len else "")


# -- Student resource & category handlers -----------------------------------


async def handle_student_resource_list_ws(
    channel: Any,
    connection: Any,
    envelope: dict[str, Any],
) -> None:
    """List student resources via WebSocket."""
    request_id = envelope.get("request_id", "")
    resource_type = envelope.get("resource_type")
    category_id = envelope.get("category_id")

    conn_meta = _get_conn_meta(channel, connection)
    user_id = conn_meta.get("user_id", "")
    role = conn_meta.get("role", "")

    if role != "student":
        await channel._send_event(
            connection, "student_resource_list_result",
            request_id=request_id, error="Only students can access resources",
        )
        return

    try:
        resources = await channel.storage.list_student_resources(user_id, resource_type)
        # Filter by category if specified
        if category_id is not None:
            resources = [r for r in resources if r.get("category_id") == category_id]
        await channel._send_event(
            connection, "student_resource_list_result",
            request_id=request_id, resources=resources,
        )
    except Exception as e:
        logger.error("[ws] student_resource_list failed: {}", e)
        await channel._send_event(
            connection, "student_resource_list_result",
            request_id=request_id, error=str(e),
        )


async def handle_student_resource_create_ws(
    channel: Any,
    connection: Any,
    envelope: dict[str, Any],
) -> None:
    """Create a student resource via WebSocket."""
    request_id = envelope.get("request_id", "")
    resource_type = envelope.get("resource_type", "question")
    title = envelope.get("title", "")
    content = envelope.get("content", "")
    source_type = envelope.get("source_type", "manual")
    source_id = envelope.get("source_id")
    category_id = envelope.get("category_id")
    metadata = envelope.get("metadata", {})

    conn_meta = _get_conn_meta(channel, connection)
    user_id = conn_meta.get("user_id", "")
    role = conn_meta.get("role", "")

    if role != "student":
        await channel._send_event(
            connection, "student_resource_create_result",
            request_id=request_id, error="Only students can create resources",
        )
        return

    if not title:
        await channel._send_event(
            connection, "student_resource_create_result",
            request_id=request_id, error="title is required",
        )
        return

    try:
        resource_data = {
            "student_id": user_id,
            "resource_type": resource_type,
            "title": title,
            "content": content,
            "source_type": source_type,
            "source_id": source_id,
            "category_id": category_id,
            "metadata_extra": metadata,
        }
        resource = await channel.storage.create_student_resource(resource_data)

        # Update category question count if categorized
        if category_id:
            await channel.storage.update_category_question_count(category_id)

        logger.info("[ws] student_resource_create: id={}, type={}, user={}", resource.get("id"), resource_type, user_id)
        await channel._send_event(
            connection, "student_resource_create_result",
            request_id=request_id, ok=True, resource=resource,
        )
    except Exception as e:
        logger.error("[ws] student_resource_create failed: {}", e)
        await channel._send_event(
            connection, "student_resource_create_result",
            request_id=request_id, error=str(e),
        )


async def handle_student_resource_delete_ws(
    channel: Any,
    connection: Any,
    envelope: dict[str, Any],
) -> None:
    """Delete a student resource via WebSocket."""
    request_id = envelope.get("request_id", "")
    resource_id = envelope.get("resource_id")

    conn_meta = _get_conn_meta(channel, connection)
    user_id = conn_meta.get("user_id", "")
    role = conn_meta.get("role", "")

    if role != "student":
        await channel._send_event(
            connection, "student_resource_delete_result",
            request_id=request_id, error="Only students can delete resources",
        )
        return

    if not resource_id:
        await channel._send_event(
            connection, "student_resource_delete_result",
            request_id=request_id, error="resource_id is required",
        )
        return

    try:
        # Get the resource first to know its category
        resource = await channel.storage.get_student_resource(int(resource_id))
        category_id = resource.get("category_id") if resource else None

        success = await channel.storage.delete_student_resource(int(resource_id), user_id)
        if success:
            # Update category question count
            if category_id:
                await channel.storage.update_category_question_count(category_id)
            await channel._send_event(
                connection, "student_resource_delete_result",
                request_id=request_id, ok=True,
            )
        else:
            await channel._send_event(
                connection, "student_resource_delete_result",
                request_id=request_id, error="Resource not found",
            )
    except Exception as e:
        logger.error("[ws] student_resource_delete failed: {}", e)
        await channel._send_event(
            connection, "student_resource_delete_result",
            request_id=request_id, error=str(e),
        )


async def handle_student_resource_update_ws(
    channel: Any,
    connection: Any,
    envelope: dict[str, Any],
) -> None:
    """Update a student resource via WebSocket."""
    request_id = envelope.get("request_id", "")
    resource_id = envelope.get("resource_id")
    update_fields = envelope.get("data", {})

    conn_meta = _get_conn_meta(channel, connection)
    user_id = conn_meta.get("user_id", "")
    role = conn_meta.get("role", "")

    if role != "student":
        await channel._send_event(
            connection, "student_resource_update_result",
            request_id=request_id, error="Only students can update resources",
        )
        return

    if not resource_id:
        await channel._send_event(
            connection, "student_resource_update_result",
            request_id=request_id, error="resource_id is required",
        )
        return

    try:
        # Map metadata to metadata_extra for storage
        if "metadata" in update_fields:
            update_fields["metadata_extra"] = update_fields.pop("metadata")

        resource = await channel.storage.update_student_resource(int(resource_id), user_id, update_fields)
        if resource:
            await channel._send_event(
                connection, "student_resource_update_result",
                request_id=request_id, ok=True, resource=resource,
            )
        else:
            await channel._send_event(
                connection, "student_resource_update_result",
                request_id=request_id, error="Resource not found",
            )
    except Exception as e:
        logger.error("[ws] student_resource_update failed: {}", e)
        await channel._send_event(
            connection, "student_resource_update_result",
            request_id=request_id, error=str(e),
        )


async def handle_student_resource_categorize_ws(
    channel: Any,
    connection: Any,
    envelope: dict[str, Any],
) -> None:
    """Set category for a student resource via WebSocket."""
    request_id = envelope.get("request_id", "")
    resource_id = envelope.get("resource_id")
    category_id = envelope.get("category_id")

    conn_meta = _get_conn_meta(channel, connection)
    user_id = conn_meta.get("user_id", "")
    role = conn_meta.get("role", "")

    if role != "student":
        await channel._send_event(
            connection, "student_resource_categorize_result",
            request_id=request_id, error="Only students can categorize resources",
        )
        return

    if not resource_id:
        await channel._send_event(
            connection, "student_resource_categorize_result",
            request_id=request_id, error="resource_id is required",
        )
        return

    try:
        # Get old category for count update
        old_resource = await channel.storage.get_student_resource(int(resource_id))
        old_category_id = old_resource.get("category_id") if old_resource else None

        resource = await channel.storage.update_student_resource(
            int(resource_id), user_id, {"category_id": category_id}
        )
        if resource:
            # Update category question counts
            if old_category_id:
                await channel.storage.update_category_question_count(old_category_id)
            if category_id:
                await channel.storage.update_category_question_count(category_id)

            await channel._send_event(
                connection, "student_resource_categorize_result",
                request_id=request_id, ok=True, resource=resource,
            )
        else:
            await channel._send_event(
                connection, "student_resource_categorize_result",
                request_id=request_id, error="Resource not found",
            )
    except Exception as e:
        logger.error("[ws] student_resource_categorize failed: {}", e)
        await channel._send_event(
            connection, "student_resource_categorize_result",
            request_id=request_id, error=str(e),
        )


async def handle_student_categories_list_ws(
    channel: Any,
    connection: Any,
    envelope: dict[str, Any],
) -> None:
    """List student categories via WebSocket."""
    request_id = envelope.get("request_id", "")

    conn_meta = _get_conn_meta(channel, connection)
    user_id = conn_meta.get("user_id", "")
    role = conn_meta.get("role", "")

    if role != "student":
        await channel._send_event(
            connection, "student_categories_list_result",
            request_id=request_id, error="Only students can access categories",
        )
        return

    try:
        categories = await channel.storage.list_student_categories(user_id)
        await channel._send_event(
            connection, "student_categories_list_result",
            request_id=request_id, categories=categories,
        )
    except Exception as e:
        logger.error("[ws] student_categories_list failed: {}", e)
        await channel._send_event(
            connection, "student_categories_list_result",
            request_id=request_id, error=str(e),
        )


async def handle_student_category_create_ws(
    channel: Any,
    connection: Any,
    envelope: dict[str, Any],
) -> None:
    """Create a student category via WebSocket."""
    request_id = envelope.get("request_id", "")
    name = envelope.get("name", "").strip()
    description = envelope.get("description", "")
    color = envelope.get("color")

    conn_meta = _get_conn_meta(channel, connection)
    user_id = conn_meta.get("user_id", "")
    role = conn_meta.get("role", "")

    if role != "student":
        await channel._send_event(
            connection, "student_category_create_result",
            request_id=request_id, error="Only students can create categories",
        )
        return

    if not name:
        await channel._send_event(
            connection, "student_category_create_result",
            request_id=request_id, error="Category name is required",
        )
        return

    try:
        # Check for duplicate name
        existing = await channel.storage.list_student_categories(user_id)
        for cat in existing:
            if cat.get("name") == name:
                await channel._send_event(
                    connection, "student_category_create_result",
                    request_id=request_id, error="Category with this name already exists",
                )
                return

        category_data = {
            "student_id": user_id,
            "name": name,
            "description": description,
            "color": color,
        }
        category = await channel.storage.create_student_category(category_data)
        logger.info("[ws] student_category_create: id={}, name={}, user={}", category.get("id"), name, user_id)
        await channel._send_event(
            connection, "student_category_create_result",
            request_id=request_id, ok=True, category=category,
        )
    except Exception as e:
        logger.error("[ws] student_category_create failed: {}", e)
        await channel._send_event(
            connection, "student_category_create_result",
            request_id=request_id, error=str(e),
        )


async def handle_student_category_update_ws(
    channel: Any,
    connection: Any,
    envelope: dict[str, Any],
) -> None:
    """Update a student category via WebSocket."""
    request_id = envelope.get("request_id", "")
    category_id = envelope.get("category_id")
    name = envelope.get("name")
    description = envelope.get("description")
    color = envelope.get("color")

    conn_meta = _get_conn_meta(channel, connection)
    user_id = conn_meta.get("user_id", "")
    role = conn_meta.get("role", "")

    if role != "student":
        await channel._send_event(
            connection, "student_category_update_result",
            request_id=request_id, error="Only students can update categories",
        )
        return

    if not category_id:
        await channel._send_event(
            connection, "student_category_update_result",
            request_id=request_id, error="category_id is required",
        )
        return

    try:
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if color is not None:
            update_data["color"] = color

        category = await channel.storage.update_student_category(int(category_id), user_id, update_data)
        if category:
            await channel._send_event(
                connection, "student_category_update_result",
                request_id=request_id, ok=True, category=category,
            )
        else:
            await channel._send_event(
                connection, "student_category_update_result",
                request_id=request_id, error="Category not found",
            )
    except Exception as e:
        logger.error("[ws] student_category_update failed: {}", e)
        await channel._send_event(
            connection, "student_category_update_result",
            request_id=request_id, error=str(e),
        )


async def handle_student_category_delete_ws(
    channel: Any,
    connection: Any,
    envelope: dict[str, Any],
) -> None:
    """Delete a student category via WebSocket."""
    request_id = envelope.get("request_id", "")
    category_id = envelope.get("category_id")

    conn_meta = _get_conn_meta(channel, connection)
    user_id = conn_meta.get("user_id", "")
    role = conn_meta.get("role", "")

    if role != "student":
        await channel._send_event(
            connection, "student_category_delete_result",
            request_id=request_id, error="Only students can delete categories",
        )
        return

    if not category_id:
        await channel._send_event(
            connection, "student_category_delete_result",
            request_id=request_id, error="category_id is required",
        )
        return

    try:
        success = await channel.storage.delete_student_category(int(category_id), user_id)
        if success:
            await channel._send_event(
                connection, "student_category_delete_result",
                request_id=request_id, ok=True,
            )
        else:
            await channel._send_event(
                connection, "student_category_delete_result",
                request_id=request_id, error="Category not found",
            )
    except Exception as e:
        logger.error("[ws] student_category_delete failed: {}", e)
        await channel._send_event(
            connection, "student_category_delete_result",
            request_id=request_id, error=str(e),
        )


# -- Dispatch table --------------------------------------------------------

#: Maps envelope ``type`` to its handler function.
_ENVELOPE_HANDLERS: dict[str, Any] = {
    "new_chat": handle_new_chat,
    "attach": handle_attach,
    "message": handle_message,
    "save_source": handle_save_source,
    "save_research_result": handle_save_research_result_ws,
    "delete_session": handle_delete_session_ws,
    "ai_grade_question": handle_ai_grade_question_ws,
    "ai_grade_submission": handle_ai_grade_submission_ws,
    "ai_generate_questions": handle_ai_generate_questions_ws,
    "ai_parse_questions": handle_ai_parse_questions_ws,
    "create_homework": handle_create_homework_ws,
    "ai_tutor_evaluate": handle_ai_tutor_evaluate_ws,
    "ai_generate_derivation": handle_ai_generate_derivation_ws,
    "ai_tutor_recommend": handle_ai_tutor_recommend_ws,
    "upload_paper_start": handle_upload_paper_start_ws,
    "upload_paper_chunk": handle_upload_paper_chunk_ws,
    "upload_paper_end": handle_upload_paper_end_ws,
    "ai_polish": handle_ai_polish_ws,
    "ai_paper_summary": handle_ai_paper_summary_ws,
    "researcher_clarify": handle_researcher_clarify_ws,
    # Student resource & category operations
    "student_resource_list": handle_student_resource_list_ws,
    "student_resource_create": handle_student_resource_create_ws,
    "student_resource_delete": handle_student_resource_delete_ws,
    "student_resource_update": handle_student_resource_update_ws,
    "student_resource_categorize": handle_student_resource_categorize_ws,
    "student_categories_list": handle_student_categories_list_ws,
    "student_category_create": handle_student_category_create_ws,
    "student_category_update": handle_student_category_update_ws,
    "student_category_delete": handle_student_category_delete_ws,
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
