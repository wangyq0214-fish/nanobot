from pathlib import Path

import pytest

from nanobot.api import report_generator
from nanobot.api.report_generator import (
    _parse_json_response,
    generate_report,
    validate_report_content,
)
from nanobot.api.handlers.research_artifacts import _load_sources
from nanobot.api.artifact_generators import generate_artifact, validate_artifact_content, artifact_csv
from nanobot.storage.file_storage import FileStorage


SOURCE = [{
    "_sourceType": "latex",
    "_sourceId": 1,
    "title": "实验文稿",
    "_text": "研究方法建立了可复现的实验流程。结果显示模型在测试集上表现稳定。该方法降低了实验成本。",
}]

TABLE_SOURCE = [{
    "_sourceType": "result",
    "_sourceId": 2,
    "title": "Model comparison",
    "_text": "## Comparison\n| Vendor | Model | Price | Release date |\n|---|---|---:|---|\n| Alpha | A-1 | 12.5% | 2025-03-01 |\n| Beta | B-1 | 20% | 2026-01-02 |",
}]


def _valid_ai_payload():
    return {
        "summary": "这是一段长度足够的研究报告摘要，用于验证结构化报告生成链路。",
        "sections": [
            {
                "id": section_id,
                "title": title,
                "paragraphs": [{"text": f"{title}中的研究证据和分析内容。", "sourceRefs": [{"type": "latex", "id": 1}]}],
            }
            for section_id, title in (
                ("background", "研究背景"),
                ("findings", "核心发现"),
                ("discussion", "讨论"),
                ("conclusion", "结论"),
            )
        ],
    }


def test_ai_json_parser_accepts_fenced_json_with_surrounding_text():
    parsed = _parse_json_response('Result follows:\n```json\n{"columns": [], "rows": []}\n```\nDone.')
    assert parsed == {"columns": [], "rows": []}


class _Response:
    def __init__(self, content):
        self.content = content


class _Provider:
    def __init__(self, content):
        self.content = content

    async def chat_stream(self, **kwargs):
        return _Response(self.content)


class _SequenceProvider:
    def __init__(self, contents):
        self.contents = iter(contents)

    async def chat_stream(self, **kwargs):
        return _Response(next(self.contents))


@pytest.mark.asyncio
async def test_report_generation_accepts_structured_ai_output(monkeypatch):
    monkeypatch.setattr(report_generator, "make_llm_provider", lambda: (_Provider(__import__("json").dumps(_valid_ai_payload(), ensure_ascii=False)), "test-model"))

    content, metadata = await generate_report("测试报告", SOURCE, {"includeCitations": True})

    assert metadata["generator"] == "ai"
    assert content["kind"] == "report"
    assert content["schemaVersion"] == 1
    assert [section["id"] for section in content["sections"]] == ["background", "findings", "discussion", "conclusion"]
    assert content["sections"][0]["paragraphs"][0]["sourceRefs"][0]["id"] == 1
    assert content["markdown"].startswith("# 测试报告")


@pytest.mark.asyncio
async def test_report_generation_falls_back_when_ai_output_is_invalid(monkeypatch):
    monkeypatch.setattr(report_generator, "make_llm_provider", lambda: (_Provider("not-json"), "test-model"))

    content, metadata = await generate_report("兜底报告", SOURCE)

    assert metadata["generator"] == "local"
    assert metadata["fallbackReason"]
    assert len(content["sections"]) == 4
    assert content["references"][0]["type"] == "latex"


def test_edited_report_cannot_add_foreign_source_reference():
    content = {
        **_valid_ai_payload(),
        "title": "编辑后的报告",
        "sections": [
            {
                **section,
                "paragraphs": [{"text": "修改后的段落", "sourceRefs": [{"type": "paper", "id": 999}]}],
            }
            for section in _valid_ai_payload()["sections"]
        ],
    }

    normalized = validate_report_content(content, [{"type": "latex", "id": 1, "title": "实验文稿"}])

    refs = normalized["sections"][0]["paragraphs"][0]["sourceRefs"]
    assert refs == [{"type": "latex", "id": 1, "title": "实验文稿"}]


@pytest.mark.asyncio
async def test_source_loader_rejects_foreign_sources():
    class Storage:
        async def get_research_result(self, source_id):
            return {"id": source_id, "userId": "another-user", "content": "private"}

    with pytest.raises(ValueError, match="none of the selected sources"):
        await _load_sources(Storage(), "researcher-1", [{"type": "result", "id": 1}])


@pytest.mark.asyncio
async def test_file_storage_attachment_cleanup(tmp_path: Path):
    storage = FileStorage(tmp_path)
    attachment_path = tmp_path / "attachment.txt"
    attachment_path.write_text("content", encoding="utf-8")
    attachment = await storage.create_research_attachment({
        "user_id": "researcher-1",
        "file_name": "attachment.txt",
        "file_path": str(attachment_path),
        "parse_status": "ready",
    })

    deleted_attachment = await storage.delete_research_attachment(attachment["id"])
    assert deleted_attachment["id"] == attachment["id"]
    assert not attachment_path.exists()


