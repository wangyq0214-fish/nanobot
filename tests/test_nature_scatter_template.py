from __future__ import annotations

import asyncio
import json
import math
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "docs" / "figure-test-data"


class FakeStorage:
    def __init__(self) -> None:
        self.updated: dict[str, Any] = {}

    async def update_research_job(self, job_id: int, data: dict[str, Any]) -> bool:
        self.updated = data
        return True


def run_scatter_worker(input_csv: Path, tmp_path: Path, mapping: dict[str, str], params: dict[str, Any]) -> dict[str, Any]:
    from nanobot.services.research_jobs import _generate_figure_preview_job

    copied = tmp_path / input_csv.name
    copied.write_text(input_csv.read_text(encoding="utf-8"), encoding="utf-8")
    storage = FakeStorage()
    job = {
        "id": 88101,
        "userId": "tester",
        "payload": {
            "templateId": "scatter",
            "filePath": str(copied),
            "mapping": mapping,
            "params": params,
        },
    }

    asyncio.run(_generate_figure_preview_job(storage, job))
    return storage.updated["result"]


def assert_export_bundle(result: dict[str, Any]) -> None:
    assert result["template"] == "scatter"
    assert result["renderer"] == "python/scatter"
    assert result["previewData"].startswith("data:image/png;base64,")
    for key in ("png", "svg", "pdf", "tiff"):
        assert Path(result["outputs"][key]).is_file()
    qa_path = Path(result["qaPath"])
    assert qa_path.is_file()
    assert json.loads(qa_path.read_text(encoding="utf-8")) == result["qa"]


def test_scatter_exports_without_group(tmp_path: Path) -> None:
    result = run_scatter_worker(
        DATA_DIR / "scatter_cn_no_group.csv",
        tmp_path,
        {"x": "x", "y": "y"},
        {"trendLine": False},
    )

    assert_export_bundle(result)
    assert result["qa"]["mapping"] == {"x": "x", "y": "y", "group": None}
    assert result["qa"]["rows_plotted"] == 6
    assert result["qa"]["parameters"]["group_order"] == ["All observations"]
    assert result["qa"]["parameters"]["trends"] == []


def test_scatter_exports_with_chinese_groups(tmp_path: Path) -> None:
    result = run_scatter_worker(
        DATA_DIR / "scatter_cn_group.csv",
        tmp_path,
        {"x": "x", "y": "y", "group": "group"},
        {"trendLine": False},
    )

    assert_export_bundle(result)
    assert result["qa"]["parameters"]["group_order"] == ["对照组", "处理组"]
    assert result["qa"]["parameters"]["group_counts"] == {"对照组": 4, "处理组": 4}


def test_scatter_trend_line_uses_actual_group_data(tmp_path: Path) -> None:
    result = run_scatter_worker(
        DATA_DIR / "scatter_cn_trend.csv",
        tmp_path,
        {"x": "x", "y": "y", "group": "group"},
        {"trendLine": True, "trendLineScope": "by_group"},
    )

    assert_export_bundle(result)
    trends = result["qa"]["parameters"]["trends"]
    assert [trend["group"] for trend in trends] == ["低剂量", "高剂量"]
    low = next(trend for trend in trends if trend["group"] == "低剂量")
    high = next(trend for trend in trends if trend["group"] == "高剂量")
    assert math.isclose(low["slope"], 0.82, rel_tol=0.05)
    assert math.isclose(high["slope"], 1.34, rel_tol=0.05)
    assert low["r_squared"] > 0.98
    assert high["r_squared"] > 0.98


def test_scatter_api_validation_rejects_missing_numeric_values(tmp_path: Path) -> None:
    from nanobot.api.handlers.figure_studio import _validate_scatter_csv

    bad_csv = tmp_path / "scatter_bad.csv"
    bad_csv.write_text("x,y,group\n0,1,对照组\n1,,处理组\n", encoding="utf-8")

    errors = _validate_scatter_csv(bad_csv, {"x": "x", "y": "y", "group": "group"}, {"trendLine": True})

    assert errors
    assert "缺失或非数值" in errors[0]
