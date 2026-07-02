import re
from collections.abc import AsyncIterator
from datetime import datetime

from loguru import logger

from .hermes_adapter import is_available, run_command


async def list_jobs(include_all: bool = False) -> str:
    if not is_available():
        return ""
    args = ["cron", "list"]
    if include_all:
        args.append("--all")
    code, out, err = await run_command(args)
    return out if code == 0 else ""


async def create_job(
    schedule: str,
    prompt: str | None = None,
    name: str | None = None,
    script: str | None = None,
    deliver: str | None = None,
    workdir: str | None = None,
    no_agent: bool = False,
) -> tuple[int, str, str]:
    args = ["cron", "create"]
    if name:
        args += ["--name", name]
    if deliver:
        args += ["--deliver", deliver]
    if script:
        args += ["--script", script]
    if no_agent:
        args.append("--no-agent")
    if workdir:
        args += ["--workdir", workdir]
    args.append(schedule)
    if prompt:
        args.append(prompt)
    return await run_command(args)


async def pause_job(name: str) -> tuple[int, str, str]:
    return await run_command(["cron", "pause", name])


async def resume_job(name: str) -> tuple[int, str, str]:
    return await run_command(["cron", "resume", name])


async def remove_job(name: str) -> tuple[int, str, str]:
    return await run_command(["cron", "remove", name])


async def run_now(name: str) -> tuple[int, str, str]:
    return await run_command(["cron", "run", name])


async def tick(accept_hooks: bool = True) -> tuple[int, str, str]:
    args = ["cron", "tick"]
    if accept_hooks:
        args.append("--accept-hooks")
    return await run_command(args)


async def status() -> tuple[int, str, str]:
    return await run_command(["cron", "status"])


_REPEAT_RE = re.compile(r"^\s*(\d+)\s*([smhdw])\s*$", re.IGNORECASE)


def parse_schedule_to_seconds(schedule: str) -> int | None:
    """Translate a nominal schedule string like '30s'/'5m'/'1h' into seconds.

    For full cron expression (5 fields) or 'every Nh/m/s', returns None to
    indicate the platform can't compute ticks locally — Hermes daemon owns it.
    """
    if not schedule:
        return None
    s = schedule.strip()
    if s.startswith("every "):
        rest = s[len("every "):].strip()
        m = _REPEAT_RE.match(rest)
        if m:
            n, unit = int(m.group(1)), m.group(2).lower()
            mult = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 86400 * 7}[unit]
            return n * mult
        return None
    parts = s.split()
    if len(parts) == 1:
        m = _REPEAT_RE.match(s)
        if m:
            n, unit = int(m.group(1)), m.group(2).lower()
            mult = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 86400 * 7}[unit]
            return n * mult
    return None


def iso_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


async def stream_warnings() -> AsyncIterator[str]:
    """Yield non-blocking warning if hermes is unavailable."""
    if not is_available():
        msg = f"[{iso_now()}] Hermes CLI not available — cron jobs cannot run"
        logger.warning(msg)
        yield msg