@pytest.mark.asyncio
async def test_file_storage_research_result_preserves_resources(tmp_path: Path):
    storage = FileStorage(tmp_path)
    resources = [{
        "id": "chart-1",
        "type": "chart",
        "title": "年度趋势",
        "chart": {"kind": "line", "xKey": "year", "series": [{"key": "value"}], "rows": [{"year": 2025, "value": 1}]},
    }]
    result = await storage.create_research_result({
        "user_id": "researcher-1",
        "title": "带资源的结果",
        "content": "# 结果",
        "resources": resources,
    })
    loaded = await storage.get_research_result(result["id"])
    assert loaded["resources"] == resources


@pytest.mark.asyncio
@pytest.mark.parametrize("artifact_type, kind", [
    ("mind_map", "mind_map"),
    ("flashcards", "flashcards"),
    ("quiz", "quiz"),
    ("data_table", "data_table"),
])
async def test_structured_artifact_generators_have_local_fallback(monkeypatch, artifact_type, kind):
    monkeypatch.setattr(report_generator, "make_llm_provider", lambda: (_Provider("not-json"), "test-model"))
    content, metadata = await generate_artifact(artifact_type, "测试制品", SOURCE, {})
    assert content["kind"] == kind
    assert content["references"][0]["type"] == "latex"
    assert metadata["generator"] == "local"


@pytest.mark.asyncio
async def test_data_table_falls_back_when_ai_returns_a_narrow_table(monkeypatch):
    monkeypatch.setattr(report_generator, "make_llm_provider", lambda: (_Provider('{"columns":[{"key":"finding","label":"Finding"}],"rows":[{"finding":"one fact"}]}'), "test-model"))

    content, metadata = await generate_artifact("data_table", "Rich table", SOURCE, {"maxRows": 10})

    assert metadata["generator"] == "local"
    assert len(content["columns"]) == 8
    assert {column["key"] for column in content["columns"]} >= {"finding", "evidence", "method", "limitation"}


@pytest.mark.asyncio
async def test_data_table_captures_native_markdown_output(monkeypatch):
    markdown = "Study | Value | Date | Result\n---|---:|---|---\nA | 12 | 2025-01-01 | positive"
    monkeypatch.setattr(report_generator, "make_llm_provider", lambda: (_Provider(markdown), "test-model"))

    content, metadata = await generate_artifact("data_table", "Native table", SOURCE, {})

    assert metadata["generator"] == "ai"
    assert content["columns"][1]["type"] == "number"


@pytest.mark.asyncio
async def test_data_table_fallback_extracts_markdown_table(monkeypatch):
    monkeypatch.setattr(report_generator, "make_llm_provider", lambda: (_Provider("not-json"), "test-model"))

    content, metadata = await generate_artifact("data_table", "Model comparison", TABLE_SOURCE, {})

    assert metadata["generator"] == "local"
    assert [column["label"] for column in content["columns"]] == ["Vendor", "Model", "Price", "Release date"]
    assert content["rows"][0]["column_1"] == "Alpha"
    assert [column["type"] for column in content["columns"]] == ["text", "text", "percentage", "date"]


def test_data_table_normalizes_non_ascii_column_keys():
    content = {
        "kind": "data_table",
        "title": "Table",
        "columns": [{"key": "研究对象", "label": "Study population", "type": "text"}],
        "rows": [{"研究对象": "Group A"}],
    }

    normalized = validate_artifact_content("data_table", content, [{"type": "latex", "id": 1, "title": "Source"}])

    assert normalized["columns"][0]["key"] == "column_1"
    assert normalized["rows"][0]["column_1"] == "Group A"


def test_data_table_validation_and_csv_export():
    typed = {
        "kind": "data_table",
        "title": "Typed table",
        "columns": [
            {"key": "rate", "label": "Rate", "type": "text"},
            {"key": "date", "label": "Date", "type": "text"},
        ],
        "rows": [{"rate": "12.5%", "date": "2025-03-01"}],
    }
    typed_normalized = validate_artifact_content("data_table", typed, [{"type": "latex", "id": 1, "title": "Source"}])
    assert [column["type"] for column in typed_normalized["columns"]] == ["percentage", "date"]

    content = {
        "kind": "data_table",
        "title": "数据表",
        "columns": [{"key": "finding", "label": "核心发现"}],
        "rows": [{"finding": "结论"}],
    }
    normalized = validate_artifact_content("data_table", content, [{"type": "latex", "id": 1, "title": "实验文稿"}])
    assert "核心发现" in artifact_csv(normalized)
