"""Chat backend registry — discover, register, and select backends."""

from __future__ import annotations

import os

from loguru import logger

from .claude import ClaudeBackend
from .codex import CodexBackend
from .kimi import KimiBackend
from .opencode import OpencodeBackend
from .protocol import ChatBackend

_registry: dict[str, ChatBackend] = {}


def register(backend: ChatBackend) -> None:
    _registry[backend.name] = backend


def get(name: str) -> ChatBackend | None:
    return _registry.get(name)


def discover() -> dict[str, ChatBackend]:
    """Return all registered backends whose executable is available."""
    return {n: b for n, b in _registry.items() if b.validate_available()}


def select_backend() -> ChatBackend:
    """Select a backend based on CHAT_BACKEND env var or first available.

    Returns the selected backend, or raises RuntimeError if none available.
    """
    available = discover()
    if not available:
        raise RuntimeError("No chat backends available on this system")

    preferred = os.environ.get("CHAT_BACKEND", "")
    if preferred:
        backend = available.get(preferred)
        if backend:
            return backend
        logger.warning("CHAT_BACKEND=%s not available, falling back to first available", preferred)

    name, backend = next(iter(available.items()))
    logger.info("Selected chat backend: %s", name)
    return backend


def list_available() -> list[str]:
    return sorted(discover().keys())


def list_all_registered() -> list[str]:
    return sorted(_registry.keys())


# ── Auto-register known backends ───────────────────────────────────────────────

register(ClaudeBackend())
register(OpencodeBackend())
register(CodexBackend())
register(KimiBackend())
