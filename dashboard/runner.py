"""Async subprocess runner with line-by-line log streaming via SSE."""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import StrEnum

from loguru import logger


class Status(StrEnum):
    QUEUED   = "queued"
    RUNNING  = "running"
    DONE     = "done"
    FAILED   = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    id: str
    tool: str           # tool identifier (free string)
    command: list[str]
    cwd: str
    env: dict[str, str] | None = None   # extra env vars (e.g. proxy routing)
    status: Status = Status.QUEUED
    exit_code: int | None = None
    started_at: float = field(default_factory=time.time)
    ended_at: float | None = None
    _log_lines: list[str] = field(default_factory=list)
    _subscribers: list[asyncio.Queue] = field(default_factory=list)
    _proc: asyncio.subprocess.Process | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tool": self.tool,
            "status": self.status,
            "exit_code": self.exit_code,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "line_count": len(self._log_lines),
        }


_jobs: dict[str, Job] = {}

# Eviction for finished jobs, so _jobs doesn't grow without bound (every
# /chat message creates a Job too). Finished jobs older than the TTL get
# dropped; as a backstop against bursts within the TTL window, we also cap
# how many finished jobs we keep around regardless of age.
_JOB_RETENTION_SECONDS = 60 * 60  # 1 hour
_MAX_FINISHED_JOBS = 200

_FINISHED_STATUSES = (Status.DONE, Status.FAILED, Status.CANCELLED)


def _prune_jobs() -> None:
    finished = [
        j for j in _jobs.values()
        if j.status in _FINISHED_STATUSES and not j._subscribers
    ]
    if not finished:
        return

    now = time.time()
    finished.sort(key=lambda j: j.ended_at or 0)

    # Drop everything past the TTL.
    expired = [j for j in finished if j.ended_at and now - j.ended_at > _JOB_RETENTION_SECONDS]

    # Drop the oldest finished jobs beyond the count cap (oldest-first, so
    # this only ever removes jobs not already caught by the TTL check).
    overflow_count = len(finished) - _MAX_FINISHED_JOBS
    overflow = finished[:overflow_count] if overflow_count > 0 else []

    for job in {j.id: j for j in (*expired, *overflow)}.values():
        _jobs.pop(job.id, None)


def create_job(tool: str, command: list[str], cwd: str, env: dict[str, str] | None = None) -> Job:
    _prune_jobs()
    job = Job(id=uuid.uuid4().hex[:10], tool=tool, command=command, cwd=cwd, env=env)
    _jobs[job.id] = job
    return job


def list_jobs() -> list[dict]:
    return [j.to_dict() for j in sorted(_jobs.values(), key=lambda j: -j.started_at)]


def get_job(job_id: str) -> Job | None:
    return _jobs.get(job_id)


def get_logs(job_id: str) -> list[str]:
    j = _jobs.get(job_id)
    return j._log_lines if j else []


async def run_job(job: Job) -> None:
    job.status = Status.RUNNING
    job.started_at = time.time()

    try:
        proc_env = {**__import__("os").environ}
        if job.env:
            proc_env.update(job.env)
        proc = await asyncio.create_subprocess_exec(
            *job.command,
            cwd=job.cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=proc_env,
        )
        job._proc = proc

        async for raw in proc.stdout:
            line = raw.decode("utf-8", errors="replace").rstrip()
            job._log_lines.append(line)
            for q in job._subscribers:
                await q.put(line)

        await proc.wait()
        job.exit_code = proc.returncode
        job.status = Status.DONE if proc.returncode == 0 else Status.FAILED

    except asyncio.CancelledError:
        logger.info("Job {} cancelled", job.id)
        job.status = Status.CANCELLED
        if job._proc:
            job._proc.terminate()
    except Exception as exc:
        logger.error("Job {} failed: {}", job.id, exc)
        job._log_lines.append(f"[runner error] {exc}")
        job.status = Status.FAILED
    finally:
        job.ended_at = time.time()
        for q in job._subscribers:
            await q.put(None)  # sentinel


async def stream_logs(job: Job) -> AsyncIterator[str]:
    """Yield SSE-formatted strings: already-seen lines first, then live.

    Each caller gets its own subscriber queue so concurrent/reconnecting
    clients don't steal lines from each other or replay the same line twice
    (once from the _log_lines snapshot, once from a shared live queue).
    """
    snapshot = list(job._log_lines)
    queue: asyncio.Queue = asyncio.Queue()
    still_running = job.status in (Status.QUEUED, Status.RUNNING)
    if still_running:
        job._subscribers.append(queue)

    for line in snapshot:
        yield f"data: {json.dumps(line)}\n\n"

    if not still_running:
        yield "event: done\ndata: {}\n\n"
        return

    try:
        while True:
            try:
                line = await asyncio.wait_for(queue.get(), timeout=25)
            except TimeoutError:
                yield "event: ping\ndata: {}\n\n"
                continue
            if line is None:
                break
            yield f"data: {json.dumps(line)}\n\n"
    finally:
        if queue in job._subscribers:
            job._subscribers.remove(queue)

    yield "event: done\ndata: {}\n\n"


async def cancel_job(job_id: str) -> bool:
    job = _jobs.get(job_id)
    if not job:
        return False
    if job._proc and job.status == Status.RUNNING:
        job._proc.terminate()
        job.status = Status.CANCELLED
        job.ended_at = time.time()
        return True


def checkpoint_job(job_id: str) -> dict | None:
    job = _jobs.get(job_id)
    if not job:
        return None
    return {
        "id": job.id,
        "tool": job.tool,
        "command": job.command,
        "cwd": job.cwd,
        "env": job.env,
        "status": job.status,
        "exit_code": job.exit_code,
        "started_at": job.started_at,
        "ended_at": job.ended_at,
        "logs": list(job._log_lines),
    }
    return False
