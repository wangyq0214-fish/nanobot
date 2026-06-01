"""AI grading logic for homework submissions."""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any

from loguru import logger

from .llm_utils import make_llm_provider

# Timeout for LLM calls in seconds.
LLM_TIMEOUT_S = 60

# Question types considered objective (auto-gradable without LLM)
OBJECTIVE_TYPES = {"choice", "true_false", "fill", "blank"}


def _build_grading_prompt(questions: list[dict], answers: dict) -> str:
    """Build the LLM prompt for grading subjective questions."""
    parts = [
        "你是一位专业的作业批改助手。请对以下学生的主观题答案进行评分。",
        "请严格按照 JSON 格式返回结果，不要包含任何其他文字。\n",
    ]

    for i, q in enumerate(questions):
        qid = q.get("id", "")
        answer = answers.get(qid, answers.get(f"q{i+1}", ""))
        parts.append(f"## 题目 [{qid}]")
        parts.append(f"内容：{q.get('content', '')}")
        parts.append(f"分值：{q.get('points', 25)}分")
        if q.get("answer"):
            parts.append(f"参考答案：{q['answer']}")
        parts.append(f"学生答案：{answer or '(未作答)'}\n")

    parts.append("""请返回以下 JSON 格式（不要包含 markdown 代码块标记）：
{
  "results": [
    {
      "questionId": "题目ID",
      "score": 得分(数字),
      "comment": "评语(50字以内)"
    }
  ],
  "totalScore": 总得分(所有主观题得分之和),
  "overallComment": "综合评语(80字以内)",
  "strengths": ["优点1", "优点2"],
  "improvements": [{"title": "改进方向", "detail": "具体建议"}]
}""")

    return "\n".join(parts)


def _parse_ai_response(content: str) -> dict:
    """Parse the LLM response, stripping markdown code blocks if present."""
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[-1]
    if content.endswith("```"):
        content = content.rsplit("```", 1)[0]
    content = content.strip()
    return json.loads(content)


