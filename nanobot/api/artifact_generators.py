"""Structured generators for researcher artifacts."""

from __future__ import annotations

import json
import re
from typing import Any, Callable

from loguru import logger

from .report_generator import (
    ReportGenerationError,
    _generate_with_ai,
    _sentences,
    _text,
    source_reference,
    source_title,
)

ARTIFACT_SCHEMA_VERSION = 1
SUPPORTED_GENERATORS = {"report", "mind_map", "flashcards", "quiz", "data_table"}


async def generate_artifact(
    artifact_type: str,
    title: str,
    sources: list[dict[str, Any]],
    config: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    config = config if isinstance(config, dict) else {}
    if artifact_type == "report":
        from .report_generator import generate_report
        return await generate_report(title, sources, config)
    generator = _GENERATORS.get(artifact_type)
    if generator is None:
        raise ReportGenerationError(f"unsupported artifact type: {artifact_type}")
    try:
        raw = await _generate_with_ai(title, sources, {**config, "artifactType": artifact_type})
        generator_config = {**config, "_requireRichTable": artifact_type == "data_table"}
        content = generator(raw, title, sources, generator_config)
        return content, {"generator": "ai", "schemaVersion": ARTIFACT_SCHEMA_VERSION, "sourceCount": len(sources)}
    except Exception as exc:
        logger.warning("{} AI generation failed; using local fallback: {}", artifact_type, exc)
        fallback_config = {**config}
        if artifact_type == "data_table" and isinstance(raw, dict) and raw.get("_rawContent"):
            fallback_config["_rawContent"] = raw["_rawContent"]
        content = _LOCAL_GENERATORS[artifact_type](title, sources, fallback_config)
        return content, {
            "generator": "local",
            "schemaVersion": ARTIFACT_SCHEMA_VERSION,
            "sourceCount": len(sources),
            "fallbackReason": str(exc)[:500],
        }


def validate_artifact_content(artifact_type: str, content: Any, allowed_refs: list[dict[str, Any]]) -> dict[str, Any]:
    sources = [{"_sourceType": item.get("type"), "_sourceId": item.get("id"), "title": item.get("title")} for item in allowed_refs if isinstance(item, dict)]
    if artifact_type == "report":
        from .report_generator import validate_report_content
        return validate_report_content(content, allowed_refs)
    generator = _GENERATORS.get(artifact_type)
    if generator is None or not isinstance(content, dict):
        raise ReportGenerationError("invalid artifact content")
    return generator(content, _text(content.get("title")) or "研究制品", sources, {})


def artifact_markdown(content: dict[str, Any], title: str = "") -> str:
    kind = content.get("kind")
    heading = content.get("title") or title
    lines = [f"# {heading}", ""]
    if kind == "mind_map":
        def walk(node: dict[str, Any], depth: int = 0) -> None:
            lines.append(f"{'  ' * depth}- {node.get('label', '')}")
            if node.get("summary"):
                lines.append(f"{'  ' * (depth + 1)}{node['summary']}")
            for child in node.get("children", []): walk(child, depth + 1)
        walk(content.get("root", {}))
    elif kind == "flashcards":
        for index, card in enumerate(content.get("cards", []), 1):
            lines += [f"## {index}. {card.get('question', '')}", "", card.get("answer", ""), "", card.get("explanation", ""), ""]
    elif kind == "quiz":
        for index, question in enumerate(content.get("questions", []), 1):
            lines += [f"## {index}. {question.get('question', '')}", ""]
            lines += [f"- {option.get('id')}: {option.get('text', '')}" for option in question.get("options", [])]
            lines += [f"答案：{', '.join(question.get('answer', []))}", question.get("explanation", ""), ""]
    elif kind == "data_table":
        columns = content.get("columns", [])
        lines += ["| " + " | ".join(c.get("label", c.get("key", "")) for c in columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
        for row in content.get("rows", []): lines.append("| " + " | ".join(str(row.get(c.get("key"), "")) for c in columns) + " |")
    return "\n".join(lines).strip() + "\n"


def artifact_csv(content: dict[str, Any]) -> str:
    import csv
    import io
    columns = content.get("columns", [])
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([c.get("label", c.get("key", "")) for c in columns])
    for row in content.get("rows", []): writer.writerow([row.get(c.get("key"), "") for c in columns])
    return output.getvalue()


def _refs(sources): return [source_reference(source) for source in sources]
def _source_sentences(sources): return _sentences("\n".join(str(s.get("_text", "")) for s in sources)) or ["当前来源没有可提取的正文内容。"]
def _ref_for(sources, index=0): return [_refs(sources)[index % len(sources)]]


def _mind_map(raw, title, sources, config):
    refs = _refs(sources)
    root = raw.get("root") if isinstance(raw, dict) else None
    if not isinstance(root, dict): raise ReportGenerationError("mind map root is missing")
    return {"kind": "mind_map", "schemaVersion": 1, "title": title, "root": _normalize_node(root, refs, 0, int(config.get("maxDepth", 4))), "references": refs, "markdown": artifact_markdown({"kind": "mind_map", "title": title, "root": root})}


def _normalize_node(node, refs, depth, max_depth):
    label = _text(node.get("label"))
    if not label: raise ReportGenerationError("mind map node label is missing")
    children = [_normalize_node(child, refs, depth + 1, max_depth) for child in node.get("children", []) if isinstance(child, dict)] if depth < max_depth else []
    return {"id": _text(node.get("id")) or f"node-{depth}", "label": label[:240], "summary": _text(node.get("summary"))[:2000], "sourceRefs": refs, "children": children}


def _local_mind_map(title, sources, config):
    refs, sentences = _refs(sources), _source_sentences(sources)
    limit = max(6, min(int(config.get("maxNodes", 20)), 20))
    groups = (("研究背景", sentences[:2]), ("核心发现", sentences[2:6]), ("讨论与结论", sentences[6:]))
    children = []
    sentence_index = 0
    for group_index, (label, group_sentences) in enumerate(groups, 1):
        if not group_sentences: continue
        grandchildren = []
        for sentence in group_sentences[: max(1, limit // 3)]:
            sentence_index += 1
            grandchildren.append({"id": f"evidence-{sentence_index}", "label": sentence[:90], "summary": sentence, "sourceRefs": _ref_for(sources, sentence_index), "children": []})
        children.append({"id": f"branch-{group_index}", "label": label, "summary": f"{len(grandchildren)} 条可追溯内容", "sourceRefs": refs, "children": grandchildren})
    root = {"id": "root", "label": title, "summary": f"从 {len(sources)} 项资料整理出 {sentence_index} 条内容", "sourceRefs": refs, "children": children}
    return {"kind": "mind_map", "schemaVersion": 1, "title": title, "root": root, "references": refs, "markdown": artifact_markdown({"kind": "mind_map", "title": title, "root": root})}


def _flashcards(raw, title, sources, config):
    cards = raw.get("cards") if isinstance(raw, dict) else None
    if not isinstance(cards, list) or not cards: raise ReportGenerationError("flashcards are missing")
    refs = _refs(sources)
    normalized = [{"id": f"card-{i}", "question": _text(c.get("question"))[:500], "answer": _text(c.get("answer"))[:2000], "explanation": _text(c.get("explanation"))[:2000], "difficulty": _text(c.get("difficulty")) if _text(c.get("difficulty")) in {"easy", "medium", "hard"} else "medium", "tags": [str(t)[:40] for t in c.get("tags", [])[:8]] if isinstance(c.get("tags"), list) else [], "sourceRefs": refs} for i, c in enumerate(cards[:20], 1) if isinstance(c, dict) and _text(c.get("question")) and _text(c.get("answer"))]
    if not normalized: raise ReportGenerationError("flashcards are invalid")
    return {"kind": "flashcards", "schemaVersion": 1, "title": title, "cards": normalized, "references": refs}


def _local_flashcards(title, sources, config):
    refs, sentences = _refs(sources), _source_sentences(sources)
    count = max(8, min(int(config.get("count", 12)), 20))
    return {"kind": "flashcards", "schemaVersion": 1, "title": title, "cards": [{"id": f"card-{i}", "question": f"这项研究的关键论据是什么？（{i}）", "answer": sentence, "explanation": "答案直接来自所选研究资料。", "difficulty": "medium", "tags": ["研究"], "sourceRefs": _ref_for(sources, i)} for i, sentence in enumerate((sentences * count)[:count], 1)], "references": refs}


def _quiz(raw, title, sources, config):
    questions = raw.get("questions") if isinstance(raw, dict) else None
    if not isinstance(questions, list) or not questions: raise ReportGenerationError("quiz questions are missing")
    refs = _refs(sources); normalized = []
    for i, q in enumerate(questions[:30], 1):
        options = q.get("options") if isinstance(q, dict) else None
        answer = q.get("answer") if isinstance(q, dict) else None
        if not isinstance(options, list) or not 3 <= len(options) <= 5 or not isinstance(answer, list) or len(answer) != 1: continue
        normalized.append({"id": f"question-{i}", "type": "single", "question": _text(q.get("question"))[:1000], "options": [{"id": _text(o.get("id")), "text": _text(o.get("text"))[:500]} for o in options if isinstance(o, dict)], "answer": [str(answer[0])], "explanation": _text(q.get("explanation"))[:2000], "sourceRefs": refs})
    if not normalized: raise ReportGenerationError("quiz questions are invalid")
    return {"kind": "quiz", "schemaVersion": 1, "title": title, "questions": normalized, "references": refs}


def _local_quiz(title, sources, config):
    refs, sentences = _refs(sources), _source_sentences(sources); count = max(5, min(int(config.get("count", 10)), 30))
    return {"kind": "quiz", "schemaVersion": 1, "title": title, "questions": [{"id": f"question-{i}", "type": "single", "question": f"以下哪项准确概括了研究资料中的内容？", "options": [{"id": "a", "text": sentence}, {"id": "b", "text": "来源未提及的推测"}, {"id": "c", "text": "与来源相反的结论"}], "answer": ["a"], "explanation": "选项 A 来自所选资料。", "sourceRefs": _ref_for(sources, i)} for i, sentence in enumerate((sentences * count)[:count], 1)], "references": refs}


def _data_table(raw, title, sources, config):
    raw_markdown = ""
    if isinstance(raw, dict) and raw.get("_rawContent"):
        raw_markdown = str(raw["_rawContent"])
        extracted = _extract_markdown_table([{"_text": raw["_rawContent"]}])
        if extracted:
            raw = extracted
    columns = raw.get("columns") if isinstance(raw, dict) else None; rows = raw.get("rows") if isinstance(raw, dict) else None
    if not isinstance(columns, list) or not isinstance(rows, list) or not columns or not rows: raise ReportGenerationError("table structure is missing")
    refs = _refs(sources); keys = set(); normalized_columns = []; source_keys = []
    for index, col in enumerate(columns[:12], 1):
        if not isinstance(col, dict): continue
        original_key = _text(col.get("key"))
        label = _text(col.get("label")) or original_key or f"Column {index}"
        key = re.sub(r"[^a-zA-Z0-9_]+", "_", original_key or label).strip("_").lower()
        if not key: key = f"column_{index}"
        base_key = key; suffix = 2
        while key in keys:
            key = f"{base_key}_{suffix}"; suffix += 1
        keys.add(key); source_keys.append((key, original_key, label))
        normalized_columns.append({"key": key, "label": label[:120], "type": _table_column_type(col.get("type"), rows, original_key, label)})
    if not normalized_columns: raise ReportGenerationError("table columns are invalid")
    if config.get("_requireRichTable") and len(normalized_columns) < 4:
        raise ReportGenerationError("data table needs at least four meaningful columns")
    row_limit = max(1, min(int(config.get("maxRows", 20)), 50))
    normalized_rows = []
    for row in rows[:row_limit]:
        if not isinstance(row, dict): continue
        values = {}
        for key, original_key, label in source_keys:
            value = row.get(original_key) if original_key and original_key in row else row.get(label, row.get(key, ""))
            values[key] = _table_value(value)[:4000]
        row_refs = _normalize_table_refs(row.get("sourceRefs"), refs) or refs
        normalized_rows.append({**values, "sourceRefs": row_refs})
    if not normalized_rows: raise ReportGenerationError("table rows are invalid")
    content = {"kind": "data_table", "schemaVersion": 1, "title": title, "columns": normalized_columns, "rows": normalized_rows, "references": refs}
    if raw_markdown:
        content["rawMarkdown"] = raw_markdown[:50000]
    if config.get("_rawContent"):
        content["rawMarkdown"] = str(config["_rawContent"])[:50000]
    content["markdown"] = artifact_markdown(content)
    return content


def _local_data_table(title, sources, config):
    refs, sentences = _refs(sources), _source_sentences(sources); columns = [{"key": "finding", "label": "核心发现", "type": "text"}, {"key": "evidence", "label": "证据", "type": "text"}, {"key": "source", "label": "来源", "type": "text"}]
    rows = [{"finding": sentence[:200], "evidence": sentence, "source": source_title(sources[i % len(sources)]), "sourceRefs": _ref_for(sources, i)} for i, sentence in enumerate(sentences[: max(1, min(int(config.get("maxRows", 20)), 20))])]
    content = {"kind": "data_table", "schemaVersion": 1, "title": title, "columns": columns, "rows": rows, "references": refs}; content["markdown"] = artifact_markdown(content); return content


def _rich_local_data_table(title, sources, config):
    refs = _refs(sources)
    extracted = _extract_markdown_table(sources)
    if extracted:
        return _data_table(extracted, title, sources, config)
    columns = [
        {"key": "source", "label": "\u6765\u6e90", "type": "text"},
        {"key": "topic", "label": "\u4e3b\u9898", "type": "text"},
        {"key": "finding", "label": "\u6838\u5fc3\u53d1\u73b0", "type": "text"},
        {"key": "evidence", "label": "\u8bc1\u636e", "type": "text"},
        {"key": "metrics", "label": "\u6307\u6807\u6216\u6bd4\u8f83", "type": "text"},
        {"key": "method", "label": "\u65b9\u6cd5\u6216\u7814\u7a76\u5bf9\u8c61", "type": "text"},
        {"key": "limitation", "label": "\u5c40\u9650\u6027", "type": "text"},
        {"key": "implication", "label": "\u7814\u7a76\u542f\u793a", "type": "text"},
    ]
    max_rows = max(1, min(int(config.get("maxRows", 20)), 50))
    rows = []
    for item in _source_records(sources)[:max_rows]:
        sentence = item["text"]
        rows.append({
            "source": source_title(item["source"]),
            "topic": title,
            "finding": sentence[:240],
            "evidence": sentence,
            "metrics": _extract_table_metrics(sentence) or "Not stated",
            "method": "Not stated in source",
            "limitation": "Not stated in source",
            "implication": "Requires interpretation against the research question",
            "sourceRefs": _ref_for(sources, item["index"]),
        })
    if not rows:
        rows = [{column["key"]: "Not stated" for column in columns}]
        rows[0].update({"source": "No source text", "topic": title, "sourceRefs": refs})
    content = {"kind": "data_table", "schemaVersion": 1, "title": title, "columns": columns, "rows": rows, "references": refs}
    content["markdown"] = artifact_markdown(content)
    return content


def _extract_markdown_table(sources):
    candidates = []
    for source_index, source in enumerate(sources):
        lines = str(source.get("_text", "")).splitlines()
        for index in range(len(lines) - 1):
            header = lines[index].strip()
            separator = lines[index + 1].strip()
            if not _is_markdown_table_line(header) or not _is_markdown_separator(separator):
                continue
            headers = _markdown_cells(header)
            if len(headers) < 2:
                continue
            rows = []
            cursor = index + 2
            while cursor < len(lines) and _is_markdown_table_line(lines[cursor].strip()):
                values = _markdown_cells(lines[cursor].strip())
                if values:
                    rows.append(values[:len(headers)] + [""] * max(0, len(headers) - len(values)))
                cursor += 1
            if rows:
                candidates.append((len(headers) * len(rows), headers, rows, source_index))
    if not candidates:
        return None
    _, headers, rows, source_index = max(candidates, key=lambda item: item[0])
    columns = [{"key": f"column_{index + 1}", "label": _clean_markdown_cell(label) or f"Column {index + 1}", "type": "text"} for index, label in enumerate(headers)]
    return {
        "columns": columns,
        "rows": [
            {column["key"]: _clean_markdown_cell(values[index]) for index, column in enumerate(columns)}
            for values in rows
        ],
        "sourceIndex": source_index,
    }


def _is_markdown_table_line(value):
    normalized = value.strip().strip("|")
    return normalized.count("|") >= 1 and bool(normalized)


def _is_markdown_separator(value):
    return _is_markdown_table_line(value) and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in _markdown_cells(value))


def _markdown_cells(value):
    return [cell.strip() for cell in value.strip().strip("|").split("|")]


def _clean_markdown_cell(value):
    return re.sub(r"<br\s*/?>", " ", re.sub(r"[*_`]", "", str(value or ""))).strip()


def _source_records(sources):
    records = []
    for index, source in enumerate(sources):
        sentences = _sentences(str(source.get("_text", ""))) or ["No extractable text in source"]
        for sentence in sentences:
            records.append({"source": source, "text": sentence, "index": index})
    return records


def _extract_metrics(value):
    matches = re.findall(r"(?:\d+(?:\.\d+)?\s*(?:%|％|倍|次|人|项|件|天|年)?|p\s*[<=>]\s*0?\.\d+)", value, flags=re.IGNORECASE)
    return "; ".join(matches[:8])


def _table_value(value):
    if value is None: return ""
    if isinstance(value, (dict, list)): return json.dumps(value, ensure_ascii=False)
    return _text(value)


def _table_column_type(value, rows, original_key, label):
    requested = _text(value).lower()
    values = [row.get(original_key, row.get(label, "")) for row in rows[:20] if isinstance(row, dict)]
    numeric_values = [item for item in values if item not in (None, "")]
    if requested in {"number", "numeric", "date", "percentage"}:
        return "percentage" if requested == "percentage" else ("number" if requested == "numeric" else requested)
    if numeric_values and all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in numeric_values):
        return "number"
    text_values = [_text(item).strip() for item in numeric_values]
    if text_values and all(re.fullmatch(r"[-+]?\d+(?:\.\d+)?\s*%", item) for item in text_values):
        return "percentage"
    if text_values and all(re.fullmatch(r"[$€£¥]?\s*[-+]?\d+(?:\.\d+)?", item.replace(",", "")) for item in text_values):
        return "number"
    if text_values and all(re.fullmatch(r"\d{4}[-/]\d{1,2}[-/]\d{1,2}", item) for item in text_values):
        return "date"
    return "text"


def _normalize_table_refs(value, refs):
    if not isinstance(value, list): return []
    requested = {(str(item.get("type")), str(item.get("id"))) for item in value if isinstance(item, dict)}
    return [ref for ref in refs if (str(ref.get("type")), str(ref.get("id"))) in requested]


def _extract_table_metrics(value):
    matches = re.findall(r"(?:\d+(?:\.\d+)?\s*(?:%|x|times|people|items|days|years)?|p\s*[<=>]\s*0?\.\d+)", value, flags=re.IGNORECASE)
    return "; ".join(matches[:8])


_GENERATORS: dict[str, Callable[..., dict[str, Any]]] = {"mind_map": _mind_map, "flashcards": _flashcards, "quiz": _quiz, "data_table": _data_table}
_LOCAL_GENERATORS = {"mind_map": _local_mind_map, "flashcards": _local_flashcards, "quiz": _local_quiz, "data_table": _rich_local_data_table}
