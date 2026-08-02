"""Grading, AI grading, publish and delete handlers."""

from __future__ import annotations

from datetime import datetime, timezone

from loguru import logger
from websockets.http11 import Request as WsRequest
from websockets.http11 import Response

from nanobot.storage.storage_wrapper import StorageWrapper

from ..ai_grade import grade_single_question
from ..utils import (
    http_error,
    http_json_response,
    parse_mutation_data,
    parse_query,
)


async def handle_homework_grade(
    request: WsRequest,
    storage: StorageWrapper,
    course_id: str,
    hw_id: str,
    *,
    identity: dict[str, str],
) -> Response:
    role = identity.get("role", "")
    user_id = identity.get("user_id", "")
    if role != "teacher":
        return http_error(403, "Only teachers can grade")
    course = await storage.get_course(course_id)
    if not course:
        return http_error(404, "Course not found")
    teacher_id = course.get("teacherId") or course.get("teacher_id", "")
    if teacher_id != user_id:
        return http_error(403, "Only the course owner can grade")
    query = parse_query(request.path)
    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload
    student_id = payload.get("studentId", "").strip()
    if not student_id:
        return http_error(400, "studentId is required")
    submission = await storage.get_submission(hw_id, student_id)
    if not submission:
        return http_error(404, "Submission not found")

    # Per-question grading: payload.questions = [{ id, score, comment }, ...]
    question_grades = payload.get("questions")
    if question_grades and isinstance(question_grades, list):
        hw = await storage.get_homework(hw_id)
        questions_meta = hw.get("questions", []) if hw else []
        meta_map = {q.get("id", ""): q for q in questions_meta}

        graded_questions = []
        total_score = 0
        total_points = 0
        for gq in question_grades:
            qid = gq.get("id", "")
            meta = meta_map.get(qid, {})
            max_score = meta.get("points", 0)
            score = min(gq.get("score", 0), max_score)
            total_score += score
            total_points += max_score
            graded_questions.append({
                "id": qid,
                "graded": True,
                "studentScore": score,
                "maxScore": max_score,
                "comment": gq.get("comment", ""),
            })
        # Auto-grade objective questions, mark remaining as ungraded
        graded_ids = {gq.get("id") for gq in question_grades}
        student_answers = submission.get("answers", {}) or {}
        logger.info(f"[grade] questions_meta count={len(questions_meta)}, graded_ids={graded_ids}, student_answers keys={list(student_answers.keys())}")
        for q in questions_meta:
            qid = q.get("id", "")
            if qid not in graded_ids:
                pts = q.get("points", 0)
                total_points += pts
                qtype = q.get("type", "")
                student_ans = str(student_answers.get(qid, "")).strip().lower()
                correct_ans = str(q.get("answer", "")).strip().lower()
                if qtype in ("choice", "true_false") and correct_ans:
                    is_correct = student_ans == correct_ans
                    earned = pts if is_correct else 0
                    total_score += earned
                    graded_questions.append({
                        "id": qid,
                        "graded": True,
                        "studentScore": earned,
                        "maxScore": pts,
                        "comment": "回答正确" if is_correct else f"回答错误，正确答案: {q.get('answer', '')}",
                    })
                else:
                    graded_questions.append({
                        "id": qid,
                        "graded": False,
                        "studentScore": 0,
                        "maxScore": pts,
                        "comment": "",
                    })

        score_pct = round((total_score / max(total_points, 1)) * 100)
        feedback_data = {
            "questions": graded_questions,
            "score": score_pct,
            "feedback": payload.get("feedback", ""),
            "strengths": [],
            "improvements": [],
        }
        submission_update = {
            "status": "graded",
            "score": score_pct,
            "feedback": feedback_data,
            "graded_at": datetime.utcnow(),
            "graded_by": user_id,
        }
    else:
        # Simple overall score/feedback (legacy path)
        submission_update = {
            "status": "graded",
            "score": payload.get("score", 0),
            "feedback": payload.get("feedback", {}),
            "graded_at": datetime.utcnow(),
            "graded_by": user_id,
        }

    updated = await storage.update_submission(submission["id"], submission_update)
    logger.info("Homework {} graded for student {} in course {}", hw_id, student_id, course_id)
    return http_json_response({"ok": True, "submission": updated})


