from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / ".nanobot"
    / "templates"
    / "researcher"
    / "skills"
    / "nature-figure"
    / "assets"
    / "figures4papers"
    / "figure_ophthal_review"
    / "plot_composition.py"
)
DATA_DIR = ROOT / "docs" / "figure-test-data"


def run_heatmap(input_csv: Path, output_prefix: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--input",
            str(input_csv),
            "--output",
            str(output_prefix),
            "--row-col",
            "行分类",
            "--column-col",
            "列分类",
            "--value-col",
            "表达值",
            "--color-map",
            "Reds",
            "--vmin",
            "0",
            "--vmax",
            "4",
        ],
        check=False,
        text=True,
        capture_output=True,
    )


def test_chinese_heatmap_complete_matrix_exports_bundle(tmp_path: Path) -> None:
    output_prefix = tmp_path / "heatmap_complete"
    result = run_heatmap(DATA_DIR / "heatmap_cn_complete.csv", output_prefix)

    assert result.returncode == 0, result.stderr
    bundle = json.loads(result.stdout)
    for key in ("png", "svg", "pdf", "tiff"):
        assert Path(bundle["outputs"][key]).is_file()
    qa_path = Path(bundle["qa"])
    assert qa_path.is_file()
    qa = json.loads(qa_path.read_text(encoding="utf-8"))
    assert qa["mapping"] == {"row": "行分类", "column": "列分类", "value": "表达值"}
    assert qa["row_count"] == 3
    assert qa["column_count"] == 3
    assert qa["matrix_cells"] == 9
    assert qa["validation"]["duplicate_policy"] == "fail"
    assert qa["validation"]["missing_matrix_policy"] == "fail"


def test_chinese_heatmap_duplicate_pairs_fail(tmp_path: Path) -> None:
    result = run_heatmap(DATA_DIR / "heatmap_cn_duplicate.csv", tmp_path / "heatmap_duplicate")

    assert result.returncode == 2
    assert "duplicate row-column combinations" in result.stderr
    assert "视网膜 / 对照组" in result.stderr


def test_chinese_heatmap_missing_matrix_cells_fail(tmp_path: Path) -> None:
    result = run_heatmap(DATA_DIR / "heatmap_cn_missing.csv", tmp_path / "heatmap_missing")

    assert result.returncode == 2
    assert "missing heatmap matrix combinations" in result.stderr
    assert "角膜 / 低剂量" in result.stderr


def test_heatmap_runs_through_figure_studio_worker(tmp_path: Path) -> None:
    from nanobot.services.research_jobs import _generate_figure_preview_job

    input_csv = tmp_path / "heatmap_cn_complete.csv"
    input_csv.write_text((DATA_DIR / "heatmap_cn_complete.csv").read_text(encoding="utf-8"), encoding="utf-8")

    class FakeStorage:
        def __init__(self) -> None:
            self.updated: dict[str, Any] = {}

        async def update_research_job(self, job_id: int, data: dict[str, Any]) -> bool:
            self.updated = data
            return True

    storage = FakeStorage()
    job = {
        "id": 88001,
        "userId": "tester",
        "payload": {
            "templateId": "heatmap",
            "filePath": str(input_csv),
            "mapping": {"row": "行分类", "column": "列分类", "value": "表达值"},
            "params": {
                "colorMap": "Reds",
                "showCellValues": False,
                "colorMin": 0,
                "colorMax": 4,
                "showColorbar": True,
            },
        },
    }

    import asyncio

    asyncio.run(_generate_figure_preview_job(storage, job))

    result = storage.updated["result"]
    assert result["template"] == "heatmap"
    assert result["renderer"] == "nature-figure/plot_composition.py"
    assert result["previewData"].startswith("data:image/png;base64,")
    for key in ("png", "svg", "pdf", "tiff"):
        assert Path(result["outputs"][key]).is_file()
    assert Path(result["qaPath"]).is_file()
    assert result["qa"]["parameters"]["show_values"] is False
    assert result["qa"]["parameters"]["vmin"] == 0
    assert result["qa"]["parameters"]["vmax"] == 4
