"""AI tutoring evaluation logic.

Provides AI-powered analysis of student answers in the tutoring assistant,
returning structured feedback including knowledge point assessment,
error analysis, and learning strategies.
"""

from __future__ import annotations

import asyncio
import json

from loguru import logger

from .llm_utils import make_llm_provider

LLM_TIMEOUT_S = 60


def _build_eval_prompt(question: str, student_answer: str, profile_context: str = "", reference_answer: str = "") -> str:
    """Build the LLM prompt for evaluating a student's answer in tutor mode."""
    parts = [
        "你是一位专业的学科辅导老师。请分析以下学生的解答，给出详细的评估。",
        "请严格按照 JSON 格式返回结果，不要包含任何其他文字。\n",
    ]

    if profile_context:
        parts.append(f"## 学生学习画像\n{profile_context}\n")

    parts.append(f"## 题目\n{question}\n")

    if reference_answer:
        parts.append(f"## 参考答案/解析\n{reference_answer}\n")

    parts.append(f"## 学生解答\n{student_answer or '(未作答)'}\n")

    parts.append("""请返回以下 JSON 格式（不要包含 markdown 代码块标记）：
注意：如果有参考答案，请将学生解答与参考答案对比分析，判断正确性。
{
  "is_correct": true或false,
  "score": 得分(0-100的数字),
  "analysis": "对解答的详细分析(100字以内)",
  "knowledge_points": [
    {
      "title": "涉及的知识点名称",
      "formula": "相关公式(如有)",
      "mastery_delta": 掌握度变化(-0.3到0.3之间，正数表示掌握提升，负数表示下降)
    }
  ],
  "error_type": "错误类型(如：概念错误/计算疏忽/方法不当/回答不完整)，正确时为空字符串",
  "error_detail": "错误的具体说明，正确时为空字符串",
  "strategy": "针对性的学习建议(50字以内)"
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


async def evaluate_student_answer(
    question: str,
    student_answer: str,
    profile_context: str = "",
    reference_answer: str = "",
) -> dict:
    """Evaluate a student's answer using AI in tutor mode.

    Args:
        question: The question content
        student_answer: The student's answer text
        profile_context: Optional string summarizing the student's learning history
        reference_answer: Optional reference answer/explanation for more accurate evaluation

    Returns:
        dict with keys: is_correct, score, analysis, knowledge_points,
        error_type, error_detail, strategy
    """
    prompt = _build_eval_prompt(question, student_answer, profile_context, reference_answer)

    try:
        provider, model = make_llm_provider()
        messages = [{"role": "user", "content": prompt}]
        response = await asyncio.wait_for(
            provider.chat_stream(messages=messages, model=model, temperature=0.3),
            timeout=LLM_TIMEOUT_S,
        )
        result = _parse_ai_response(response.content or "{}")

        # Validate and normalize fields
        is_correct = bool(result.get("is_correct", False))
        score = max(0, min(100, int(result.get("score", 0))))
        analysis = str(result.get("analysis", ""))[:200]
        error_type = str(result.get("error_type", "")) if not is_correct else ""
        error_detail = str(result.get("error_detail", "")) if not is_correct else ""
        strategy = str(result.get("strategy", ""))[:100]

        knowledge_points = []
        for kp in result.get("knowledge_points", []):
            if isinstance(kp, dict) and kp.get("title"):
                knowledge_points.append({
                    "title": str(kp["title"]),
                    "formula": str(kp.get("formula", "")),
                    "mastery_delta": max(-0.3, min(0.3, float(kp.get("mastery_delta", 0)))),
                })

        return {
            "is_correct": is_correct,
            "score": score,
            "analysis": analysis,
            "knowledge_points": knowledge_points,
            "error_type": error_type,
            "error_detail": error_detail,
            "strategy": strategy,
        }
    except Exception as e:
        logger.error("AI tutor evaluation failed: {} - {}", type(e).__name__, e)
        # Fallback: basic heuristic
        ans_len = len(student_answer or "")
        if ans_len > 100:
            return {
                "is_correct": True,
                "score": 75,
                "analysis": "回答较为详细，但无法进行深度分析。（AI 评阅失败，已使用基础评分）",
                "knowledge_points": [],
                "error_type": "",
                "error_detail": "",
                "strategy": "建议继续练习，巩固所学知识。",
            }
        elif ans_len > 30:
            return {
                "is_correct": False,
                "score": 45,
                "analysis": "回答偏简略，建议展开论述。（AI 评阅失败，已使用基础评分）",
                "knowledge_points": [],
                "error_type": "回答不完整",
                "error_detail": "解答过于简略，无法充分展示理解。",
                "strategy": "请写出具体的计算步骤或分析过程。",
            }
        else:
            return {
                "is_correct": False,
                "score": 20,
                "analysis": "回答过于简略。（AI 评阅失败，已使用基础评分）",
                "knowledge_points": [],
                "error_type": "回答不完整",
                "error_detail": "几乎没有提供有效信息。",
                "strategy": "请认真阅读题目，尝试写出你的思路。",
            }
