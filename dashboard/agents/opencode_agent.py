from __future__ import annotations

import asyncio
import os
import shutil
import uuid

import httpx
from loguru import logger

from .protocol import AgentContext, AgentResult, DeveloperCapability

OPCODE_SERVER_PORT = int(os.environ.get("OPCODE_SERVER_PORT", "8899"))
OPCODE_SERVER_HOST = os.environ.get("OPCODE_SERVER_HOST", "127.0.0.1")
OPCODE_API_URL = f"http://{OPCODE_SERVER_HOST}:{OPCODE_SERVER_PORT}/v1"

_server_proc: asyncio.subprocess.Process | None = None


def is_server_available() -> bool:
    return shutil.which("opencode") is not None


async def start_server() -> bool:
    global _server_proc
    if not is_server_available():
        logger.info("opencode not found on PATH — SDK agent disabled")
        return False

    if _server_proc is not None and _server_proc.returncode is None:
        logger.debug("opencode server already running")
        return True

    cmd = [
        "opencode", "serve",
        "--port", str(OPCODE_SERVER_PORT),
        "--hostname", OPCODE_SERVER_HOST,
        "--print-logs",
    ]

    logger.info("Starting opencode server on {}:{}", OPCODE_SERVER_HOST, OPCODE_SERVER_PORT)
    try:
        _server_proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError:
        logger.warning("opencode binary not found — SDK agent disabled")
        return False

    await asyncio.sleep(2)

    if _server_proc.returncode is not None:
        _, stderr = await _server_proc.communicate()
        logger.error("opencode server exited immediately: {}", stderr.decode() if stderr else "unknown")
        _server_proc = None
        return False

    logger.info("opencode server started (PID {})", _server_proc.pid)
    return True


async def stop_server() -> None:
    global _server_proc
    if _server_proc is not None and _server_proc.returncode is None:
        logger.info("Stopping opencode server (PID {})", _server_proc.pid)
        _server_proc.terminate()
        try:
            await asyncio.wait_for(_server_proc.wait(), timeout=10)
        except TimeoutError:
            logger.warning("opencode server did not terminate in time, killing")
            _server_proc.kill()
            await _server_proc.wait()
        _server_proc = None


class OpencodeAgent(DeveloperCapability):
    def __init__(self) -> None:
        self._http_client: httpx.AsyncClient | None = None

    @property
    def description(self) -> str:
        return "OpenCode-powered software engineering agent"

    async def _client(self) -> httpx.AsyncClient:
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(base_url=OPCODE_API_URL, timeout=120)
        return self._http_client

    async def _chat_completion(
        self, messages: list[dict], session_id: str | None = None, stream: bool = False
    ) -> dict:
        client = await self._client()
        body: dict = {
            "model": "opencode",
            "messages": messages,
            "stream": stream,
        }
        if session_id:
            body["session_id"] = session_id

        resp = await client.post("/chat/completions", json=body)
        resp.raise_for_status()
        return resp.json()

    async def _spawn_session(self, context: AgentContext) -> str:
        session_id = uuid.uuid4().hex[:12]
        messages = [{"role": "user", "content": f"System: {context.system_prompt or ''}"}]
        await self._chat_completion(messages, session_id=session_id)
        return session_id

    async def _execute(self, user_msg: str, context: AgentContext) -> AgentResult:
        session_id = await self._spawn_session(context)
        messages = [
            {"role": "system", "content": context.system_prompt or "You are a software engineer."},
            {"role": "user", "content": user_msg},
        ]
        try:
            result = await self._chat_completion(messages, session_id=session_id)
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return AgentResult(
                success=True,
                summary=content[:200],
                details={"session_id": session_id, "full_output": content},
            )
        except httpx.HTTPError as exc:
            logger.error("OpencodeAgent call failed: {}", exc)
            return AgentResult(success=False, summary=str(exc))

    async def fix_bug(self, description: str, context: AgentContext) -> AgentResult:
        return await self._execute(f"Fix the following bug:\n\n{description}", context)

    async def implement_feature(self, spec: str, context: AgentContext) -> AgentResult:
        return await self._execute(f"Implement the following feature:\n\n{spec}", context)

    async def refactor(self, target: str, description: str, context: AgentContext) -> AgentResult:
        return await self._execute(f"Refactor {target}:\n\n{description}", context)
