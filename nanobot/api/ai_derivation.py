"""AI derivation chain generation logic.

Provides AI-powered generation of step-by-step derivation chains for
educational topics. Supports three modes: formula (mathematical derivation),
code (Python implementation), and concept (comparative analysis).
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from loguru import logger

from .llm_utils import make_llm_provider

LLM_TIMEOUT_S = 120


def _build_derivation_prompt(topic: str, mode: str) -> str:
    """Build the LLM prompt for generating a derivation chain."""
    mode_instructions = {
        "formula": (
            "请为该主题生成一个数学/物理公式推导链，每个步骤包含：\n"
            "- 一个核心公式（使用 LaTeX 格式，用 $$...$$ 包裹）\n"
            "- 公式前后的文字解释\n"
            "- 洞察/注释\n"
            "步骤应从基础定义出发，逐步推导到最终结论。"
        ),
        "code": (
            "请为该主题生成一个 Python 代码实现链，每个步骤包含：\n"
            "- 一段可运行的 Python 代码片段\n"
            "- 代码的关键行高亮说明\n"
            "- 代码注释/批注\n"
            "步骤应从数据准备开始，逐步实现核心算法。"
        ),
        "concept": (
            "请为该主题生成一个概念辨析链，每个步骤包含：\n"
            "- 2-3 个相关概念的对比卡片（含优缺点）\n"
            "- 概念间的逻辑关系\n"
            "步骤应从基础概念出发，逐步深入到高级应用。"
        ),
    }

    mode_desc = mode_instructions.get(mode, mode_instructions["formula"])

    parts = [
        "你是一位专业的学科教师，擅长将复杂知识拆解为循序渐进的推导步骤。",
        f"请为以下主题生成一个完整的推导链：「{topic}」\n",
        f"## 推导模式：{mode}\n{mode_desc}\n",
        """## 输出要求
请严格按照以下 JSON 格式返回，不要包含任何其他文字或 markdown 代码块标记：
{
  "steps": [
    {
      "name": "步骤名称（含 emoji，如：🌿 光合作用方程）",
      "shortDesc": "一句话简述",
      "trace": "知识溯源（如：Monteith 1977 — 辐射利用效率模型）",
      "extra": "补充说明或典型值",
      "sections": [
        {"kind": "text", "value": "解释性文字"},
        {"kind": "formula", "value": "$$...LaTeX公式...$$", "tag": "(1)"},
        {"kind": "insight", "value": "洞察/注释文字"},
        {"kind": "code", "code": "python代码", "highlight": [1,2], "annotation": "批注"},
        {"kind": "concept-grid", "cards": [{"badge": "标签", "title": "标题", "desc": "描述", "pro": "✓ 优点", "con": "✗ 缺点"}]}
      ]
    }
  ]
}

