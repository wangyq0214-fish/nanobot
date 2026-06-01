"""AI-powered question generation for homework."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from loguru import logger

from .llm_utils import make_llm_provider

# Timeout for LLM calls in seconds.
LLM_TIMEOUT_S = 90

# Supported question types
QUESTION_TYPES = {
    "choice": "选择题",
    "true_false": "判断题",
    "fill": "填空题",
    "short_answer": "简答题",
    "essay": "论述题",
}


def _build_generation_prompt(
    content: str,
    num_questions: int,
    type_distribution: dict[str, int],
) -> str:
    """Build the LLM prompt for generating questions.

    Args:
        content: The knowledge content to base questions on.
        num_questions: Total number of questions to generate.
        type_distribution: Dict mapping question type to count.
    """
    type_desc = []
    for qtype, count in type_distribution.items():
        if count > 0 and qtype in QUESTION_TYPES:
            type_desc.append(f"- {QUESTION_TYPES[qtype]}: {count}道")

    type_dist_str = "\n".join(type_desc) if type_desc else f"- 根据内容自动分配（共{num_questions}道）"

    prompt = f"""你是一位专业的教育工作者和出题专家。请根据以下知识内容，生成高质量的作业题目。

## 知识内容
{content}

## 出题要求
1. 题目总数：{num_questions}道
2. 题型分布：
{type_dist_str}
3. 题目要求：
   - 紧扣提供的知识内容
   - 难度适中，适合学生练习
   - 选择题需要4个选项（A/B/C/D）
   - 每道题都需要提供参考答案
   - 简答题和论述题需要提供评分要点

## 返回格式
请严格按照以下 JSON 格式返回（不要包含 markdown 代码块标记）：
{{
  "questions": [
    {{
      "id": "q1",
      "type": "choice",
      "content": "题目内容",
      "options": [
        {{"key": "A", "text": "选项A内容"}},
        {{"key": "B", "text": "选项B内容"}},
        {{"key": "C", "text": "选项C内容"}},
        {{"key": "D", "text": "选项D内容"}}
      ],
      "answer": "A",
      "points": 10,
      "explanation": "解析说明"
    }},
    {{
      "id": "q2",
      "type": "true_false",
      "content": "判断题内容",
      "answer": "true",
      "points": 5,
      "explanation": "解析说明"
    }},
    {{
      "id": "q3",
      "type": "fill",
      "content": "填空题内容，____部分为填空",
      "answer": "正确答案",
      "points": 10,
      "explanation": "解析说明"
    }},
    {{
      "id": "q4",
      "type": "short_answer",
      "content": "简答题内容",
      "answer": "参考答案要点",
      "points": 15,
      "explanation": "评分要点说明"
    }},
    {{
      "id": "q5",
      "type": "essay",
      "content": "论述题内容",
      "answer": "参考答案要点",
      "points": 20,
      "explanation": "评分要点说明"
    }}
  ]
}}

