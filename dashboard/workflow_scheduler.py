"""Autonomous cron-driven workflow scheduler.

Runs every 30 minutes. If a workflow is already running when its next tick
arrives, schedules a retry 5 minutes later (recursive re-entrancy).
"""
from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import Any

from loguru import logger

from dashboard.chat_store import _connect
from dashboard.ops_workflows import _WORKFLOW_REGISTRY

_scheduler_task: asyncio.Task | None = None
_pending_retries: dict[str, asyncio.Task] = {}


async def _init_table() -> None:
    async with _connect() as conn:
        await conn.executescript("""
            CREATE TABLE IF NOT EXISTS workflow_runs (
                id            TEXT PRIMARY KEY,
                workflow_name TEXT NOT NULL,
                status        TEXT NOT NULL DEFAULT 'pending',
                started_at    REAL,
                completed_at  REAL,
                detail_json   TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_wr_workflow ON workflow_runs(workflow_name);
        """)


async def _record_run_start(name: str) -> str:
    run_id = uuid.uuid4().hex[:16]
    async with _connect() as conn:
        await conn.execute(
            "INSERT INTO workflow_runs (id, workflow_name, status, started_at) VALUES (?, ?, 'running', ?)",
            (run_id, name, time.time()),
        )
    return run_id


async def _record_run_complete(run_id: str, status: str, detail: dict | None = None) -> None:
    async with _connect() as conn:
        await conn.execute(
            "UPDATE workflow_runs SET status = ?, completed_at = ?, detail_json = ? WHERE id = ?",
            (status, time.time(), json.dumps(detail) if detail else None, run_id),
        )


async def _run_and_record(name: str) -> None:
    cfg = _WORKFLOW_REGISTRY.get(name)
    if not cfg:
        return
    cfg["running"] = True
    run_id = await _record_run_start(name)
    try:
        result = await cfg["func"]()
        await _record_run_complete(run_id, "completed", result)
        logger.info("Workflow '{}' completed", name)
    except Exception as e:
        logger.error("Workflow '{}' failed: {}", name, e)
        await _record_run_complete(run_id, "failed", {"error": str(e)})
    finally:
        cfg["running"] = False
        cfg["last_tick"] = time.time()


async def _retry_later(name: str) -> None:
    await asyncio.sleep(300)
    cfg = _WORKFLOW_REGISTRY.get(name)
    if not cfg:
        return
    if cfg["running"]:
        await _retry_later(name)
    else:
        logger.info("Retry starting workflow '{}'", name)
        asyncio.create_task(_run_and_record(name))


async def tick() -> None:
    now = time.time()
    for name, cfg in list(_WORKFLOW_REGISTRY.items()):
        if not cfg["enabled"]:
            continue
        elapsed = now - cfg["last_tick"]
        if elapsed < cfg["interval_min"] * 60:
            continue
        if cfg["running"]:
            logger.info("Workflow '{}' still running, retry in 5 min", name)
            asyncio.create_task(_retry_later(name))
        else:
            logger.info("Starting scheduled workflow '{}'", name)
            asyncio.create_task(_run_and_record(name))


async def tick_one(name: str) -> dict[str, Any]:
    cfg = _WORKFLOW_REGISTRY.get(name)
    if not cfg:
        return {"ok": False, "error": f"Workflow '{name}' not found"}
    if cfg["running"]:
        return {"ok": False, "error": "Already running"}
    cfg["last_tick"] = 0.0
    asyncio.create_task(_run_and_record(name))
    return {"ok": True, "workflow": name}


async def _loop(interval_seconds: int = 1800) -> None:
    await _init_table()
    logger.info("Workflow scheduler started (interval={}s)", interval_seconds)
    while True:
        try:
            await tick()
        except Exception as e:
            logger.error("Scheduler tick error: {}", e)
        await asyncio.sleep(interval_seconds)


def start(interval_seconds: int = 1800) -> asyncio.Task | None:
    global _scheduler_task
    if _scheduler_task and not _scheduler_task.done():
        return _scheduler_task
    _scheduler_task = asyncio.create_task(_loop(interval_seconds))
    return _scheduler_task


def stop() -> None:
    global _scheduler_task
    if _scheduler_task:
        _scheduler_task.cancel()
        _scheduler_task = None
