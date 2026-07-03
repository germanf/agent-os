"""Kimi Code backend — https://kimi.ai"""

from __future__ import annotations

import json

from .protocol import ChatBackend, Done, NormalizedEvent, TextDelta


class KimiBackend(ChatBackend):
    name = "kimi"

    @property
    def executable(self) -> str:
        return "kimi"

    def _proxy_env(self, proxy_url: str) -> dict[str, str]:
        return {}

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
        cmd = ["kimi", "--input", message, "--format", "json"]

        cmd += ["--session", session_id] if first else ["--resume", session_id]

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
