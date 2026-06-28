"""AI-powered paper summarization."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from loguru import logger

from .llm_utils import make_llm_provider

LLM_TIMEOUT_S = 120

SUMMARY_PROMPT_TEMPLATE = """你是一位专业的学术论文分析助手。请对以下论文全文进行结构化摘要分析。

要求输出以下五个部分（使用 Markdown 格式）：

## 概述
简要介绍论文的研究背景和主要贡献（3-5句话）

## 研究方法
描述论文采用的核心研究方法和技术路线（2-4句话）

## 关键创新
列出论文的2-4个主要创新点（使用编号列表）

## 主要结论
总结论文的核心发现和结论（2-4句话）

## 关键词
提取5-8个关键词（使用逗号分隔）

论文全文：
{full_text}"""


def _build_summary_prompt(full_text: str) -> str:
    """Build the prompt for paper summarization."""
    # Truncate to ~50k chars to stay within context limits
    max_chars = 50000
    if len(full_text) > max_chars:
        full_text = full_text[:max_chars] + "\n\n[文本已截断...]"
    return SUMMARY_PROMPT_TEMPLATE.format(full_text=full_text)


def _parse_summary_response(content: str) -> str:
    """Extract summary from LLM response."""
    content = content.strip()
    # Strip markdown code fences if present
    if content.startswith("```"):
        content = content.split("\n", 1)[-1]
    if content.endswith("```"):
        content = content.rsplit("```", 1)[0]
    return content.strip()


async def generate_paper_summary(full_text: str) -> dict[str, Any]:
    """Generate a structured summary for a paper.

    Args:
        full_text: The full text of the paper.

    Returns:
        dict with 'summary' key, or 'error' on failure.
    """
    if not full_text or not full_text.strip():
        return {"summary": "", "error": "empty paper text"}

    try:
        provider, model = make_llm_provider()
        prompt = _build_summary_prompt(full_text)
        messages = [{"role": "user", "content": prompt}]

        response = await asyncio.wait_for(
            provider.chat_stream(messages=messages, model=model, temperature=0.3),
            timeout=LLM_TIMEOUT_S,
        )

        summary = _parse_summary_response(response.content or "")
        if not summary:
            # Fallback: use first 500 chars
            summary = full_text[:500].strip()
            if len(full_text) > 500:
                summary += "..."

        return {"summary": summary}

    except asyncio.TimeoutError:
        logger.warning("[ai_paper_summary] LLM call timed out after {}s", LLM_TIMEOUT_S)
        fallback = full_text[:500].strip()
        if len(full_text) > 500:
            fallback += "..."
        return {"summary": fallback, "error": "AI 处理超时，已返回摘要预览"}
    except Exception as e:
        logger.error("[ai_paper_summary] LLM call failed: {}", e)
        fallback = full_text[:500].strip()
        if len(full_text) > 500:
            fallback += "..."
        return {"summary": fallback, "error": f"AI 处理失败: {e}"}
