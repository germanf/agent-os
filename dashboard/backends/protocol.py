"""Tool-agnostic chat backend protocol and normalized event types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

# ── Normalized Event Types ────────────────────────────────────────────────────

@dataclass
class TextDelta:
    content: str

@dataclass
class ToolUse:
    id: str
    name: str
    input: dict

@dataclass
class ToolResult:
    id: str
    content: str

@dataclass
class AssistantMessage:
    content: str
    tool_calls: list[dict] = field(default_factory=list)

@dataclass
class Done:
    pass

NormalizedEvent = TextDelta | ToolUse | ToolResult | AssistantMessage | Done


# ── Chat Backend Protocol ─────────────────────────────────────────────────────

class ChatBackend(ABC):
    """Contract that any agentic CLI tool must implement."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier, e.g. 'claude', 'opencode'."""

    @abstractmethod
    def build_command(
        self,
        message: str,
        session_id: str,
        first: bool,
        project: dict | None = None,
        file_paths: list[str] | None = None,
        context_dirs: list[str] | None = None,
    ) -> list[str]:
        """Build argv for the subprocess.

        Args:
            message: The user's message text.
            session_id: Unique session identifier.
            first: True if this is the first message in a session.
            project: Optional project dict with system_prompt and folders.
            file_paths: Optional list of uploaded file paths.
            context_dirs: Optional list of additional directories to include as context.
        """

    @abstractmethod
    def parse_line(self, raw_line: str) -> NormalizedEvent | None:
        """Parse a single raw output line into a normalized event.

        Return None if the line should be skipped (e.g. non-JSON, pings).
        """

    async def stream_chat(
        self,
        message: str,
        session_id: str,
        first: bool,
        project: dict | None = None,
        file_paths: list[str] | None = None,
        context_dirs: list[str] | None = None,
    ) -> AsyncIterator[NormalizedEvent]:
        """Stream chat response via HTTP/sdk (optional override).

        Default raises NotImplementedError — the caller falls back to
        the subprocess-based flow (build_command + parse_line).
        """
        raise NotImplementedError(f"{type(self).__name__} does not support stream_chat")

    def parse_full_transcript(self, log_lines: list[str]) -> tuple[str, list[dict]]:
        """Extract final text and tool calls from all log lines.

        Default implementation iterates parse_line() and collects
        AssistantMessage events. Subclasses may override for efficiency.
        """
        text = ""
        tool_calls: dict[str, dict] = {}
        for line in log_lines:
            evt = self.parse_line(line)
            if isinstance(evt, TextDelta):
                text += evt.content
            elif isinstance(evt, ToolUse):
                tool_calls[evt.id] = {"id": evt.id, "name": evt.name, "input": evt.input}
            elif isinstance(evt, ToolResult):
                tc = tool_calls.get(evt.id)
                if tc is not None:
                    tc["result"] = evt.content
            elif isinstance(evt, AssistantMessage):
                text = evt.content
                for tc in evt.tool_calls:
                    tool_calls[tc["id"]] = tc
        return text, list(tool_calls.values())

    def proxy_env(self) -> dict[str, str]:
        """Environment variables to route API traffic through the Headroom proxy.

        Returns the env vars for this backend's provider, or empty dict
        if the proxy is not available or the provider is unknown.
        """
        from dashboard.headroom_sidecar import is_available, proxy_url

        if not is_available():
            return {}
        url = proxy_url()
        return self._proxy_env(url)

    def _proxy_env(self, proxy_url: str) -> dict[str, str]:
        """Override in subclasses to set the provider-specific env var."""
        return {}

    def validate_available(self) -> bool:
        """Check if the executable is available on this system."""
        import shutil
        return shutil.which(self.executable) is not None

    @property
    def executable(self) -> str:
        """Default: same as name. Override if the binary differs."""
        return self.name