def _grade_objective(question: dict, answer: str) -> dict:
    """Grade a single objective question (choice/tf/fill)."""
    qtype = question.get("type", "")
    pts = question.get("points", 0)
    correct = (question.get("answer") or "").strip()
    given = (answer or "").strip()

    if qtype == "choice":
        is_correct = given.upper() == correct.upper()
    elif qtype == "true_false":
        is_correct = given.lower() == correct.lower()
    elif qtype in ("fill", "blank"):
        if given and correct:
            if given.lower() == correct.lower():
                is_correct = True
            elif correct.lower() in given.lower() or given.lower() in correct.lower():
                return {"score": pts // 2, "comment": "部分正确"}
            else:
                is_correct = False
        else:
            is_correct = False
    else:
        is_correct = False

    return {
        "score": pts if is_correct else 0,
        "comment": "正确" if is_correct else "错误",
    }


def _build_rubric(score_pct: int, ai_rubric: Any) -> list[dict]:
    """Build or generate grading rubric."""
    if isinstance(ai_rubric, dict) and ai_rubric:
        return [{"name": k, "score": v, "max": 20} for k, v in ai_rubric.items()]

    base = score_pct / 100
    return [
        {"name": "基础知识", "score": round(16 * base + 4), "max": 20},
        {"name": "内容理解", "score": round(15 * base + 5), "max": 20},
        {"name": "分析深度", "score": round(14 * base + 4), "max": 20},
        {"name": "语言表达", "score": round(14 * base + 3), "max": 20},
        {"name": "综合评价", "score": round(13 * base + 3), "max": 20},
    ]


async def grade_submission(
    questions: list[dict],
    answers: dict,
) -> dict:
    """Grade a homework submission using AI for subjective questions.

    Args:
        questions: List of question dicts with id, type, content, points, answer
        answers: Dict mapping question id to student answer

    Returns:
        dict with keys: questions, score, rubric, feedback, strengths, improvements
    """
    # Normalize field names (frontend may send stem/objType/maxScore)
    for q in questions:
        if "objType" in q and "type" not in q:
            q["type"] = q["objType"]
        if "stem" in q and "content" not in q:
            q["content"] = q["stem"]
        if "maxScore" in q and "points" not in q:
            q["points"] = q["maxScore"]

    # Split questions into objective and subjective
    subjective_qs = [q for q in questions if q.get("type") not in OBJECTIVE_TYPES]

    # Grade objective questions locally
    graded_questions = []
    obj_score = 0
    obj_total = 0

    for q in questions:
        qid = q.get("id", "")
        qtype = q.get("type", "")
        pts = q.get("points", 0)
        student_ans = answers.get(qid, "")

        if qtype in OBJECTIVE_TYPES:
            result = _grade_objective(q, student_ans)
            obj_score += result["score"]
            obj_total += pts
            graded_questions.append({
                "id": qid,
                "graded": True,
                "studentScore": result["score"],
                "maxScore": pts,
                "comment": result["comment"],
            })
        else:
            # Placeholder — will be filled by AI
            graded_questions.append({
                "id": qid,
                "graded": True,
                "studentScore": 0,
                "maxScore": pts,
                "comment": "",
            })

    # Call LLM for subjective questions
    ai_result = {"results": [], "totalScore": 0, "overallComment": "", "strengths": [], "improvements": []}

    if subjective_qs:
        try:
            provider, model = make_llm_provider()
            prompt = _build_grading_prompt(subjective_qs, answers)
            messages = [{"role": "user", "content": prompt}]
            response = await asyncio.wait_for(
                provider.chat_stream(messages=messages, model=model, temperature=0.3),
                timeout=LLM_TIMEOUT_S,
            )
            ai_result = _parse_ai_response(response.content or "{}")
        except Exception as e:
            logger.error("AI grading failed: {} - {}", type(e).__name__, e)
            # Fall back to length-based grading
            for q in subjective_qs:
                qid = q.get("id", "")
                pts = q.get("points", 25)
                ans_len = len(answers.get(qid, "") or "")
                if ans_len > 150:
                    score, comment = round(pts * 0.9), "回答详细，条理清晰。"
                elif ans_len > 80:
                    score, comment = round(pts * 0.72), "回答基本完整，可进一步展开。"
                elif ans_len > 30:
                    score, comment = round(pts * 0.5), "回答偏简略，建议展开论述。"
                else:
                    score, comment = round(pts * 0.3), "回答过于简略，需充分展开。"
                ai_result["results"].append({"questionId": qid, "score": score, "comment": comment})
                ai_result["totalScore"] += score
            ai_result["overallComment"] = "（AI 评阅失败，已使用基础评分）"
            ai_result["strengths"] = ["完成了全部题目"]
            ai_result["improvements"] = [{"title": "继续努力", "detail": "加强日常练习和阅读积累。"}]

    # Merge AI results into graded questions
    ai_results_map = {r.get("questionId"): r for r in ai_result.get("results", [])}
    ai_subj_score = 0
    matched_count = 0

    for gq in graded_questions:
        if gq["id"] in ai_results_map:
            ai_q = ai_results_map[gq["id"]]
            gq["studentScore"] = ai_q.get("score", 0)
            gq["comment"] = ai_q.get("comment", "")
            ai_subj_score += gq["studentScore"]
            matched_count += 1

    # Only use totalScore as fallback when NO individual results were matched
    # (avoids hallucinated totalScore overriding actual 0 scores)
    if ai_result.get("totalScore") and matched_count == 0:
        ai_subj_score = ai_result["totalScore"]

    # Calculate final score
    total_score = obj_score + ai_subj_score
    total_points = sum(q.get("points", 0) for q in questions)
    score_pct = round((total_score / max(total_points, 1)) * 100)

    return {
        "questions": graded_questions,
        "score": score_pct,
        "rubric": _build_rubric(score_pct, ai_result.get("rubric")),
        "feedback": ai_result.get("overallComment", ""),
        "strengths": ai_result.get("strengths", ["完成全部题目", "作答态度认真"]),
        "improvements": ai_result.get("improvements", [
            {"title": "继续努力", "detail": "加强日常练习和阅读积累。"}
        ]),
    }


async def grade_single_question(
    question_content: str,
    max_score: int,
    reference_answer: str,
    student_answer: str,
) -> dict:
    """Grade a single subjective question using AI.

    Returns:
        dict with keys: score, comment
    """
    prompt = (
        "你是一位专业的作业批改助手。请对以下学生的主观题答案进行评分。\n"
        "请严格按照 JSON 格式返回结果，不要包含任何其他文字。\n\n"
        f"题目内容：{question_content}\n"
        f"分值：{max_score}分\n"
    )
    if reference_answer:
        prompt += f"参考答案：{reference_answer}\n"
    prompt += f"学生答案：{student_answer or '(未作答)'}\n\n"
    prompt += (
        '请返回以下 JSON 格式（不要包含 markdown 代码块标记）：\n'
        '{"score": 得分(数字), "comment": "评语(50字以内)"}'
    )

    try:
        logger.info("[grade_single_question] creating LLM provider")
        provider, model = make_llm_provider()
        logger.info("[grade_single_question] calling LLM (streaming), model={}", model)
        messages = [{"role": "user", "content": prompt}]
        # Use streaming to keep the connection alive during LLM processing.
        # Non-streaming calls block for 25-35s with no data flow, which can
        # cause proxy/client timeouts (agent chat avoids this via WS streaming).
        response = await asyncio.wait_for(
            provider.chat_stream(messages=messages, model=model, temperature=0.3),
            timeout=LLM_TIMEOUT_S,
        )
        logger.info("[grade_single_question] LLM responded, content_len={}", len(response.content or ""))
        result = _parse_ai_response(response.content or "{}")
        score = min(int(result.get("score", 0)), max_score)
        comment = result.get("comment", "")
        return {"score": score, "comment": comment}
    except Exception as e:
        logger.error("Single question AI grading failed: {} - {}", type(e).__name__, e)
        # Fallback: length-based heuristic
        ans_len = len(student_answer or "")
        if ans_len > 150:
            return {"score": round(max_score * 0.9), "comment": "回答详细，条理清晰。(AI 评阅失败，已使用基础评分)"}
        elif ans_len > 80:
            return {"score": round(max_score * 0.72), "comment": "回答基本完整，可进一步展开。(AI 评阅失败，已使用基础评分)"}
        elif ans_len > 30:
            return {"score": round(max_score * 0.5), "comment": "回答偏简略，建议展开论述。(AI 评阅失败，已使用基础评分)"}
        else:
            return {"score": round(max_score * 0.3), "comment": "回答过于简略，需充分展开。(AI 评阅失败，已使用基础评分)"}
