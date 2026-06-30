"""Kimi Code backend stub — https://kimi.ai"""

from __future__ import annotations

from .protocol import ChatBackend, NormalizedEvent


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
    ) -> list[str]:
        raise NotImplementedError("Kimi backend is not yet implemented")

    def parse_line(self, raw_line: str) -> NormalizedEvent | None:
        return None  # RawLine fallback — text-only display
