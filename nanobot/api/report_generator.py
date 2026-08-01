"""AI-first structured report generation with a deterministic fallback."""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any

from loguru import logger

from .llm_utils import make_llm_provider

REPORT_SCHEMA_VERSION = 1
LLM_TIMEOUT_S = 120
SECTION_DEFINITIONS = (
    ("background", "研究背景"),
    ("findings", "核心发现"),
    ("discussion", "讨论"),
    ("conclusion", "结论"),
)


class ReportGenerationError(ValueError):
    """Raised when neither AI nor the deterministic generator can make a report."""


def source_reference(source: dict[str, Any]) -> dict[str, Any]:
    """Return the stable public reference for a loaded source."""
    return {
        "type": str(source.get("_sourceType", "")),
        "id": source.get("_sourceId"),
        "title": source_title(source),
    }


def source_title(source: dict[str, Any]) -> str:
    return str(
        source.get("fileName")
        or source.get("title")
        or source.get("name")
        or f"来源 {source.get('_sourceId', '')}"
    )


async def generate_report(
    title: str,
    sources: list[dict[str, Any]],
    config: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Generate a report and return ``(content, generator_metadata)``.

    The model is asked for JSON, but the persisted structure is always
    normalized and validated by this module before it reaches the database.
    """
    config = config if isinstance(config, dict) else {}
    try:
        ai_content = await _generate_with_ai(title, sources, config)
        content = normalize_report(ai_content, title, sources, config)
        return content, {
            "generator": "ai",
            "schemaVersion": REPORT_SCHEMA_VERSION,
            "sourceCount": len(sources),
        }
    except Exception as exc:
        logger.warning("Report AI generation failed; using local fallback: {}", exc)
        content = generate_local_report(title, sources, config)
        return content, {
            "generator": "local",
            "schemaVersion": REPORT_SCHEMA_VERSION,
            "sourceCount": len(sources),
            "fallbackReason": str(exc)[:500],
        }


async def _generate_with_ai(
    title: str,
    sources: list[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    provider, model = make_llm_provider()
    prompt = _build_prompt(title, sources, config)
    response = await asyncio.wait_for(
        provider.chat_stream(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=0.2,
        ),
        timeout=LLM_TIMEOUT_S,
    )
    raw_content = response.content or ""
    if config.get("artifactType") == "data_table":
        return {"_rawContent": raw_content}
    try:
        return _parse_json_response(raw_content)
    except ReportGenerationError:
        if config.get("artifactType") == "data_table":
            return {"_rawContent": raw_content}
        raise


def _build_prompt(title: str, sources: list[dict[str, Any]], config: dict[str, Any]) -> str:
    source_blocks = []
    for index, source in enumerate(sources, 1):
        source_blocks.append(json.dumps({
            "sourceRef": source_reference(source),
            "text": str(source.get("_text", ""))[:12000],
        }, ensure_ascii=False))
    focus = str(config.get("note") or config.get("focus") or "").strip()
    length = str(config.get("length") or "standard").strip()
    artifact_type = str(config.get("artifactType") or "report")
    if artifact_type == "data_table":
        max_rows = max(5, min(int(config.get("maxRows", 20)), 50))
        return f"""You are a rigorous academic data extraction editor. Return ONLY one Markdown table. Do not return JSON, a code fence, headings, bullets, explanations, or any text before or after the table.
Title: {title}
Research focus: {focus or config.get('topic') or 'Extract comparable, traceable information from the selected sources.'}
Maximum rows: {max_rows}

Choose 4 to 10 meaningful columns yourself from the research topic and sources. Do not use a fixed generic schema. A clinical table may use intervention, comparator, sample size, outcome, effect size, follow-up, and adverse events. An experiment table may use variable, setting, method, measurement, result, and limitation. A literature comparison may use study, dataset, method, metric, result, and conclusion. Use domain-specific fields when supported by the sources.
Use this exact Markdown shape: one header row, one separator row made only of hyphens, then data rows. Keep every row the same number of cells. Preserve numbers, units, prices, dates, comparisons, study names, and statistical results exactly. Use \"Not stated\" for a missing source-grounded value. Create one row per study, experiment, claim, or comparable observation. Do not invent facts. Escape or replace any pipe character inside a cell so it does not break the table.

Example shape only:
| Field chosen for this topic | Measured value | Result |
|---|---:|---|
| Source-grounded value | 12.5 | Source-grounded result |

Selected sources:
{chr(10).join(source_blocks)}"""
    if artifact_type != "report":
        schemas = {
            "mind_map": '{"root":{"id":"root","label":"主题","summary":"摘要","children":[{"id":"node-1","label":"节点","summary":"摘要","children":[]}]}}',
            "flashcards": '{"cards":[{"question":"问题","answer":"答案","explanation":"解释","difficulty":"medium","tags":[]}]}' ,
            "quiz": '{"questions":[{"question":"题目","options":[{"id":"a","text":"选项"},{"id":"b","text":"选项"},{"id":"c","text":"选项"}],"answer":["a"],"explanation":"解析"}]}',
            "data_table": '{"columns":[{"key":"finding","label":"核心发现","type":"text"}],"rows":[{"finding":"来源中的明确内容"}]}',
        }
        return f"""你是一名严谨的学术资料编辑。请只输出一个 JSON 对象，不要 Markdown 代码围栏或额外解释。
制品类型：{artifact_type}
制品标题：{title}
研究重点：{focus or '根据来源提炼可追溯内容'}
JSON 结构必须接近：{schemas.get(artifact_type, '{}')}
只使用提供的来源，不得补造事实；不要输出 sourceRefs，系统会根据来源自动补齐。
输入来源：
{chr(10).join(source_blocks)}"""
    return f"""你是一名严谨的学术研究报告编辑。请只输出一个 JSON 对象，不要 Markdown 代码围栏或额外解释。

报告标题：{title}
报告重点：{focus or '根据来源提炼主要研究问题、证据和结论'}
报告长度：{length}

JSON 必须符合以下结构：
{{
  "summary": "150-300字的摘要",
  "sections": [
    {{"id": "background", "title": "研究背景", "paragraphs": [{{"text": "...", "sourceRefs": [{{"type": "paper", "id": 1}}]}}]}},
    {{"id": "findings", "title": "核心发现", "paragraphs": [{{"text": "...", "sourceRefs": [{{"type": "paper", "id": 1}}]}}]}},
    {{"id": "discussion", "title": "讨论", "paragraphs": [{{"text": "...", "sourceRefs": [{{"type": "paper", "id": 1}}]}}]}},
    {{"id": "conclusion", "title": "结论", "paragraphs": [{{"text": "...", "sourceRefs": [{{"type": "paper", "id": 1}}]}}]}}
  ]
}}

只使用提供的来源，不得补造事实。每个段落尽量携带来源引用；引用中的 type 和 id 必须来自输入来源。

输入来源：
{chr(10).join(source_blocks)}"""


def _parse_json_response(value: str) -> dict[str, Any]:
    text = value.strip()
    candidates = [text]
    fenced = re.findall(r"```(?:json)?\s*([\s\S]*?)```", text, flags=re.IGNORECASE)
    candidates[0:0] = fenced
    parsed = None
    for candidate in candidates:
        try:
            value = json.loads(candidate.strip())
            if isinstance(value, dict):
                parsed = value
                break
        except (json.JSONDecodeError, TypeError):
            for fragment in _balanced_json_objects(candidate):
                try:
                    value = json.loads(fragment)
                    if isinstance(value, dict):
                        parsed = value
                        break
                except json.JSONDecodeError:
                    continue
            if parsed is not None:
                break
    if parsed is None:
        raise ReportGenerationError("AI response is not valid JSON")
    if not isinstance(parsed, dict):
        raise ReportGenerationError("AI response must be a JSON object")
    return parsed


def _balanced_json_objects(text: str):
    for start, character in enumerate(text):
        if character != "{":
            continue
        depth = 0
        in_string = False
        escaped = False
        for index in range(start, len(text)):
            current = text[index]
            if in_string:
                if escaped:
                    escaped = False
                elif current == "\\":
                    escaped = True
                elif current == '"':
                    in_string = False
                continue
            if current == '"':
                in_string = True
            elif current == "{":
                depth += 1
            elif current == "}":
                depth -= 1
                if depth == 0:
                    yield text[start:index + 1]
                    break


def normalize_report(
    raw: dict[str, Any],
    title: str,
    sources: list[dict[str, Any]],
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate and normalize model output to the persisted report schema."""
    config = config if isinstance(config, dict) else {}
    allowed_refs = {
        (str(source.get("_sourceType")), str(source.get("_sourceId"))): source_reference(source)
        for source in sources
    }
    summary = _text(raw.get("summary"))
    if len(summary) < 20:
        raise ReportGenerationError("AI report summary is too short")

    raw_sections = raw.get("sections")
    if not isinstance(raw_sections, list):
        raise ReportGenerationError("AI report sections are missing")
    by_id = {str(item.get("id")): item for item in raw_sections if isinstance(item, dict)}
    sections = []
    for section_id, default_title in SECTION_DEFINITIONS:
        item = by_id.get(section_id)
        if not item:
            raise ReportGenerationError(f"AI report section missing: {section_id}")
        paragraphs = _normalize_paragraphs(item.get("paragraphs"), allowed_refs)
        if not paragraphs:
            raise ReportGenerationError(f"AI report section is empty: {section_id}")
        sections.append({
            "id": section_id,
            "title": _text(item.get("title")) or default_title,
            "paragraphs": paragraphs,
            "sourceRefs": _merge_refs(paragraph["sourceRefs"] for paragraph in paragraphs),
        })

    references = list(allowed_refs.values())
    content = {
        "kind": "report",
        "schemaVersion": REPORT_SCHEMA_VERSION,
        "title": title,
        "summary": summary,
        "sections": sections,
        "references": references,
    }
    if config.get("includeCitations", True) is not False:
        content["markdown"] = report_markdown(content)
    return content


def generate_local_report(
    title: str,
    sources: list[dict[str, Any]],
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate a deterministic report when no model is available."""
    del config
    refs = [source_reference(source) for source in sources]
    sentences = _sentences("\n".join(str(source.get("_text", "")) for source in sources))
    summary = " ".join(sentences[:3]).strip() or "当前来源没有可提取的正文内容。"
    section_text = {
        "background": sentences[:2],
        "findings": sentences[2:6] or sentences[:2],
        "discussion": sentences[6:9] or sentences[2:4] or [summary],
        "conclusion": sentences[-3:] or [summary],
    }
    sections = []
    for section_id, section_title in SECTION_DEFINITIONS:
        paragraphs = [
            {
                "id": f"{section_id}-{index}",
                "text": text,
                "sourceRefs": refs,
            }
            for index, text in enumerate(section_text[section_id], 1)
            if text
        ]
        if not paragraphs:
            paragraphs = [{"id": f"{section_id}-1", "text": summary, "sourceRefs": refs}]
        sections.append({
            "id": section_id,
            "title": section_title,
            "paragraphs": paragraphs,
            "sourceRefs": refs,
        })
    content = {
        "kind": "report",
        "schemaVersion": REPORT_SCHEMA_VERSION,
        "title": title,
        "summary": summary,
        "sections": sections,
        "references": refs,
    }
    content["markdown"] = report_markdown(content)
    return content


def validate_report_content(content: Any, allowed_refs: list[dict[str, Any]]) -> dict[str, Any]:
    """Validate user-edited content without allowing new source references."""
    if not isinstance(content, dict):
        raise ReportGenerationError("report content must be an object")
    sources = [
        {"_sourceType": item.get("type"), "_sourceId": item.get("id"), "title": item.get("title")}
        for item in allowed_refs
        if isinstance(item, dict)
    ]
    normalized = normalize_report(content, _text(content.get("title")) or "研究报告", sources, {})
    normalized["title"] = _text(content.get("title")) or normalized["title"]
    return normalized


def report_markdown(content: dict[str, Any]) -> str:
    lines = [f"# {_text(content.get('title'))}", "", "## 摘要", "", _text(content.get("summary")), ""]
    for section in content.get("sections", []):
        lines.extend([f"## {_text(section.get('title'))}", ""])
        for paragraph in section.get("paragraphs", []):
            lines.extend([_text(paragraph.get("text")), ""])
    references = content.get("references", [])
    if references:
        lines.extend(["## 参考来源", ""])
        lines.extend(f"- {_text(item.get('title'))} ({item.get('type')}:{item.get('id')})" for item in references)
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _normalize_paragraphs(
    value: Any,
    allowed_refs: dict[tuple[str, str], dict[str, Any]],
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    fallback_refs = list(allowed_refs.values())
    paragraphs = []
    for index, item in enumerate(value, 1):
        if isinstance(item, str):
            text = item.strip()
            raw_refs = []
        elif isinstance(item, dict):
            text = _text(item.get("text") or item.get("content"))
            raw_refs = item.get("sourceRefs", [])
        else:
            continue
        if not text:
            continue
        refs = _filter_refs(raw_refs, allowed_refs) or fallback_refs
        paragraphs.append({"id": f"paragraph-{index}", "text": text[:12000], "sourceRefs": refs})
    return paragraphs


def _filter_refs(value: Any, allowed_refs: dict[tuple[str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    refs = []
    for item in value:
        if not isinstance(item, dict):
            continue
        key = (str(item.get("type", "")), str(item.get("id", "")))
        if key in allowed_refs and key not in {(ref["type"], str(ref["id"])) for ref in refs}:
            refs.append(allowed_refs[key])
    return refs


def _merge_refs(groups: Any) -> list[dict[str, Any]]:
    refs = []
    seen = set()
    for group in groups:
        for ref in group:
            key = (ref.get("type"), str(ref.get("id")))
            if key not in seen:
                seen.add(key)
                refs.append(ref)
    return refs


def _text(value: Any) -> str:
    return str(value or "").strip()


def _sentences(text: str) -> list[str]:
    clean = re.sub(r"\s+", " ", text or "").strip()
    if not clean:
        return []
    return [part.strip() for part in re.split(r"(?<=[。！？.!?])\s*", clean) if part.strip()]
