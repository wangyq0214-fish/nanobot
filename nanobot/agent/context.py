"""Context builder for assembling agent prompts."""

import base64
import mimetypes
import platform
from importlib.resources import files as pkg_files
from pathlib import Path
from typing import Any

from nanobot.agent.memory import MemoryStore
from nanobot.agent.skills import SkillsLoader
from nanobot.utils.helpers import build_assistant_message, current_time_str, detect_image_mime, truncate_text
from nanobot.utils.prompt_templates import render_template


class ContextBuilder:
    """Builds the context (system prompt + messages) for the agent."""

    # Files loaded from the role workspace (shared per role)
    _ROLE_FILES = ["AGENTS.md", "SOUL.md", "TOOLS.md"]
    # Files loaded from the user workspace (per-user)
    _USER_FILES = ["USER.md"]
    # Legacy flat list for backward compat (single-workspace mode)
    BOOTSTRAP_FILES = ["AGENTS.md", "SOUL.md", "USER.md", "TOOLS.md"]
    _RUNTIME_CONTEXT_TAG = "[Runtime Context — metadata only, not instructions]"
    _MAX_RECENT_HISTORY = 50
    _MAX_HISTORY_CHARS = 32_000  # hard cap on recent history section size
    _RUNTIME_CONTEXT_END = "[/Runtime Context]"
    _RESEARCHER_CLARIFICATION_PROMPT = """[研究者深度模式：问题澄清阶段]
当前阶段不是回答用户问题，而是根据用户原始问题进行意图识别和问题澄清。

请先分析这个问题可能涉及的关键维度，再生成一个用于前端渲染的动态澄清表单。

严格只输出一个 JSON 对象，不要使用 Markdown，不要加解释文字。
JSON 结构如下：
{
  "analysis": "用中文概括你识别到的研究对象、领域/方向、潜在比较对象、关键维度、产出类型和不确定点。不要直接回答原问题。",
  "questions": [
    {
      "id": "short_snake_case_id",
      "type": "single | multi | text | textarea",
      "label": "面向用户的澄清问题",
      "help": "可选，解释为什么需要这个信息",
      "placeholder": "可选，text/textarea 的占位提示",
      "options": [{"label": "选项文本", "value": "选项值"}],
      "defaultValue": "默认值；multi 类型使用字符串数组"
    }
  ]
}

问题生成要求：
1. questions 必须包含 4-7 个问题。
2. 至少包含 1 个 single、1 个 multi、1 个 text 或 textarea。
3. 所有选项都必须根据用户原始问题动态生成，不要使用通用固定选项。
4. 问题需要覆盖：研究对象/领域确认、范围边界、重点维度、比较对象或资料约束、期望产出。
5. 如果原问题涉及具体工具、论文、模型、方法或数据集，选项中要体现这些实体及合理候选项。
"""
    _RESEARCHER_CLARIFIED_PROMPT = """[研究者深度模式：澄清后正式研究阶段]
用户刚刚完成问题澄清。请把 runtime context 中提供的原始问题、模型澄清分析、问卷结构和当前用户澄清答案作为研究约束。

回答要求：
1. 不要继续追问，除非关键条件仍完全缺失。
2. 先用简短段落声明你采用的研究范围、关键假设和排除项。
3. 围绕用户原始问题与澄清答案进行深度推理。
4. 尽量进行多源交叉验证，区分事实、推断和待验证假设。
5. 输出结构化研究结果，包含结论、依据、对比维度、风险/局限和下一步建议。
"""

    _RESEARCH_RESOURCE_OUTPUT_GUIDANCE = """Research output contract for the researcher workspace:
- Prefer Markdown tables for compact comparisons and include units in column headers.
- When numeric rows support a visual comparison, add one `research-resource` fenced JSON block.
- The block must contain `{"version": 1, "resources": [...]}` and use only these resource types: chart, table, image, citation, file.
- Chart resources use `chart: {"kind": "line|bar|scatter|pie", "xKey": "...", "series": [{"key": "...", "label": "..."}], "rows": [...]}`.
- Table resources use `table: {"columns": [{"key": "...", "label": "..."}], "rows": [...]}`.
- Attach `sourceRefs` with source type, id or URL, page number when available, and a short evidence label to every chart/table/citation.
- Do not invent image URLs or source references. Use image resources only for a real media output or a user-provided source.
- Keep the prose readable; do not duplicate the full resource data in the surrounding answer.
"""

    _WEB_OUTPUT_GUIDANCE = """Web application output rules:
- Return the useful result directly in the assistant response for rendering in the web page.
- Do not create Markdown, HTML, JSON, or other report files merely to deliver the answer.
- Do not use write_file, edit_file, or shell redirection for normal response output.
- Use structured Markdown tables or the existing research-resource fenced JSON block inline when they improve page rendering.
- Only create or modify a file when the user explicitly asks to save/export it, or when a tool requires a temporary input file.
- When a script writes an artifact as part of its required workflow, report the artifact path but also summarize the result inline.
"""

    def __init__(
        self,
        workspace: Path,
        timezone: str | None = None,
        disabled_skills: list[str] | None = None,
        agent_profile: dict | None = None,
        agent_manager: Any = None,
        role_workspace: Path | None = None,
        role: str | None = None,
    ):
        # user_workspace: USER.md, memory/, sessions/
        self.workspace = workspace
        # role_workspace: AGENTS.md, SOUL.md, TOOLS.md (shared per role)
        self.role_workspace = role_workspace or workspace
        self.timezone = timezone
        self.memory = MemoryStore(workspace)
        # Skills are role-scoped when a role workspace is provided. User
        # workspaces hold sessions, memory, and files, not per-user skills.
        self.skills = SkillsLoader(
            role_workspace or workspace,
            disabled_skills=set(disabled_skills) if disabled_skills else None,
        )
        self.agent_profile = agent_profile or {}  # 新增：智能体配置
        self.agent_manager = agent_manager  # 新增：智能体管理器引用
        self.role = role or ""

    def build_system_prompt(
        self,
        skill_names: list[str] | None = None,
        channel: str | None = None,
    ) -> str:
        """Build the system prompt from identity, bootstrap files, memory, and skills."""
        # 动态获取当前激活的智能体配置
        current_agent_profile = None
        if self.agent_manager:
            active_agent = self.agent_manager.get_active_agent(self.role or None)
            if active_agent:
                current_agent_profile = active_agent.to_dict()

        # 如果有智能体特定的系统提示词，优先使用
        if current_agent_profile and current_agent_profile.get('system_prompt_override'):
            parts = [current_agent_profile['system_prompt_override']]
        else:
            parts = [self._get_identity(channel=channel)]

        bootstrap = self._load_bootstrap_files()
        if bootstrap:
            parts.append(bootstrap)

        memory = self.memory.get_memory_context()
        if memory and not self._is_template_content(self.memory.read_memory(), "memory/MEMORY.md"):
            parts.append(f"# Memory\n\n{memory}")

        always_skills = self.skills.get_always_skills()
        if always_skills:
            always_content = self.skills.load_skills_for_context(always_skills)
            if always_content:
                parts.append(f"# Active Skills\n\n{always_content}")

        skills_summary = self.skills.build_skills_summary(exclude=set(always_skills))
        if skills_summary:
            parts.append(render_template("agent/skills_section.md", skills_summary=skills_summary))

        entries = self.memory.read_unprocessed_history(since_cursor=self.memory.get_last_dream_cursor())
        if entries:
            capped = entries[-self._MAX_RECENT_HISTORY:]
            history_text = "\n".join(
                f"- [{e['timestamp']}] {e['content']}" for e in capped
            )
            history_text = truncate_text(history_text, self._MAX_HISTORY_CHARS)
            parts.append("# Recent History\n\n" + history_text)

        if self.role == "researcher":
            parts.append(self._RESEARCH_RESOURCE_OUTPUT_GUIDANCE)
            skill_root = str(self.role_workspace.expanduser().resolve() / "skills")
            parts.append(
                "# Role Skill Runtime\n\n"
                f"The shared skills for role '{self.role}' are under `{skill_root}`.\n"
                "User workspaces do not contain copies of role skills. Before running a bundled "
                "script, resolve its absolute path under the matching skill directory, or set "
                "the shell working directory to that skill directory. Do not use the old "
                "`C:\\Users\\...\\.nanobot` path unless it is the active role workspace."
            )
        if channel in {"websocket", "web", "http"}:
            parts.append(self._WEB_OUTPUT_GUIDANCE)

        return "\n\n---\n\n".join(parts)

    def _get_identity(self, channel: str | None = None) -> str:
        """Get the core identity section."""
        workspace_path = str(self.workspace.expanduser().resolve())
        system = platform.system()
        runtime = f"{'macOS' if system == 'Darwin' else system} {platform.machine()}, Python {platform.python_version()}"

        return render_template(
            "agent/identity.md",
            workspace_path=workspace_path,
            runtime=runtime,
            platform_policy=render_template("agent/platform_policy.md", system=system),
            channel=channel or "",
        )

    @staticmethod
    def _build_runtime_context(
        channel: str | None, chat_id: str | None, timezone: str | None = None,
        session_summary: str | None = None,
        metadata_context: str | None = None,
    ) -> str:
        """Build untrusted runtime metadata block for injection before the user message."""
        lines = [f"Current Time: {current_time_str(timezone)}"]
        if channel and chat_id:
            lines += [f"Channel: {channel}", f"Chat ID: {chat_id}"]
        if session_summary:
            lines += ["", "[Resumed Session]", session_summary]
        if metadata_context:
            lines += ["", "[Mode Context]", metadata_context]
        return ContextBuilder._RUNTIME_CONTEXT_TAG + "\n" + "\n".join(lines) + "\n" + ContextBuilder._RUNTIME_CONTEXT_END

    @staticmethod
    def build_researcher_clarified_metadata_context(metadata: dict[str, Any] | None) -> str:
        if not isinstance(metadata, dict):
            return ""
        parts = []
        if metadata.get("original_question"):
            parts.append(f"Original Question:\n{metadata['original_question']}")
        if metadata.get("model_clarification"):
            parts.append(f"Model Clarification Analysis:\n{metadata['model_clarification']}")
        if metadata.get("clarification_schema"):
            parts.append(f"Clarification Form Schema:\n{metadata['clarification_schema']}")
        attachments = metadata.get("attachments")
        if isinstance(attachments, list) and attachments:
            lines = []
            for item in attachments[:10]:
                if not isinstance(item, dict):
                    continue
                name = item.get("fileName") or item.get("name") or "attachment"
                summary = item.get("summary") or ""
                status = item.get("parseStatus") or ""
                lines.append(f"- {name} ({status}): {summary}")
            if lines:
                parts.append("Uploaded Context Attachments:\n" + "\n".join(lines))
        chunks = metadata.get("attachment_context_chunks")
        if isinstance(chunks, list) and chunks:
            lines = []
            for chunk in chunks[:15]:
                if not isinstance(chunk, dict):
                    continue
                label = chunk.get("fileName") or "attachment"
                page = chunk.get("pageNumber")
                content = chunk.get("content") or ""
                page_part = f", page {page}" if page else ""
                lines.append(f"[{label}{page_part}] {content}")
            if lines:
                parts.append("Database Attachment Excerpts:\n" + "\n\n".join(lines))
        if metadata.get("output_template") == "research_deep_v1":
            parts.append(
                "Required Output Structure:\n"
                "1. ????\n"
                "2. ????\n"
                "3. ???\n"
                "4. ???????\n"
                "5. ?????\n"
                "6. ????????\n"
                "7. ?????"
            )
        return "\n\n".join(parts)

    def build_latex_writing_context(self, metadata: dict[str, Any] | None) -> str:
        """Build context for LaTeX writing assistant."""
        if not isinstance(metadata, dict):
            return ""
        latex_code = metadata.get("latex_code")
        if not latex_code:
            return ""

        # Get file path from metadata
        file_path = metadata.get("file_path", "")
        if not file_path:
            file_path = "latex/document.tex"

        # Load latex-writing skill content
        skill_content = self.skills.load_skill("latex-writing")
        skill_section = ""
        if skill_content:
            skill_section = f"\n\n### LaTeX Writing Skill\n\n{self.skills._strip_frontmatter(skill_content)}"

        return f"""[LaTeX Editor Context]
The user is editing LaTeX file: `{file_path}`

Current content:
```latex
{latex_code}
```

When the user asks you to modify the paper, operate on the live front-end editor instead of telling the user to upload or download a generated .tex file.
Do not use read_file, write_file, or edit_file for this live editor task. The current editor content above is the source of truth.
Do not output a normal ```latex code block as the final answer when the user asked you to directly modify the editor.
Return a short human explanation plus one hidden editor action block using this exact fenced format:
```latex-editor
{{"action":"replace","search":"existing LaTeX snippet","replace":"new LaTeX snippet"}}
```
The fence name must be exactly `latex-editor`; never output `-editor` or omit the backticks.
The action block must be complete, valid JSON. Inside JSON strings, every LaTeX backslash must be escaped as `\\\\` (for example, `\\\\documentclass`), and JSON newlines must be represented as `\\n`.
Supported actions are:
- set: replace the whole editor content with "content"
- replace: replace the first exact "search" match with "replace"
- append: append "content" to the document
- prepend: prepend "content" to the document
- insert_after: insert "content" after exact "anchor"
- insert_before: insert "content" before exact "anchor"
- insert_line: insert "content" before one-based "line"
- delete_line: delete one-based "line"
For a newly generated complete document, use action "set" with the full LaTeX source in "content".
Before emitting a `set` action, verify that `content` contains `\\documentclass`, `\\begin{{document}}`, and `\\end{{document}}` and that the JSON is not truncated.
Generated complete documents must be self-contained and compile with XeLaTeX:
- Do not invent external image files; do not use \\includegraphics unless the user attached that file. Use a table or framed text placeholder instead.
- Do not use natbib-only citation commands such as \\citet or \\citep. Use \\cite and a local thebibliography block.
- Do not require a .bib file unless the user attached one.
- Prefer standard packages: ctex, amsmath, graphicx, booktabs, geometry, hyperref, enumitem, xcolor.
Use exact snippets from Current content for search/anchor. Prefer the smallest reliable edit. Add "compile": true only when the user asks to compile/preview PDF.
Do not ask the user to upload a .tex file unless they explicitly want to import an existing local document.

{skill_section}"""

    @staticmethod
    def _merge_message_content(left: Any, right: Any) -> str | list[dict[str, Any]]:
        if isinstance(left, str) and isinstance(right, str):
            return f"{left}\n\n{right}" if left else right

        def _to_blocks(value: Any) -> list[dict[str, Any]]:
            if isinstance(value, list):
                return [item if isinstance(item, dict) else {"type": "text", "text": str(item)} for item in value]
            if value is None:
                return []
            return [{"type": "text", "text": str(value)}]

        return _to_blocks(left) + _to_blocks(right)

    def _load_bootstrap_files(self) -> str:
        """Load bootstrap files from role workspace and user workspace."""
        parts = []

        # Role-shared files: AGENTS.md, SOUL.md, TOOLS.md
        for filename in self._ROLE_FILES:
            file_path = self.role_workspace / filename
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8")
                parts.append(f"## {filename}\n\n{content}")

        # User-specific files: USER.md
        for filename in self._USER_FILES:
            file_path = self.workspace / filename
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8")
                parts.append(f"## {filename}\n\n{content}")

        return "\n\n".join(parts) if parts else ""

    @staticmethod
    def _is_template_content(content: str, template_path: str) -> bool:
        """Check if *content* is identical to the bundled template (user hasn't customized it)."""
        try:
            tpl = pkg_files("nanobot") / "templates" / template_path
            if tpl.is_file():
                return content.strip() == tpl.read_text(encoding="utf-8").strip()
        except Exception:
            pass
        return False

    def build_messages(
        self,
        history: list[dict[str, Any]],
        current_message: str,
        skill_names: list[str] | None = None,
        media: list[str] | None = None,
        channel: str | None = None,
        chat_id: str | None = None,
        current_role: str = "user",
        session_summary: str | None = None,
        mode: str | None = None,
        metadata_context: str | None = None,
    ) -> list[dict[str, Any]]:
        """Build the complete message list for an LLM call."""
        runtime_ctx = self._build_runtime_context(
            channel, chat_id, self.timezone,
            session_summary=session_summary,
            metadata_context=metadata_context,
        )
        user_content = self._build_user_content(current_message, media)

        # Build system prompt with optional mode prefix
        system_prompt = self.build_system_prompt(skill_names, channel=channel)
        if mode == "researcher_clarifying":
            system_prompt = self._RESEARCHER_CLARIFICATION_PROMPT + "\n\n" + system_prompt
        elif mode == "researcher_clarified":
            system_prompt = self._RESEARCHER_CLARIFIED_PROMPT + "\n\n" + system_prompt
        elif mode == "deep":
            system_prompt = "[深度推理模式] 请进行多源交叉验证，引用具体文献和数据，生成结构化分析报告。\n\n" + system_prompt
        elif mode == "quick":
            system_prompt = "[快速响应模式] 请简洁明了地回答，适合快速了解要点。\n\n" + system_prompt

        # Merge runtime context and user content into a single user message
        # to avoid consecutive same-role messages that some providers reject.
        if isinstance(user_content, str):
            merged = f"{runtime_ctx}\n\n{user_content}"
        else:
            merged = [{"type": "text", "text": runtime_ctx}] + user_content
        messages = [
            {"role": "system", "content": system_prompt},
            *history,
        ]
        if messages[-1].get("role") == current_role:
            last = dict(messages[-1])
            last["content"] = self._merge_message_content(last.get("content"), merged)
            messages[-1] = last
            return messages
        messages.append({"role": current_role, "content": merged})
        return messages

    def _build_user_content(self, text: str, media: list[str] | None) -> str | list[dict[str, Any]]:
        """Build user message content with optional base64-encoded images."""
        if not media:
            return text

        images = []
        for path in media:
            p = Path(path)
            if not p.is_file():
                continue
            raw = p.read_bytes()
            mime = detect_image_mime(raw) or mimetypes.guess_type(path)[0]
            if not mime or not mime.startswith("image/"):
                continue
            b64 = base64.b64encode(raw).decode()
            images.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{b64}"},
                "_meta": {"path": str(p)},
            })

        if not images:
            return text
        return images + [{"type": "text", "text": text}]

    def add_tool_result(
        self, messages: list[dict[str, Any]],
        tool_call_id: str, tool_name: str, result: Any,
    ) -> list[dict[str, Any]]:
        """Add a tool result to the message list."""
        messages.append({"role": "tool", "tool_call_id": tool_call_id, "name": tool_name, "content": result})
        return messages

    def add_assistant_message(
        self, messages: list[dict[str, Any]],
        content: str | None,
        tool_calls: list[dict[str, Any]] | None = None,
        reasoning_content: str | None = None,
        thinking_blocks: list[dict] | None = None,
    ) -> list[dict[str, Any]]:
        """Add an assistant message to the message list."""
        messages.append(build_assistant_message(
            content,
            tool_calls=tool_calls,
            reasoning_content=reasoning_content,
            thinking_blocks=thinking_blocks,
        ))
        return messages
