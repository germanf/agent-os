"""HTTP chat backend — OpenAI-compatible API, no local CLI required."""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator

import httpx

from .protocol import ChatBackend, Done, NormalizedEvent, TextDelta


class HttpChatBackend(ChatBackend):
    name = "http"

    @property
    def executable(self) -> str:
        return ""

    def validate_available(self) -> bool:
        return bool(os.environ.get("OPENAI_API_KEY"))

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
        raise NotImplementedError("HttpChatBackend uses stream_chat, not subprocess")

    def parse_line(self, raw_line: str) -> NormalizedEvent | None:
        return None

    async def stream_chat(
        self,
        message: str,
        session_id: str,
        first: bool,
        project: dict | None = None,
        file_paths: list[str] | None = None,
        context_dirs: list[str] | None = None,
        mcp_manifest: str | None = None,
    ) -> AsyncIterator[NormalizedEvent]:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

        system_prompt = (project or {}).get("system_prompt") if project else ""
        if mcp_manifest:
            system_prompt = f"{system_prompt}\n\n{mcp_manifest}" if system_prompt else mcp_manifest

        messages: list[dict] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})

        body = {
            "model": model,
            "messages": messages,
            "stream": True,
            "max_tokens": int(os.environ.get("OPENAI_MAX_TOKENS", "4096")),
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=300) as client:
            async with client.stream("POST", f"{base_url}/chat/completions", json=body, headers=headers) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_lines():
                    chunk = chunk.strip()
                    if not chunk:
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