async def handle_ai_grade(
    request: WsRequest,
    storage: StorageWrapper,
    course_id: str,
    hw_id: str,
    *,
    identity: dict[str, str],
) -> Response:
    """AI-powered grading for homework submissions."""
    from nanobot.api.ai_grade import grade_submission

    user_id = identity.get("user_id", "")
    course = await storage.get_course(course_id)
    if not course:
        return http_error(404, "Course not found")
    teacher_id = course.get("teacherId") or course.get("teacher_id", "")
    if teacher_id != user_id:
        return http_error(403, "Only the course owner can AI grade")

    query = parse_query(request.path)
    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload

    student_id = payload.get("studentId", "").strip()
    if not student_id:
        return http_error(400, "studentId is required")

    submission = await storage.get_submission(hw_id, student_id)
    if not submission:
        return http_error(404, "Submission not found")

    hw = await storage.get_homework(hw_id)
    if not hw:
        return http_error(404, "Homework not found")

    settings = hw.get("settings") or {}
    questions = settings.get("questions") or hw.get("questions") or []
    answers = submission.get("answers") or {}

    if not questions:
        return http_error(400, "No questions found for this homework")

    try:
        result = await grade_submission(questions, answers)
    except Exception as e:
        logger.error("AI grading failed: {}", e)
        return http_error(500, f"AI grading failed: {e}")

    feedback_data = {
        "overall": result.get("feedback", ""),
        "questions": {q["id"]: q.get("comment", "") for q in result.get("questions", [])},
    }
    submission_update = {
        "status": "graded",
        "score": result["score"],
        "feedback": feedback_data,
        "graded_at": datetime.now(timezone.utc),
        "graded_by": user_id,
    }
    updated = await storage.update_submission(submission["id"], submission_update)

    return http_json_response({
        "ok": True,
        "submission": updated,
        "questions": result["questions"],
        "score": result["score"],
        "rubric": result["rubric"],
        "feedback": result["feedback"],
        "strengths": result["strengths"],
        "improvements": result["improvements"],
    })


async def handle_homework_publish(
    request: WsRequest,
    storage: StorageWrapper,
    course_id: str,
    hw_id: str,
    *,
    identity: dict[str, str],
) -> Response:
    """Publish a draft homework assignment."""
    user_id = identity.get("user_id", "")
    course = await storage.get_course(course_id)
    if not course:
        return http_error(404, "Course not found")
    teacher_id = course.get("teacherId") or course.get("teacher_id", "")
    if teacher_id != user_id:
        return http_error(403, "Only the course owner can publish homework")
    hw = await storage.get_homework(hw_id)
    if not hw:
        return http_error(404, "Homework not found")
    if hw.get("status") == "published":
        return http_error(400, "Homework is already published")

    updated = await storage.update_homework(hw_id, {"status": "published"})
    if updated:
        logger.info("Homework {} published in course {} by {}", hw_id, course_id, user_id)
        return http_json_response({"ok": True, "homework": updated})
    return http_error(500, "Failed to publish homework")


async def handle_homework_delete(
    request: WsRequest,
    storage: StorageWrapper,
    course_id: str,
    hw_id: str,
    *,
    identity: dict[str, str],
) -> Response:
    user_id = identity.get("user_id", "")
    course = await storage.get_course(course_id)
    if not course:
        return http_error(404, "Course not found")
    teacher_id = course.get("teacherId") or course.get("teacher_id", "")
    if teacher_id != user_id:
        return http_error(403, "Only the course owner can delete homework")
    hw = await storage.get_homework(hw_id)
    if not hw:
        return http_error(404, "Homework not found")
    success = await storage.delete_homework(hw_id)
    if success:
        logger.info("Homework {} deleted from course {} by {}", hw_id, course_id, user_id)
        return http_json_response({"ok": True})
    return http_error(500, "Failed to delete homework")


async def handle_ai_grade_question(
    request: WsRequest,
    storage: StorageWrapper,
    course_id: str,
    hw_id: str,
    *,
    identity: dict[str, str],
) -> Response:
    """AI-grade a single subjective question."""
    logger.info("[ai_grade_question] called, path={}", request.path)
    query = parse_query(request.path)
    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        logger.warning("[ai_grade_question] bad payload")
        return payload

    question_content = payload.get("content", "")
    max_score = payload.get("maxScore", 10)
    reference_answer = payload.get("referenceAnswer", "")
    student_answer = payload.get("studentAnswer", "")
    logger.info("[ai_grade_question] content={}, maxScore={}", question_content[:30], max_score)

    try:
        result = await grade_single_question(
            question_content=question_content,
            max_score=max_score,
            reference_answer=reference_answer,
            student_answer=student_answer,
        )
        logger.info("[ai_grade_question] result: {}", result)
        return http_json_response({"ok": True, "score": result["score"], "comment": result["comment"]})
    except Exception as e:
        logger.error("[ai_grade_question] exception: {}", e)
        return http_error(500, str(e))


