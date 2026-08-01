"""Safe execution of bundled Nature skill scripts."""

from __future__ import annotations

import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Any

from nanobot.agent.skills import BUILTIN_SKILLS_DIR
from nanobot.agent.tools.base import Tool, tool_parameters
from nanobot.agent.tools.schema import ArraySchema, IntegerSchema, StringSchema, tool_parameters_schema


@tool_parameters(
    tool_parameters_schema(
        skill_name=StringSchema("Nature skill directory name"),
        script=StringSchema("Script path relative to the skill directory"),
        runtime=StringSchema("Script runtime", enum=("python", "node")),
        args=ArraySchema(StringSchema("One script argument")),
        timeout=IntegerSchema(180, minimum=1, maximum=900),
        required=["skill_name", "script", "runtime", "args"],
    )
)
class NatureExecTool(Tool):
    """Run a bundled Nature script without relying on the caller's cwd or shell."""

    @property
    def name(self) -> str:
        return "nature_exec"

    @property
    def description(self) -> str:
        return (
            "Run a bundled Nature skill Python or Node script. "
            "Use a skill-relative script path and pass arguments as an array. "
            "Large output is summarized; inspect declared output files instead."
        )

    def __init__(self, skill_root: Path | None = None, allowed_env_keys: list[str] | None = None):
        self.skill_root = (skill_root or BUILTIN_SKILLS_DIR).resolve()
        self.allowed_env_keys = set(allowed_env_keys or [])

    async def execute(
        self, skill_name: str, script: str, runtime: str, args: list[str],
        timeout: int = 180, **_: Any,
    ) -> str:
        if runtime not in {"python", "node"}:
            return "Error: runtime must be python or node"
        if any(Path(part).name in {".", ".."} for part in Path(script).parts):
            return "Error: script path traversal is not allowed"

        skill_dir = (self.skill_root / skill_name).resolve()
        script_path = (skill_dir / script).resolve()
        if self.skill_root not in skill_dir.parents or not (skill_dir / "SKILL.md").is_file():
            return "Error: unknown Nature skill"
        if skill_dir not in script_path.parents or not script_path.is_file():
            return "Error: script must be an existing file inside the skill directory"

        executable = "python" if runtime == "python" else "node"
        command = [executable, str(script_path), *[str(value) for value in args]]
        env = {"PATH": os.environ.get("PATH", ""), "PYTHONUTF8": "1"}
        for key in self.allowed_env_keys:
            if key in os.environ:
                env[key] = os.environ[key]
        started = time.monotonic()
        try:
            process = await asyncio.create_subprocess_exec(
                *command, cwd=str(skill_dir), env=env,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=min(timeout, 900))
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return f"Error: Nature script timed out after {min(timeout, 900)} seconds"
        except FileNotFoundError:
            return f"Error: required runtime not found: {executable}"
        except Exception as exc:
            return f"Error executing Nature script: {exc}"

        def decode(value: bytes) -> str:
            return value.decode("utf-8", errors="replace")

        out = decode(stdout).strip()
        err = decode(stderr).strip()
        text = out
        if err:
            text += ("\n" if text else "") + "STDERR:\n" + err
        text += f"\nExit code: {process.returncode}\nDuration: {time.monotonic() - started:.1f}s"
        if len(text) > 10_000:
            text = text[:4_500] + "\n... output truncated; inspect generated artifacts ...\n" + text[-4_500:]
        return text or "(no output)"
