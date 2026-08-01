"""Local UI for testing role-scoped agent workspaces and skill scripts."""

from __future__ import annotations

import asyncio
import json
import os
import shlex
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from nanobot import Nanobot
from nanobot.bus.events import InboundMessage
from nanobot.config.loader import get_config_path
from nanobot.config.paths import get_path_root


class AgentTestUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Nanobot Agent Tool Tester")
        self.root.geometry("1100x760")
        self.roles = ["student", "teacher", "researcher"]
        self.root_dir = get_path_root()
        self.role_var = tk.StringVar(value="researcher")
        self.user_var = tk.StringVar()
        self.skill_var = tk.StringVar()
        self.script_var = tk.StringVar()
        self._build()
        self._refresh_users()

    def _build(self) -> None:
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text="Role").grid(row=0, column=0, sticky="w")
        role = ttk.Combobox(top, textvariable=self.role_var, values=self.roles, state="readonly", width=18)
        role.grid(row=0, column=1, padx=6)
        role.bind("<<ComboboxSelected>>", lambda _: self._refresh_users())
        ttk.Label(top, text="User").grid(row=0, column=2, sticky="w")
        self.users = ttk.Combobox(top, textvariable=self.user_var, state="readonly", width=24)
        self.users.grid(row=0, column=3, padx=6)
        self.users.bind("<<ComboboxSelected>>", lambda _: self._refresh_workspace())
        self.workspace_label = ttk.Label(top, text="", foreground="#345")
        self.workspace_label.grid(row=1, column=0, columnspan=6, sticky="w", pady=(8, 0))

        body = ttk.PanedWindow(self.root, orient="horizontal")
        body.pack(fill="both", expand=True, padx=10, pady=8)
        left = ttk.Frame(body, padding=6)
        right = ttk.Frame(body, padding=6)
        body.add(left, weight=1)
        body.add(right, weight=2)

        ttk.Label(left, text="Role skills and scripts").pack(anchor="w")
        self.skills = ttk.Treeview(left, columns=("path",), show="tree headings")
        self.skills.heading("#0", text="Name")
        self.skills.heading("path", text="Path")
        self.skills.column("path", width=360)
        self.skills.pack(fill="both", expand=True, pady=6)
        self.skills.bind("<<TreeviewSelect>>", self._select_script)
        ttk.Label(left, text="Script arguments").pack(anchor="w")
        self.args = ttk.Entry(left)
        self.args.pack(fill="x", pady=4)
        script_buttons = ttk.Frame(left)
        script_buttons.pack(anchor="w", pady=4)
        ttk.Button(script_buttons, text="Show help", command=self._show_script_help).pack(side="left")
        ttk.Button(script_buttons, text="Run selected script", command=self._run_script).pack(side="left", padx=6)
        self.script_help = tk.Text(left, height=8, wrap="word", state="disabled")
        self.script_help.pack(fill="both", expand=True, pady=4)

        ttk.Label(right, text="Agent test prompt").pack(anchor="w")
        self.prompt = tk.Text(right, height=6, wrap="word")
        self.prompt.pack(fill="x", pady=6)
        self.prompt.insert("1.0", "Use list_dir to inspect the role skills directory and report the resolved path.")
        ttk.Button(right, text="Run agent", command=self._run_agent).pack(anchor="w", pady=4)
        ttk.Label(right, text="Direct tool execution").pack(anchor="w", pady=(12, 0))
        tool_row = ttk.Frame(right)
        tool_row.pack(fill="x", pady=4)
        ttk.Label(tool_row, text="Tool").pack(side="left")
        self.tool_var = tk.StringVar(value="list_dir")
        self.tool = ttk.Combobox(
            tool_row,
            textvariable=self.tool_var,
            values=["list_dir", "read_file", "glob", "grep", "exec"],
            state="readonly",
            width=18,
        )
        self.tool.pack(side="left", padx=6)
        self.tool.bind("<<ComboboxSelected>>", lambda _: self._set_tool_defaults())
        ttk.Button(tool_row, text="Execute", command=self._run_tool).pack(side="left")
        ttk.Label(right, text="Tool arguments (JSON)").pack(anchor="w")
        self.tool_args = tk.Text(right, height=4, wrap="word")
        self.tool_args.pack(fill="x", pady=4)
        self.tool_args.insert("1.0", '{"path": "skills", "recursive": true}')
        ttk.Label(right, text="Execution log").pack(anchor="w", pady=(10, 0))
        self.log = tk.Text(right, wrap="word", state="disabled")
        self.log.pack(fill="both", expand=True, pady=6)

    def _set_tool_defaults(self) -> None:
        defaults = {
            "list_dir": {"path": "skills", "recursive": True, "max_entries": 200},
            "read_file": {"path": "skills/nature-writing/SKILL.md", "offset": 1, "limit": 80},
            "glob": {"pattern": "skills/**/*.py"},
            "grep": {"pattern": "scripts", "path": "skills"},
            "exec": {"command": "python --version", "working_dir": ".", "timeout": 60},
        }
        value = json.dumps(defaults.get(self.tool_var.get(), {}), ensure_ascii=False, indent=2)
        self.tool_args.delete("1.0", "end")
        self.tool_args.insert("1.0", value)

    def _append(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text.rstrip() + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _role_template(self) -> Path:
        return self.root_dir / "templates" / self.role_var.get()

    def _user_workspace(self) -> Path:
        return self.root_dir / "users" / self.role_var.get() / self.user_var.get()

    def _refresh_users(self) -> None:
        base = self.root_dir / "users" / self.role_var.get()
        users = sorted(p.name for p in base.iterdir() if p.is_dir()) if base.is_dir() else []
        if not users:
            users = ["demo"]
        self.users["values"] = users
        self.user_var.set(users[0])
        self._refresh_workspace()
        self._refresh_skills()

    def _refresh_workspace(self) -> None:
        self.workspace_label.configure(
            text=f"Config: {get_config_path()} | User workspace: {self._user_workspace()} | Role workspace: {self._role_template()}"
        )

    def _refresh_skills(self) -> None:
        for item in self.skills.get_children():
            self.skills.delete(item)
        skills_dir = self._role_template() / "skills"
        if not skills_dir.is_dir():
            return
        for skill in sorted(p for p in skills_dir.iterdir() if p.is_dir()):
            parent = self.skills.insert("", "end", text=skill.name, values=(str(skill),))
            for script in sorted(p for p in skill.rglob("*") if p.is_file() and (p.suffix in {".py", ".sh", ".ps1", ".bat"} or p.name == "install.sh")):
                self.skills.insert(parent, "end", text=script.name, values=(str(script),))

    def _select_script(self, _event=None) -> None:
        selected = self.skills.selection()
        if selected:
            path = self.skills.item(selected[0], "values")
            if path and Path(path[0]).is_file():
                script_path = Path(path[0])
                self.script_var.set(path[0])
                self.args.delete(0, "end")
                example_args = self._script_example_args(script_path)
                self.args.insert(0, example_args)
                self._fill_exec_arguments(script_path, example_args)
                self._show_script_help()

    def _fill_exec_arguments(self, path: Path, args_text: str) -> None:
        args = shlex.split(args_text, posix=False) if args_text else []
        command = subprocess.list2cmdline(self._script_command(path, args))
        self.tool_var.set("exec")
        self.tool_args.delete("1.0", "end")
        self.tool_args.insert(
            "1.0",
            json.dumps(
                {"command": command, "working_dir": str(path.parent), "timeout": 600},
                ensure_ascii=False,
                indent=2,
            ),
        )

    @staticmethod
    def _script_example_args(path: Path) -> str:
        """Return safe, minimal demo arguments for common bundled scripts."""
        examples = {
            "academic_search.py": '"graph neural network" --limit 5',
            "format-converter.py": "--doi 10.1038/nature14539 --format ris",
            "nature_citation.py": '"https://doi.org/10.1038/nature14539"',
            "prepare_paper.py": "--help",
            "audit_paper_card.py": "--help",
            "preflight.py": "",
            "validate_figure.py": "--help",
            "audit_pptx_quality.py": "--help",
        }
        return examples.get(path.name, "--help" if path.suffix == ".py" else "")

    def _script_command(self, path: Path, extra: list[str] | None = None) -> list[str]:
        extra = extra or []
        if path.suffix == ".py":
            return [os.environ.get("PYTHON", "python"), str(path), *extra]
        if path.suffix == ".ps1":
            return ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(path), *extra]
        if path.suffix == ".sh":
            return ["bash", str(path), *extra]
        return [str(path), *extra]

    def _show_script_help(self) -> None:
        path = Path(self.script_var.get())
        if not path.is_file():
            return
        self._set_script_help("Loading --help ...")
        threading.Thread(target=self._help_worker, args=(path,), daemon=True).start()

    def _set_script_help(self, text: str) -> None:
        self.script_help.configure(state="normal")
        self.script_help.delete("1.0", "end")
        self.script_help.insert("1.0", text)
        self.script_help.configure(state="disabled")

    def _help_worker(self, path: Path) -> None:
        try:
            output = asyncio.run(self._exec_skill_command(path, ["--help"], timeout=30))
            self.root.after(0, self._set_script_help, output.strip() or "This script does not provide --help.")
        except Exception as exc:
            self.root.after(0, self._set_script_help, f"Unable to get help: {exc}")

    def _run_script(self) -> None:
        path = Path(self.script_var.get())
        if not path.is_file():
            messagebox.showwarning("Script", "Select a script first.")
            return
        args = shlex.split(self.args.get().strip(), posix=False) if self.args.get().strip() else []
        command = self._script_command(path, args)
        self._append(f"$ {' '.join(command)}\nworking_dir={path.parent}")
        threading.Thread(target=self._script_worker, args=(command, path.parent), daemon=True).start()

    def _script_worker(self, command: list[str], cwd: Path) -> None:
        try:
            path = Path(command[1]) if len(command) > 1 else Path(command[0])
            extra = command[2:] if path.suffix in {".py", ".ps1", ".sh"} else command[1:]
            output = asyncio.run(self._exec_skill_command(path, extra, timeout=600))
            self.root.after(0, self._append, output)
        except Exception as exc:
            self.root.after(0, self._append, f"Script error: {exc}")

    async def _exec_skill_command(self, path: Path, args: list[str], timeout: int) -> str:
        bot = Nanobot.from_config(get_config_path())
        loop = bot._loop
        context = loop._resolve_user_context(self.role_var.get(), self.user_var.get())
        if context:
            role_context, _ = context
            user_ws = role_context.workspace
            role_ws = role_context.role_workspace
            for tool in loop.tools._tools.values():
                if hasattr(tool, "_workspace"):
                    tool._workspace = user_ws
                if hasattr(tool, "_skill_workspace"):
                    tool._skill_workspace = role_ws
        exec_tool = loop.tools.get("exec")
        if exec_tool is None:
            raise RuntimeError("exec tool is not enabled")
        executable = self._script_command(path, args)
        command = subprocess.list2cmdline(executable)
        return await exec_tool.execute(command=command, working_dir=str(path.parent), timeout=timeout)

    def _run_agent(self) -> None:
        prompt = self.prompt.get("1.0", "end").strip()
        if not prompt:
            return
        role, user_id = self.role_var.get(), self.user_var.get()
        self._append(f"Agent role={role}, user={user_id}\nPrompt: {prompt}")
        threading.Thread(target=self._agent_worker, args=(prompt, role, user_id), daemon=True).start()

    def _run_tool(self) -> None:
        try:
            raw_args = self.tool_args.get("1.0", "end").strip() or "{}"
            args = json.loads(raw_args)
            if not isinstance(args, dict):
                raise ValueError("tool arguments must be a JSON object")
        except (json.JSONDecodeError, ValueError) as exc:
            messagebox.showerror(
                "Tool arguments",
                f"参数不是合法 JSON：{exc}\n\n请重新点击左侧脚本，让 UI 自动生成 exec 参数。",
            )
            return
        tool_name = self.tool_var.get()
        self._append(f"Tool: {tool_name}\nArguments: {json.dumps(args, ensure_ascii=False)}")
        threading.Thread(target=self._tool_worker, args=(tool_name, args), daemon=True).start()

    def _tool_worker(self, tool_name: str, args: dict) -> None:
        async def run() -> str:
            bot = Nanobot.from_config(get_config_path())
            loop = bot._loop
            context = loop._resolve_user_context(self.role_var.get(), self.user_var.get())
            if context:
                role_context, _ = context
                user_ws = role_context.workspace
                role_ws = role_context.role_workspace
                for tool in loop.tools._tools.values():
                    if hasattr(tool, "_workspace"):
                        tool._workspace = user_ws
                    if hasattr(tool, "_skill_workspace"):
                        tool._skill_workspace = role_ws
                allowed = loop.tools.get(tool_name)
            else:
                allowed = loop.tools.get(tool_name)
            if allowed is None:
                raise ValueError(f"unknown tool: {tool_name}")
            result = await allowed.execute(**args)
            return result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, indent=2)
        try:
            result = asyncio.run(run())
            self.root.after(0, self._append, "Tool result:\n" + result)
        except Exception as exc:
            self.root.after(0, self._append, f"Tool error: {exc}")

    def _agent_worker(self, prompt: str, role: str, user_id: str) -> None:
        async def run() -> str:
            bot = Nanobot.from_config(get_config_path())
            msg = InboundMessage(channel="local-ui", sender_id=user_id, chat_id=user_id, content=prompt, metadata={"role": role, "user_id": user_id})
            response = await bot._loop._process_message(msg, session_key=f"local-ui:{role}:{user_id}", user_ctx_sessions=bot._loop._resolve_user_context(role, user_id))
            return response.content if response else "(no response)"
        try:
            result = asyncio.run(run())
            self.root.after(0, self._append, "Agent result:\n" + result)
        except Exception as exc:
            self.root.after(0, self._append, f"Agent error: {exc}")


def main() -> None:
    root = tk.Tk()
    AgentTestUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
