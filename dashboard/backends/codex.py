"""GPT Codex backend stub — https://github.com/openai/codex"""

from __future__ import annotations

from .protocol import ChatBackend, NormalizedEvent


class CodexBackend(ChatBackend):
    name = "codex"

    @property
    def executable(self) -> str:
        return "codex"

    def build_command(
        self,
        message: str,
        session_id: str,
        first: bool,
        project: dict | None = None,
        file_paths: list[str] | None = None,
        context_dirs: list[str] | None = None,
    ) -> list[str]:
        raise NotImplementedError("Codex backend is not yet implemented")

    def parse_line(self, raw_line: str) -> NormalizedEvent | None:
        return None  # RawLine fallback — text-only display
