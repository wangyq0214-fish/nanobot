"""AI text polishing for the writing assistant."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from loguru import logger

from .llm_utils import make_llm_provider

LLM_TIMEOUT_S = 60

MODE_INSTRUCTIONS = {
    "polish": "润色以下学术文本，修正语法错误、改善表达流畅度，保持原意不变。",
    "rewrite": "以更学术化的风格改写以下段落，使用更正式的学术用语和句式。",
    "concise": "精简以下文本，去除冗余表达，保留核心论点，使表达更简洁有力。",
    "expand": "扩展以下段落，补充论证细节、过渡句或例证，使论述更充分完整。",
}


def _build_polish_prompt(text: str, mode: str) -> str:
    """Build the LLM prompt for text polishing."""
    mode_desc = MODE_INSTRUCTIONS.get(mode, MODE_INSTRUCTIONS["polish"])
    return f"""你是一位专业的学术写作助手，擅长中英文学术论文的润色和改写。

任务：{mode_desc}

要求：
1. 保持原文的核心含义和学术准确性
2. 如果是中文文本，保持中文输出；如果是英文文本，保持英文输出
3. 只返回润色后的文本，不要添加解释或说明
4. 保留原文的段落结构

原文：
{text}"""


def _parse_polish_response(content: str) -> str:
    """Extract polished text from LLM response."""
    content = content.strip()
    # Strip markdown code fences if present
    if content.startswith("```"):
        content = content.split("\n", 1)[-1]
    if content.endswith("```"):
        content = content.rsplit("```", 1)[0]
    return content.strip()


async def polish_text(text: str, mode: str = "polish") -> dict[str, Any]:
    """Polish academic text using LLM.

    Args:
        text: The text to polish.
        mode: One of 'polish', 'rewrite', 'concise', 'expand'.

    Returns:
        dict with 'polished_text' key, or 'error' on failure.
    """
    if not text or not text.strip():
        return {"polished_text": "", "error": "empty text"}

    if mode not in MODE_INSTRUCTIONS:
        mode = "polish"

    try:
        provider, model = make_llm_provider()
        prompt = _build_polish_prompt(text, mode)
        messages = [{"role": "user", "content": prompt}]

        response = await asyncio.wait_for(
            provider.chat_stream(messages=messages, model=model, temperature=0.3),
            timeout=LLM_TIMEOUT_S,
        )

        result_text = _parse_polish_response(response.content or "")
        if not result_text:
            return {"polished_text": text, "error": "AI returned empty response"}

        return {"polished_text": result_text}

    except asyncio.TimeoutError:
        logger.warning("[ai_polish] LLM call timed out after {}s", LLM_TIMEOUT_S)
        return {"polished_text": text, "error": "AI 处理超时，请稍后重试"}
    except Exception as e:
        logger.error("[ai_polish] LLM call failed: {}", e)
        return {"polished_text": text, "error": f"AI 处理失败: {e}"}
