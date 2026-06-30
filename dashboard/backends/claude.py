"""Claude Code backend — https://docs.anthropic.com/en/docs/claude-code/overview"""

from __future__ import annotations

import json

from .protocol import (
    AssistantMessage,
    ChatBackend,
    Done,
    NormalizedEvent,
    TextDelta,
    ToolResult,
)


class ClaudeBackend(ChatBackend):
    name = "claude"

    @property
    def executable(self) -> str:
        return "claude"

    def _proxy_env(self, proxy_url: str) -> dict[str, str]:
        return {"ANTHROPIC_BASE_URL": proxy_url}

    def build_command(
        self,
        message: str,
        session_id: str,
        first: bool,
        project: dict | None = None,
        file_paths: list[str] | None = None,
        context_dirs: list[str] | None = None,
    ) -> list[str]:
        if file_paths:
            file_list = "\n".join(file_paths)
            message = f"{message}\n\n[Attached files]:\n{file_list}"

        cmd = [
            "claude", "-p", message,
            "--output-format", "stream-json",
            "--verbose",
            "--include-partial-messages",
            "--permission-mode", "bypassPermissions",
        ]

        if project is not None and project.get("system_prompt"):
            cmd += ["--append-system-prompt", project["system_prompt"]]

        for folder in (project or {}).get("folders", []):
            if folder.get("path"):
                cmd += ["--add-dir", folder["path"]]

        for d in (context_dirs or []):
            cmd += ["--add-dir", d]

        cmd += ["--session-id", session_id] if first else ["--resume", session_id]
        return cmd

    def parse_line(self, raw_line: str) -> NormalizedEvent | None:
        if not raw_line or raw_line.isspace():
            return None
        try:
            evt = json.loads(raw_line)
        except (json.JSONDecodeError, TypeError):
            return None

        if evt.get("type") == "stream_event":
            inner = evt.get("event", {})
            if inner.get("type") == "content_block_delta":
                delta = inner.get("delta", {})
                if delta.get("type") == "text_delta":
                    return TextDelta(content=delta.get("text", ""))
            return None

        if evt.get("type") == "assistant":
            tool_calls = []
            text_parts = []
            for block in evt.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    tool_calls.append({
                        "id": block["id"],
                        "name": block["name"],
                        "input": block.get("input"),
                    })
                elif block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
            return AssistantMessage(content="".join(text_parts), tool_calls=tool_calls)

        if evt.get("type") == "user":
            for block in evt.get("message", {}).get("content", []):
                if block.get("type") == "tool_result":
                    content = block.get("content")
                    text = content if isinstance(content, str) else json.dumps(content)
                    return ToolResult(id=block["tool_use_id"], content=text)
            return None

        if evt.get("type") == "result":
            return Done()

        return None
