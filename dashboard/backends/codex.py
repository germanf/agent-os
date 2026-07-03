"""GPT Codex backend — https://github.com/openai/codex"""

from __future__ import annotations

import json

from .protocol import ChatBackend, Done, NormalizedEvent, TextDelta


class CodexBackend(ChatBackend):
    name = "codex"

    @property
    def executable(self) -> str:
        return "codex"

    def _proxy_env(self, proxy_url: str) -> dict[str, str]:
        return {"OPENAI_BASE_URL": f"{proxy_url}/v1"}

    def build_command(
        self,
        message: str,
        session_id: str,
        first: bool,
        project: dict | None = None,
        file_paths: list[str] | None = None,
        context_dirs: list[str] | None = None,
        mcp_manifest: str | None = None,
    ) -> list[str]:
        cmd = ["codex", "-p", message, "--output-format", "json"]

        cmd += ["--session-id", session_id] if first else ["--resume", session_id]

        if mcp_manifest:
            cmd += ["--instructions", mcp_manifest]

        for d in (context_dirs or []):
            cmd += ["--add-dir", d]

        return cmd

    def parse_line(self, raw_line: str) -> NormalizedEvent | None:
        if not raw_line or raw_line.isspace():
            return None
        try:
            evt = json.loads(raw_line)
        except (json.JSONDecodeError, TypeError):
            return TextDelta(content=raw_line)

        if evt.get("type") == "text":
            return TextDelta(content=evt.get("content", ""))
        if evt.get("type") == "result":
            return Done()
        return None
