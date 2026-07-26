"""Dynamic clarification form generation for researcher deep mode."""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any

from loguru import logger

from .llm_utils import make_llm_provider

LLM_TIMEOUT_S = 60


def _build_prompt(question: str) -> str:
    return f"""你正在处理研究者深度模式请求。当前阶段不是回答问题，而是根据用户原始问题进行意图识别和问题澄清。

用户原始问题：{question}

请先分析这个问题可能涉及的关键维度，再生成一个用于前端渲染的动态澄清表单。

严格只输出一个 JSON 对象，不要使用 Markdown，不要加解释文字。
JSON 结构如下：
{{
  "analysis": "用中文概括你识别到的研究对象、领域/方向、潜在比较对象、关键维度、产出类型和不确定点。不要直接回答原问题。",
  "questions": [
    {{
      "id": "short_snake_case_id",
      "type": "single | multi | text | textarea",
      "label": "面向用户的澄清问题",
      "help": "可选，解释为什么需要这个信息",
      "placeholder": "可选，text/textarea 的占位提示",
      "options": [{{"label": "选项文本", "value": "选项值"}}],
      "defaultValue": "默认值；multi 类型使用字符串数组"
    }}
  ]
}}

问题生成要求：
1. questions 必须包含 4-7 个问题。
2. 至少包含 1 个 single、1 个 multi、1 个 text 或 textarea。
3. 所有选项都必须根据用户原始问题动态生成，不要使用通用固定选项。
4. 问题需要覆盖：研究对象/领域确认、范围边界、重点维度、比较对象或资料约束、期望产出。
5. 如果原问题涉及具体工具、论文、模型、方法或数据集，选项中要体现这些实体及合理候选项。"""


def _extract_json_object(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, flags=re.I)
    raw = match.group(1) if match else text
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        parsed = json.loads(raw[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _normalize_option(option: Any, index: int) -> dict[str, str]:
    if isinstance(option, str):
        return {"label": option, "value": option}
    if isinstance(option, dict):
        label = str(option.get("label") or option.get("value") or f"选项 {index + 1}")
        return {"label": label, "value": str(option.get("value") or label)}
    label = f"选项 {index + 1}"
    return {"label": label, "value": label}


def _fallback_schema(question: str) -> dict[str, Any]:
    topic = question.strip()[:40] or "该主题"
    return {
        "analysis": f"我识别到你想围绕“{topic}”做深度研究，但研究对象、应用场景、比较对象、重点维度和最终产出形式还需要进一步确认。",
        "questions": [
            {
                "id": "research_object",
                "type": "single",
                "label": "你希望把研究对象限定在哪个层级？",
                "help": "这会决定后续检索和论证的粒度。",
                "options": [
                    {"label": f"{topic} 的技术体系", "value": "technology_system"},
                    {"label": f"{topic} 的应用场景", "value": "application_scenarios"},
                    {"label": f"{topic} 的代表模型/方法", "value": "models_methods"},
                ],
                "defaultValue": "technology_system",
            },
            {
                "id": "focus_dimensions",
                "type": "multi",
                "label": "本次研究最需要覆盖哪些维度？",
                "options": [
                    {"label": "技术路线与关键方法", "value": "technical_routes"},
                    {"label": "代表模型/系统对比", "value": "model_system_comparison"},
                    {"label": "数据集与评测指标", "value": "datasets_metrics"},
                    {"label": "应用落地与局限", "value": "applications_limits"},
                ],
                "defaultValue": ["technical_routes", "model_system_comparison"],
            },
            {
                "id": "comparison_targets",
                "type": "text",
                "label": "是否有必须比较或纳入的对象？",
                "placeholder": "例如具体论文、模型、工具、数据集或公司产品",
                "defaultValue": "",
            },
            {
                "id": "output_format",
                "type": "single",
                "label": "你期望最终产出是什么形式？",
                "options": [
                    {"label": "结构化研究报告", "value": "structured_report"},
                    {"label": "技术路线图", "value": "technology_roadmap"},
                    {"label": "对比矩阵", "value": "comparison_matrix"},
                ],
                "defaultValue": "structured_report",
            },
            {
                "id": "scope_notes",
                "type": "textarea",
                "label": "还有哪些范围边界或资料约束？",
                "placeholder": "例如时间范围、行业场景、排除项、是否需要引用近三年论文等",
                "defaultValue": "",
            },
        ],
    }


def normalize_schema(schema: dict[str, Any] | None, question: str) -> dict[str, Any]:
    fallback = _fallback_schema(question)
    if not isinstance(schema, dict) or not isinstance(schema.get("questions"), list):
        return fallback

    normalized_questions: list[dict[str, Any]] = []
    allowed = {"single", "multi", "text", "textarea"}
    for index, item in enumerate(schema["questions"][:7]):
        if not isinstance(item, dict):
            continue
        q_type = item.get("type") if item.get("type") in allowed else "text"
        options = [_normalize_option(opt, idx) for idx, opt in enumerate(item.get("options") or [])]
        if q_type in {"single", "multi"} and not options:
            q_type = "text"
        qid = re.sub(r"[^\w-]", "_", str(item.get("id") or f"question_{index + 1}"))
        normalized_questions.append(
            {
                "id": qid,
                "type": q_type,
                "label": str(item.get("label") or f"澄清问题 {index + 1}"),
                "help": str(item.get("help") or ""),
                "placeholder": str(item.get("placeholder") or ""),
                "options": options,
                "defaultValue": item.get("defaultValue", [] if q_type == "multi" else ""),
            }
        )

    if not normalized_questions:
        return fallback
    return {
        "analysis": str(schema.get("analysis") or fallback["analysis"]),
        "questions": normalized_questions,
    }


async def generate_researcher_clarification(question: str) -> dict[str, Any]:
    if not question or not question.strip():
        return {"error": "empty question", **_fallback_schema(question)}

    try:
        provider, model = make_llm_provider()
        response = await asyncio.wait_for(
            provider.chat_stream(
                messages=[{"role": "user", "content": _build_prompt(question.strip())}],
                model=model,
                temperature=0.2,
            ),
            timeout=LLM_TIMEOUT_S,
        )
        schema = normalize_schema(_extract_json_object(response.content or ""), question)
        return schema
    except asyncio.TimeoutError:
        logger.warning("[researcher_clarification] LLM timed out after {}s", LLM_TIMEOUT_S)
        return {"error": "clarification generation timed out", **_fallback_schema(question)}
    except Exception as exc:
        logger.error("[researcher_clarification] LLM failed: {}", exc)
        return {"error": str(exc), **_fallback_schema(question)}
