import asyncio
from pathlib import Path

from nanobot.agent.tools.nature import NatureExecTool


def make_skill(root: Path, body: str) -> None:
    skill = root / "nature-demo"
    (skill / "scripts").mkdir(parents=True)
    (skill / "SKILL.md").write_text("# demo", encoding="utf-8")
    (skill / "scripts" / "probe.py").write_text(body, encoding="utf-8")


def run(tool: NatureExecTool, **kwargs: object) -> str:
    return asyncio.run(tool.execute(**kwargs))


def test_runs_from_skill_directory_and_passes_args_and_allowed_env(tmp_path: Path, monkeypatch) -> None:
    make_skill(tmp_path, "import os, sys\nprint(os.getcwd())\nprint(sys.argv[1])\nprint(os.getenv('NATURE_TEST_VALUE'))")
    monkeypatch.setenv("NATURE_TEST_VALUE", "ok")
    result = run(
        NatureExecTool(tmp_path, ["NATURE_TEST_VALUE"]),
        skill_name="nature-demo", script="scripts/probe.py", runtime="python", args=["hello"],
    )
    assert "hello" in result
    assert "ok" in result
    assert str(tmp_path / "nature-demo") in result
    assert "Exit code: 0" in result


def test_rejects_script_outside_skill(tmp_path: Path) -> None:
    make_skill(tmp_path, "print('ok')")
    result = run(
        NatureExecTool(tmp_path),
        skill_name="nature-demo", script="../outside.py", runtime="python", args=[],
    )
    assert "path traversal" in result


def test_times_out_and_reaps_process(tmp_path: Path) -> None:
    make_skill(tmp_path, "import time\ntime.sleep(2)")
    result = run(
        NatureExecTool(tmp_path),
        skill_name="nature-demo", script="scripts/probe.py", runtime="python", args=[], timeout=1,
    )
    assert "timed out" in result