async def handle_ai_grade_cropgpt(
    request: WsRequest,
    storage: StorageWrapper,
    course_id: str,
    hw_id: str,
    *,
    identity: dict[str, str],
) -> Response:
    """CropGPT vision model evaluation — dual-model grading lane 1.

    Stub: returns mock evaluation data. Implement vision model call here
    (e.g. plant disease image analysis for internship reports).
    """
    role = identity.get("role", "")
    user_id = identity.get("user_id", "")
    if role != "teacher":
        return http_error(403, "Only teachers can use AI grading")

    course = await storage.get_course(course_id)
    if not course:
        return http_error(404, "Course not found")
    teacher_id = course.get("teacherId") or course.get("teacher_id", "")
    if teacher_id != user_id:
        return http_error(403, "Only the course owner can use AI grading")

    query = parse_query(request.path)
    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload

    student_id = payload.get("studentId", "").strip()
    if not student_id:
        return http_error(400, "studentId is required")

    submission = await storage.get_submission(hw_id, student_id)
    if not submission:
        return http_error(404, "Submission not found")

    hw = await storage.get_homework(hw_id)
    if not hw:
        return http_error(404, "Homework not found")

    logger.info(
        "[cropgpt] stub called for hw={}, student={}, course={}",
        hw_id, student_id, course_id,
    )

    # --- Stub: replace with real CropGPT vision model call ---
    # TODO: Call CropGPT API with report images/submission content
    # Returns: { score, feedback, strengths, improvements, vision_analysis }
    return http_json_response({
        "ok": True,
        "stub": True,
        "model": "cropgpt-vision",
        "score": None,  # teacher reviews & confirms
        "feedback": "🌾 CropGPT 视觉评估结果（接口预留中）：请上传实习报告中的病害图像，CropGPT 将自动识别病害类型、严重程度并提供评分建议。",
        "strengths": ["接口预留 - CropGPT 视觉分析赋能"],
        "improvements": [{"title": "等待接入", "detail": "CropGPT 视觉模型接口已预留，待后续实现"}],
        "visionAnalysis": None,
    })


async def handle_ai_grade_general(
    request: WsRequest,
    storage: StorageWrapper,
    course_id: str,
    hw_id: str,
    *,
    identity: dict[str, str],
) -> Response:
    """General LLM model evaluation — dual-model grading lane 2.

    Stub: returns mock evaluation data. Implement general-purpose LLM call here
    (e.g. text content quality, logic, completeness assessment).
    """
    role = identity.get("role", "")
    user_id = identity.get("user_id", "")
    if role != "teacher":
        return http_error(403, "Only teachers can use AI grading")

    course = await storage.get_course(course_id)
    if not course:
        return http_error(404, "Course not found")
    teacher_id = course.get("teacherId") or course.get("teacher_id", "")
    if teacher_id != user_id:
        return http_error(403, "Only the course owner can use AI grading")

    query = parse_query(request.path)
    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload

    student_id = payload.get("studentId", "").strip()
    if not student_id:
        return http_error(400, "studentId is required")

    submission = await storage.get_submission(hw_id, student_id)
    if not submission:
        return http_error(404, "Submission not found")

    hw = await storage.get_homework(hw_id)
    if not hw:
        return http_error(404, "Homework not found")

    logger.info(
        "[general-ai] stub called for hw={}, student={}, course={}",
        hw_id, student_id, course_id,
    )

    # --- Stub: replace with real general LLM model evaluation ---
    # TODO: Call general LLM API with submission content
    # Returns: { score, feedback, strengths, improvements, logic_assessment }
    return http_json_response({
        "ok": True,
        "stub": True,
        "model": "general-llm",
        "score": None,  # teacher reviews & confirms
        "feedback": "🤖 通用模型评估结果（接口预留中）：将对报告的逻辑结构、内容完整性、语言表达进行综合评分。",
        "strengths": ["接口预留 - 通用大模型文本评估"],
        "improvements": [{"title": "等待接入", "detail": "通用模型评估接口已预留，待后续实现"}],
        "logicAssessment": None,
    })


async def handle_ai_generate_questions(
    request: WsRequest,
    storage: StorageWrapper,
    course_id: str,
    *,
    identity: dict[str, str],
) -> Response:
    """Generate questions from knowledge content using AI."""
    from nanobot.api.ai_generate_questions import generate_questions

    role = identity.get("role", "")
    user_id = identity.get("user_id", "")

    if role != "teacher":
        return http_error(403, "Only teachers can generate questions")

    course = await storage.get_course(course_id)
    if not course:
        return http_error(404, "Course not found")
    teacher_id = course.get("teacherId") or course.get("teacher_id", "")
    if teacher_id != user_id:
        return http_error(403, "Only the course owner can generate questions")

    query = parse_query(request.path)
    payload = parse_mutation_data(query)
    if isinstance(payload, Response):
        return payload

    content = payload.get("content", "").strip()
    if not content:
        return http_error(400, "content is required")

    num_questions = payload.get("numQuestions", 10)
    try:
        num_questions = int(num_questions)
        if num_questions < 1 or num_questions > 50:
            return http_error(400, "numQuestions must be between 1 and 50")
    except (ValueError, TypeError):
        return http_error(400, "numQuestions must be a number")

    type_distribution = payload.get("typeDistribution", {})

    logger.info(
        "[ai_generate_questions] user={}, course={}, num_questions={}, types={}",
        user_id, course_id, num_questions, type_distribution,
    )

    try:
        result = await generate_questions(
            content=content,
            num_questions=num_questions,
            type_distribution=type_distribution if type_distribution else None,
        )
        return http_json_response({
            "ok": True,
            "questions": result["questions"],
            "totalPoints": result["total_points"],
        })
    except Exception as e:
        logger.error("[ai_generate_questions] failed: {}", e)
        return http_error(500, str(e))
