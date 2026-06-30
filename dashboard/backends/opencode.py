"""Opencode backend — https://opencode.ai

Supports two execution modes:
1. HTTP / SDK mode (primary): communicates with `opencode serve` via REST API
2. Subprocess mode (fallback): calls `opencode run` CLI directly
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx
from loguru import logger

from dashboard.agents.opencode_agent import OPCODE_API_URL, is_server_available

from .protocol import ChatBackend, Done, NormalizedEvent, TextDelta, ToolUse


class OpencodeBackend(ChatBackend):
    name = "opencode"

    @property
    def executable(self) -> str:
        return "opencode"

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

        event_type = evt.get("type")

        if event_type == "text":
            return TextDelta(content=evt.get("content", ""))

        if event_type == "tool_use":
            return ToolUse(
                id=evt.get("id", ""),
                name=evt.get("name", ""),
                input=evt.get("input", {}),
            )

        if event_type == "result":
            return Done()

        return None

    async def stream_chat(
        self,
        message: str,
        session_id: str,
        first: bool,
        project: dict | None = None,
        file_paths: list[str] | None = None,
        context_dirs: list[str] | None = None,
    ) -> AsyncIterator[NormalizedEvent]:
        if not is_server_available():
            logger.warning("opencode server not available, subprocess fallback required")
            return

        system_prompt = (project or {}).get("system_prompt") if project else None
        session = session_id if first else session_id

        messages = [
            {"role": "system", "content": system_prompt or "You are a software engineer."},
            {"role": "user", "content": message},
        ]
        if file_paths:
            files_section = "\n".join(f"- {fp}" for fp in file_paths)
            messages.append({"role": "user", "content": f"[Attached files]:\n{files_section}"})

        body: dict = {
            "model": "opencode",
            "messages": messages,
            "stream": True,
            "session_id": session,
        }

        logger.debug("OpencodeBackend.stream_chat session={}", session)
        async with httpx.AsyncClient(base_url=OPCODE_API_URL, timeout=300) as client:
            async with client.stream("POST", "/chat/completions", json=body) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_lines():
                    chunk = chunk.strip()
                    if not chunk or chunk.startswith(":"):
                        continue
                    if chunk.startswith("data: "):
                        data = chunk[6:]
                        if data.strip() == "[DONE]":
                            yield Done()
                            return
                        try:
                            evt = json.loads(data)
                            delta = evt.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield TextDelta(content=content)
                        except (json.JSONDecodeError, IndexError, KeyError):
                            continue
                    else:
                        evt = self.parse_line(chunk)
                        if evt is not None:
                            yield evt