注意：
- 生成 4-5 个步骤，保持简洁
- 步骤之间要有逻辑递进关系
- 每个步骤的 sections 中至少包含 formula 或 code 或 concept-grid 中的一种
- formula 模式下主要使用 formula 和 text/insight
- code 模式下主要使用 code 和 text/insight
- concept 模式下主要使用 concept-grid 和 text/insight
- 公式使用 LaTeX 格式，用 $$...$$ 包裹行间公式
- 代码使用 Python，高亮关键行
- 每个步骤的 text 和 insight 内容要简短（50字以内）
"""
    ]

    return "\n".join(parts)


def _build_chat_system_prompt(topic: str, steps_summary: str) -> str:
    """Build system prompt for derivation Q&A chat."""
    return (
        f"你是一位专业的学科辅导老师，正在帮助学生理解「{topic}」的推导链。\n\n"
        f"当前推导链包含以下步骤：\n{steps_summary}\n\n"
        "请根据学生的问题，结合推导链内容进行解答。"
        "如果学生问到推导链中的公式、代码或概念，请详细解释其含义、来源和应用。"
        "回答要简洁准确，适合学生理解。"
    )


def _parse_ai_response(content: str) -> dict:
    """Parse the LLM response, stripping markdown code blocks if present.

    Handles truncated JSON by attempting to repair unterminated strings
    and close open brackets/braces.
    """
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[-1]
    if content.endswith("```"):
        content = content.rsplit("```", 1)[0]
    content = content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        # Attempt to repair truncated JSON
        # Close unterminated string if needed
        if content.count('"') % 2 != 0:
            content += '"'
        # Close open arrays and objects
        open_brackets = content.count('[') - content.count(']')
        open_braces = content.count('{') - content.count('}')
        # Remove trailing incomplete key-value pairs
        last_comma = content.rfind(',')
        last_brace = content.rfind('}')
        if last_comma > last_brace:
            content = content[:last_comma]
        content += ']' * max(0, open_brackets) + '}' * max(0, open_braces)
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning("Failed to parse even repaired JSON response")
            return {"steps": []}


def _validate_steps(data: dict) -> dict:
    """Validate and normalize the generated derivation steps."""
    steps = data.get("steps", [])
    if not isinstance(steps, list):
        return {"steps": []}

    valid_sections = {"text", "formula", "insight", "code", "concept-grid"}
    validated = []

    for i, step in enumerate(steps):
        if not isinstance(step, dict):
            continue

        name = str(step.get("name", f"步骤 {i + 1}"))
        short_desc = str(step.get("shortDesc", ""))
        trace = str(step.get("trace", ""))
        extra = str(step.get("extra", ""))

        sections = []
        for sec in step.get("sections", []):
            if not isinstance(sec, dict):
                continue
            kind = str(sec.get("kind", ""))
            if kind not in valid_sections:
                continue

            if kind == "text":
                sections.append({"kind": "text", "value": str(sec.get("value", ""))})
            elif kind == "formula":
                sections.append({
                    "kind": "formula",
                    "value": str(sec.get("value", "")),
                    "tag": str(sec.get("tag", "")),
                })
            elif kind == "insight":
                sections.append({"kind": "insight", "value": str(sec.get("value", ""))})
            elif kind == "code":
                highlights = sec.get("highlight", [])
                if isinstance(highlights, list):
                    highlights = [int(h) for h in highlights if isinstance(h, (int, float))]
                else:
                    highlights = []
                sections.append({
                    "kind": "code",
                    "code": str(sec.get("code", "")),
                    "highlight": highlights,
                    "annotation": str(sec.get("annotation", "")),
                })
            elif kind == "concept-grid":
                cards = []
                for card in sec.get("cards", []):
                    if isinstance(card, dict):
                        cards.append({
                            "badge": str(card.get("badge", "")),
                            "title": str(card.get("title", "")),
                            "desc": str(card.get("desc", "")),
                            "pro": str(card.get("pro", "")),
                            "con": str(card.get("con", "")),
                        })
                sections.append({"kind": "concept-grid", "cards": cards})

        if sections:
            validated.append({
                "id": i,
                "name": name,
                "shortDesc": short_desc,
                "trace": trace,
                "extra": extra,
                "sections": sections,
            })

    return {"steps": validated}


async def generate_derivation_chain(topic: str, mode: str = "formula") -> dict:
    """Generate a derivation chain for a given topic using AI.

    Args:
        topic: The topic to generate a derivation chain for
        mode: One of "formula", "code", "concept"

    Returns:
        dict with key "steps" containing a list of step objects
    """
    if mode not in ("formula", "code", "concept"):
        mode = "formula"

    prompt = _build_derivation_prompt(topic, mode)

    try:
        provider, model = make_llm_provider()
        messages = [{"role": "user", "content": prompt}]
        response = await asyncio.wait_for(
            provider.chat_stream(
                messages=messages,
                model=model,
                max_tokens=8192,
                temperature=0.5,
            ),
            timeout=LLM_TIMEOUT_S,
        )
        result = _parse_ai_response(response.content or "{}")
        return _validate_steps(result)

    except Exception as e:
        logger.error("AI derivation generation failed: {} - {}", type(e).__name__, e)
        # Fallback: return a basic single-step derivation
        return {
            "steps": [
                {
                    "id": 0,
                    "name": f"📖 {topic}",
                    "shortDesc": "基础概念",
                    "trace": "AI 生成失败，已使用基础模板。",
                    "extra": "请稍后重试。",
                    "sections": [
                        {
                            "kind": "text",
                            "value": f"关于「{topic}」的推导链生成失败。请检查网络连接后重试。",
                        },
                        {
                            "kind": "insight",
                            "value": "如果问题持续存在，请联系管理员检查 AI 服务配置。",
                        },
                    ],
                }
            ]
        }