注意：
- 每道题的 id 格式为 q1, q2, q3...
- 选择题的 options 必须是数组，每个元素包含 key 和 text
- 判断题的 answer 只能是 "true" 或 "false"
- 填空题的 content 中用 ____ 标记填空位置
- points 为每道题的分值，请合理分配
- explanation 用于解析或评分要点"""

    return prompt


def _parse_ai_response(content: str) -> dict:
    """Parse the LLM response, stripping markdown code blocks if present."""
    content = content.strip()
    if content.startswith("```"):
        # Remove markdown code block markers
        lines = content.split("\n")
        # Find the end of code block
        for i, line in enumerate(lines):
            if line.strip() == "```":
                content = "\n".join(lines[1:i])
                break
        else:
            content = "\n".join(lines[1:])
    if content.endswith("```"):
        content = content.rsplit("```", 1)[0]
    content = content.strip()
    return json.loads(content)


def _validate_and_normalize_questions(
    questions: list[dict],
    type_distribution: dict[str, int],
) -> list[dict]:
    """Validate and normalize generated questions."""
    normalized = []
    seen_ids = set()

    for i, q in enumerate(questions):
        # Ensure unique ID
        qid = q.get("id", f"q{i+1}")
        if qid in seen_ids:
            qid = f"q{i+1}"
        seen_ids.add(qid)

        qtype = q.get("type", "short_answer")
        if qtype not in QUESTION_TYPES:
            qtype = "short_answer"

        # Normalize based on type
        normalized_q = {
            "id": qid,
            "type": qtype,
            "content": q.get("content", "").strip(),
            "points": max(1, min(100, int(q.get("points", 10)))),
        }

        if qtype == "choice":
            options = q.get("options", [])
            if isinstance(options, list) and len(options) >= 2:
                normalized_q["options"] = [
                    {"key": opt.get("key", chr(65 + j)), "text": opt.get("text", "")}
                    for j, opt in enumerate(options[:6])  # Max 6 options
                ]
            else:
                # Generate default options
                normalized_q["options"] = [
                    {"key": "A", "text": ""},
                    {"key": "B", "text": ""},
                    {"key": "C", "text": ""},
                    {"key": "D", "text": ""},
                ]
            normalized_q["answer"] = q.get("answer", "A")

        elif qtype == "true_false":
            normalized_q["answer"] = str(q.get("answer", "true")).lower()

        elif qtype == "fill":
            normalized_q["answer"] = q.get("answer", "")

        else:  # short_answer, essay
            normalized_q["answer"] = q.get("answer", "")

        # Add explanation if present
        if "explanation" in q:
            normalized_q["explanation"] = q["explanation"]

        normalized.append(normalized_q)

    return normalized


async def generate_questions(
    content: str,
    num_questions: int,
    type_distribution: dict[str, int] | None = None,
) -> dict:
    """Generate questions from knowledge content using AI.

    Args:
        content: The knowledge content to base questions on.
        num_questions: Total number of questions to generate.
        type_distribution: Optional dict mapping question type to count.
            If None, AI will distribute types automatically.

    Returns:
        dict with keys: questions, total_points
    """
    if not content.strip():
        raise ValueError("知识内容不能为空")

    if num_questions < 1 or num_questions > 50:
        raise ValueError("题目数量必须在1-50之间")

    # Default type distribution if not provided
    if type_distribution is None:
        type_distribution = {}

    provider, model = make_llm_provider()
    prompt = _build_generation_prompt(content, num_questions, type_distribution)

    logger.info(
        "[generate_questions] Calling LLM with {} questions, types={}",
        num_questions,
        type_distribution,
    )

    try:
        messages = [{"role": "user", "content": prompt}]
        response = await asyncio.wait_for(
            provider.chat_stream(messages=messages, model=model, temperature=0.7),
            timeout=LLM_TIMEOUT_S,
        )
        logger.info(
            "[generate_questions] LLM responded, content_len={}",
            len(response.content or ""),
        )
        result = _parse_ai_response(response.content or "{}")
    except asyncio.TimeoutError:
        logger.error("[generate_questions] LLM call timed out")
        raise RuntimeError("AI生成超时，请稍后重试")
    except json.JSONDecodeError as e:
        logger.error("[generate_questions] Failed to parse JSON: {}", e)
        raise RuntimeError("AI返回格式错误，请重试")
    except Exception as e:
        logger.error("[generate_questions] LLM call failed: {}", type(e).__name__, e)
        raise RuntimeError(f"AI生成失败: {e}")

    questions = result.get("questions", [])
    if not questions:
        raise RuntimeError("AI未能生成题目，请重试")

    # Validate and normalize
    normalized = _validate_and_normalize_questions(questions, type_distribution)

    # Calculate total points
    total_points = sum(q.get("points", 10) for q in normalized)

    return {
        "questions": normalized,
        "total_points": total_points,
    }
