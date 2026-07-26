"""Tool for sending structured LaTeX editor actions to a live client."""

from __future__ import annotations

import json
from typing import Any

from nanobot.agent.tools.base import Tool, tool_parameters


_ACTION_ENUM = [
    "get",
    "structure",
    "set",
    "replace",
    "append",
    "prepend",
    "insert_after",
    "insert_before",
    "insert_line",
    "delete_line",
]


@tool_parameters(
    {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": _ACTION_ENUM,
                "description": "Editor action to perform.",
            },
            "content": {
                "type": ["string", "null"],
                "description": "LaTeX content for set/append/prepend/insert actions.",
            },
            "search": {
                "type": ["string", "null"],
                "description": "Exact text to replace.",
            },
            "replace": {
                "type": ["string", "null"],
                "description": "Replacement text for replace actions.",
            },
            "anchor": {
                "type": ["string", "null"],
                "description": "Exact text anchor for insert_before/insert_after actions.",
            },
            "line": {
                "type": ["integer", "null"],
                "minimum": 1,
                "description": "One-based line number for insert_line/delete_line actions.",
            },
            "compile": {
                "type": ["boolean", "null"],
                "description": "Whether the client should compile after applying the action.",
            },
        },
        "required": ["action"],
    }
)
class LatexEditorTool(Tool):
    """Send a structured edit instruction to the current LaTeX editor."""

    def __init__(self) -> None:
        self._channel: Any | None = None
        self._connection: Any | None = None

    @property
    def name(self) -> str:
        return "latex_editor"

    @property
    def description(self) -> str:
        return (
            "Modify the user's currently open LaTeX editor with structured actions. "
            "Use exact snippets for replace/anchor actions and prefer the smallest reliable edit."
        )

    def set_context(self, channel: Any, connection: Any, *_args: Any, **_kwargs: Any) -> None:
        """Set the active WebSocket channel and connection."""
        self._channel = channel
        self._connection = connection

    async def execute(
        self,
        action: str | None = None,
        content: str | None = None,
        search: str | None = None,
        replace: str | None = None,
        anchor: str | None = None,
        line: int | None = None,
        compile: bool | None = None,
        **_kwargs: Any,
    ) -> str:
        if not action:
            return self._error("action is required")
        if action not in _ACTION_ENUM:
            return self._error(f"unknown action: {action}")

        validation_error = self._validate_action(action, content, search, replace, anchor, line)
        if validation_error:
            return self._error(validation_error)

        if self._channel is None or self._connection is None:
            return self._error("No WebSocket connection available for LaTeX editor")
        send_event = getattr(self._channel, "_send_event", None)
        if not callable(send_event):
            return self._error("No WebSocket connection available for LaTeX editor")

        payload: dict[str, Any] = {"action": action}
        for key, value in (
            ("content", content),
            ("search", search),
            ("replace", replace),
            ("anchor", anchor),
            ("line", line),
            ("compile", compile),
        ):
            if value is not None:
                payload[key] = value

        conn_default = getattr(self._channel, "_conn_default", None)
        chat_id = conn_default.get(self._connection) if isinstance(conn_default, dict) else None
        if isinstance(chat_id, str) and chat_id:
            payload["chat_id"] = chat_id

        await send_event(self._connection, "latex_editor_action", **payload)
        return json.dumps({"status": "sent", **payload}, ensure_ascii=False)

    @staticmethod
    def _validate_action(
        action: str,
        content: str | None,
        search: str | None,
        replace: str | None,
        anchor: str | None,
        line: int | None,
    ) -> str | None:
        if action in {"set", "append", "prepend", "insert_after", "insert_before", "insert_line"} and content is None:
            return "content is required"
        if action == "replace" and not search:
            return "search is required"
        if action == "replace" and replace is None and content is None:
            return "replace or content is required"
        if action in {"insert_after", "insert_before"} and not anchor:
            return "anchor is required"
        if action in {"insert_line", "delete_line"} and line is None:
            return "line is required"
        return None

    @staticmethod
    def _error(message: str) -> str:
        return json.dumps({"status": "error", "message": message}, ensure_ascii=False)
