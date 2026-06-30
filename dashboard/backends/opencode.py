"""Opencode backend — https://opencode.ai"""

from __future__ import annotations

import json
import logging

from .protocol import ChatBackend, Done, NormalizedEvent, TextDelta, ToolUse

logger = logging.getLogger(__name__)


class OpencodeBackend(ChatBackend):
    name = "opencode"

    @property
    def executable(self) -> str:
        return "opencode"

    def build_command(
        self,
        message: str,
        session_id: str,
        first: bool,
        project: dict | None = None,
        file_paths: list[str] | None = None,
        context_dirs: list[str] | None = None,
    ) -> list[str]:
        cmd = ["opencode", "run", message, "--format", "json"]

        if file_paths:
            for fp in file_paths:
                cmd += ["--file", fp]

        cmd += ["-s", session_id] if first else ["-c", session_id]

        if project is not None and project.get("system_prompt"):
            cmd += ["--instructions", project["system_prompt"]]

        for d in (context_dirs or []):
            cmd += ["--add-dir", d]

        return cmd

    def parse_line(self, raw_line: str) -> NormalizedEvent | None:
        if not raw_line or raw_line.isspace():
            return None
        try:
            evt = json.loads(raw_line)
        except (json.JSONDecodeError, TypeError):
            return None

        if evt.get("type") == "text":
            return TextDelta(content=evt.get("content", ""))

        if evt.get("type") == "tool_use":
            return ToolUse(
                id=evt.get("id", ""),
                name=evt.get("name", ""),
                input=evt.get("input", {}),
            )

        if evt.get("type") == "result":
            return Done()

        return None
